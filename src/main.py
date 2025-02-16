import os
from io import BytesIO
import base64

from dotenv import load_dotenv
from PIL import Image

import pymupdf
from groq import Groq

DIR = os.path.dirname(os.path.realpath(__file__))
FORM_PATH = os.path.join(DIR, "../docs/alta_autonomos.pdf")
PIC_PATH = os.path.join(DIR, "../docs/dni.jpg")

load_dotenv()

api_key = os.getenv('API_KEY')
client = Groq(api_key=api_key)

document = pymupdf.open(FORM_PATH)

def encode_image(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

fields_to_fill = []

for page in document:
    for field in page.widgets():
        if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
            fields_to_fill.append(field.field_name)

base64_image = encode_image(PIC_PATH)

prompt = f"""
    given the image attached i want to fill the following fields {fields_to_fill}. Fill all the field that you can
"""

chat_completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        }
                    }
                ]
            }
        ],
        stream=False,
    )

print(chat_completion.choices[0].message.content)


# document.save(os.path.join(DIR, "output.pdf"))

