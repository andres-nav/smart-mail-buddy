from abc import ABC, abstractmethod

from PIL import Image  # type: ignore


class AbstractOCR(ABC):
    def _load_image(self, image_path: str) -> None:
        """
        Load an image from the specified path.

        :param image_path: Path to the image file
        """
        self.image = Image.open(image_path)

    def _preprocess_image(self) -> None:
        # Basic preprocessing, can be extended based on specific needs
        if self.image.mode != "RGB":
            self.image = self.image.convert("RGB")

    @abstractmethod
    def _recognize_text(self) -> str:
        """
        Perform OCR on the preprocessed image and return the recognized text.

        :return: Recognized text as a string
        """
        pass

    def process_image(self, image_path: str) -> str:
        """
        Convenience method to process an image through the entire OCR pipeline.

        :param image_path: Path to the image file
        :return: Recognized text as a string
        """
        self._load_image(image_path)
        self._preprocess_image()
        return self._recognize_text()
