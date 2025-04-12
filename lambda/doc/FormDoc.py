from typing import List, Any, Dict

import pymupdf  # type: ignore

from .AbstractDoc import AbstractDoc


class FormDoc(AbstractDoc):
    def __init__(self, form_path: str) -> None:
        super().__init__(form_path)

    def _load(self) -> None:
        self.document = pymupdf.open(self.form_path)

    def save(self, output_path: str) -> None:
        self.document.save(output_path)

    def get_fields_to_fill(self) -> List[str]:
        self._load()

        fields_to_fill = []
        seen_fields = set()  # Track unique field names

        for page in self.document:
            for field in page.widgets():
                if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:  # type: ignore
                    field_name = field.field_name
                    if field_name not in seen_fields:
                        seen_fields.add(field_name)
                        fields_to_fill.append(field_name)

        return fields_to_fill

    def set_fields_to_fill(self, fields_to_fill: Dict[str, Any]) -> None:
        for page in self.document:
            for field in page.widgets():
                if field.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:  # type: ignore
                    field_name = field.field_name
                    if field_name in fields_to_fill:
                        try:
                            field.field_value = fields_to_fill[field_name]
                            field.update()  # Important to update the field appearance
                        except Exception as e:
                            print(f"Error updating field {field_name}: {e}")
