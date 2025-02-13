import pymupdf
import os

DIR = os.path.dirname(os.path.realpath(__file__))
FORM_PATH = os.path.join(DIR, "../docs/alta_autonomos.pdf")

document = pymupdf.open(FORM_PATH)

for page in document:
    for field in page.widgets():
        print(field.field_name)
        if field.field_name == "nombre":
            field.field_value = "Andres"

            field.update()

document.save(os.path.join(DIR, "output.pdf"))

