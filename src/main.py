import os

from dotenv import load_dotenv

from llm import BedrockLLM
from ocr import AWSRekognitionOCR
from doc import FormDoc

DIR = os.path.dirname(os.path.realpath(__file__))
# FORM_PATH = os.path.join(DIR, "../docs/alta_autonomos.pdf")
FORM_PATH = os.path.join(DIR, "../docs/consulta_de_fondos.pdf")
PIC_PATH = os.path.join(DIR, "../docs/dni.jpg")

load_dotenv()

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_REGION")

if not aws_access_key_id or not aws_secret_access_key or not aws_region:
    raise ValueError(
        "please provide an AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION"
    )

formDoc = FormDoc(FORM_PATH)

fields_to_fill = formDoc.get_fields_to_fill()

awsRekognitionOCR = AWSRekognitionOCR(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region,
)
extracted_text = awsRekognitionOCR.process_image(PIC_PATH)

prompt = f"""
    Dado el texto obtenido abajo, quiero que rellenes los siguientes campos {fields_to_fill}.

    Tambien te doy mas informacion:
    - telefono 666666666
    - correo electronico: test@example.com
    - seccion: test 1
    - caja/legajo: test 1
    - expediente: test 1

    Hoy es 22 de marzo de 25

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

formDoc.set_fields_to_fill(json_response)

# Create output directory if needed
output_dir = os.path.join(DIR, "../docs")
os.makedirs(output_dir, exist_ok=True)

# Save the filled PDF
output_path = os.path.join(output_dir, "consulta_de_fondos_filled.pdf")
formDoc.save(output_path)
print(f"\nSuccessfully saved filled form to:\n{os.path.abspath(output_path)}")
