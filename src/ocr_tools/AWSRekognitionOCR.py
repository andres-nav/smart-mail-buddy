import boto3

from io import BytesIO
import base64

from .AbstractOCR import AbstractOCR


class AWSRekognitionOCR(AbstractOCR):
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        threshold: float = 0.5,
    ) -> None:
        self.image = None
        self.threshold = threshold
        self.client = boto3.client(
            "rekognition",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def recognize_text(self) -> str:
        image_in_bytes = self.convert_image_to_bytes()

        response = self.client.detect_text(Image={"Bytes": image_in_bytes})
        text_detections = response["TextDetections"]

        output_text = ""
        for detection in text_detections:
            if detection["Type"] == "LINE" and detection["Confidence"] > self.threshold:
                output_text += f"\n{detection['DetectedText']}"

        return output_text

    def convert_image_to_bytes(self) -> bytes:
        if not self.image:
            raise ValueError("Image not loaded. Call load_image() first.")

        buffered = BytesIO()
        self.image.save(buffered, format="PNG")
        return buffered.getvalue()
