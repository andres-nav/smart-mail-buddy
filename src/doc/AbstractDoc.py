from abc import ABC, abstractmethod
from typing import List


class AbstractDoc(ABC):
    def __init__(self, form_path: str) -> None:
        super().__init__()

        self.form_path = form_path

    @abstractmethod
    def get_fields_to_fill(self) -> List[str]:
        """
        Get the field to fill

        :return: List of field to fill the form
        """
        pass
