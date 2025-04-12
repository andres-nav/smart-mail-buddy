import pytesseract

from .AbstractOCR import AbstractOCR


class TesseractOCR(AbstractOCR):
    # Note: the spanish language is not support by pytesseract
    def __init__(self, language: str = "eng") -> None:
        self.image = None
        self.language = language

    def _recognize_text(self) -> str:
        if not self.image:
            raise ValueError("Image not loaded. Call load_image() first.")

        return pytesseract.image_to_string(self.image, lang=self.language)
