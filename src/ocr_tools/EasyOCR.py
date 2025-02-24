import easyocr

from .AbstractOCR import AbstractOCR


class EasyOCR(AbstractOCR):
    # 'es' for Spanish language
    def __init__(self, language: str = "es", threshold: float = 0.5) -> None:
        self.image = None
        self.language = language
        self.reader = easyocr.Reader([self.language])
        self.threshold = threshold

    def recognize_text(self) -> str:
        if not self.image:
            raise ValueError("Image not loaded. Call load_image() first.")

        results = self.reader.readtext(self.image)

        output_text = ""
        for _, text, prob in results:
            if prob > self.threshold:
                output_text += f"\n{text}"

        return output_text
