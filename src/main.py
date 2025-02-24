import os
from io import BytesIO
import base64

from dotenv import load_dotenv
from PIL import Image

import pymupdf
from groq import Groq

from ocr_tools import AWSRekognitionOCR, EasyOCR, TessseractOCR

DIR = os.path.dirname(os.path.realpath(__file__))
FORM_PATH = os.path.join(DIR, "../docs/alta_autonomos.pdf")
PIC_PATH = os.path.join(DIR, "../docs/dni.jpg")

load_dotenv()

api_key = os.getenv("API_KEY")
client = Groq(api_key=api_key)

document = pymupdf.open(FORM_PATH)

fields_to_fill = []

for page in document:
    for field in page.widgets():
        if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
            fields_to_fill.append(field.field_name)

# tesseractOCR = TesseractOCR()
# extracted_text = tesseractOCR.process_image(PIC_PATH)

# easyOCR = EasyOCR()
# extracted_text = easyOCR.process_image(PIC_PATH)

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

chat_completion = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ],
    stream=False,
)

print(chat_completion.choices[0].message.content)


# document.save(os.path.join(DIR, "output.pdf"))
