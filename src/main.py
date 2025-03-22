import json
import os

import pymupdf
from dotenv import load_dotenv
from groq import Groq

from ocr import AWSRekognitionOCR

from llm import BedrockLLM

DIR = os.path.dirname(os.path.realpath(__file__))
FORM_PATH = os.path.join(DIR, "../docs/alta_autonomos.pdf")
PIC_PATH = os.path.join(DIR, "../docs/dni.jpg")

load_dotenv()

api_key = os.getenv("API_KEY")
client = Groq(api_key=api_key)

document = pymupdf.open(FORM_PATH)

fields_to_fill = []
seen_fields = set()  # Track unique field names

for page in document:
    for field in page.widgets():
        if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:  # type: ignore
            field_name = field.field_name
            if field_name not in seen_fields:
                seen_fields.add(field_name)
                fields_to_fill.append(field_name)

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

if not aws_access_key_id or not aws_secret_access_key or not aws_region:
    raise ValueError(
        "please provide an AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION"
    )

awsRekognitionOCR = AWSRekognitionOCR(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region,
)
extracted_text = awsRekognitionOCR.process_image(PIC_PATH)

prompt = f"""
    Dado el texto obtenido abajo, quiero que rellenes los siguientes campos {fields_to_fill}.

    Formato: el resultado tiene que ser un JSON como en el ejemplo con los campos rellenados, nada más. No me des nada más que no sea el JSON con los campos rellenados.


    Ejemplo:
    {{
        "nombre": ""
    }}

    Texto:
    {extracted_text}

"""


llm = BedrockLLM(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region,
)

json_response = llm.send_prompt(prompt)

for page in document:
    for field in page.widgets():
        if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:  # type: ignore
            field_name = field.field_name
            if field_name in json_response:
                try:
                    # Update the form field value
                    field.field_value = json_response[field_name]
                    field.update()  # Important to update the field appearance
                except Exception as e:
                    print(f"Error updating field {field_name}: {e}")

# Create output directory if needed
output_dir = os.path.join(DIR, "../docs")
os.makedirs(output_dir, exist_ok=True)

# Save the filled PDF
output_path = os.path.join(output_dir, "filled_form.pdf")
document.save(output_path)
print(f"\nSuccessfully saved filled form to:\n{os.path.abspath(output_path)}")
