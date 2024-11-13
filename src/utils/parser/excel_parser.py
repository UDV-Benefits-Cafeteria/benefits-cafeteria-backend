from io import BytesIO
from typing import Any, Callable, Optional

import pandas as pd
from pydantic import BaseModel, ValidationError


class ExcelParser:
    def __init__(
        self,
        required_columns: list[str],
        column_mappings: dict[str, str],
        model_class: type[BaseModel],
        field_parsers: Optional[dict[str, Callable[[str], Any]]] = None,
    ):
        """
        Initialize the ExcelParser.

        :param required_columns: List of required column names in the Excel file.
        :param column_mappings: Mapping from Excel column names to model field names.
        :param model_class: Pydantic model class for validation.
        :param field_parsers: Optional dictionary of field-specific parsing functions.
        """
        self.required_columns = required_columns
        self.column_mappings = column_mappings
        self.model_class = model_class
        self.field_parsers = field_parsers or {}

    def parse_excel(
        self, file_contents: bytes
    ) -> tuple[list[BaseModel], list[dict[str, Any]]]:
        """
        Parse the Excel file contents and return valid models and errors.

        :param file_contents: The contents of the Excel file.
        :return: A tuple of (valid_models, errors)
        """
        try:
            df = pd.read_excel(BytesIO(file_contents))
        except Exception as e:
            raise ValueError("Error reading Excel file") from e

        missing_columns = set(self.required_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing columns: {', '.join(missing_columns)}")

        valid_models = []
        errors = []
        error_fields = []

        for idx, (_, row) in enumerate(
            df.iterrows(), start=2
        ):  # Start at 2 to match Excel row numbers
            data = {}
            for excel_col, model_field in self.column_mappings.items():
                value = row.get(excel_col, None)
                if pd.isna(value):
                    value = None

                if model_field in self.field_parsers:
                    try:
                        value = self.field_parsers[model_field](value)
                    except ValueError as e:
                        errors.append(
                            {
                                "row": idx,
                                "error": f"Ошибка в значении поля '{model_field}': {str(e)}",
                            }
                        )
                        error_fields.append(model_field)
                        value = None
                    except Exception as e:
                        errors.append(
                            {
                                "row": idx,
                                "error": f"Непредвиденная ошибка в поле '{model_field}': {str(e)}",
                            }
                        )
                        error_fields.append(model_field)
                        value = None

                data[model_field] = value

            try:
                model_instance = self.model_class(**data)
                valid_models.append(model_instance)
            except ValidationError as ve:
                for err in ve.errors():
                    field = err["loc"][0]
                    if field not in error_fields:
                        error_messages = "; ".join([f"{field}: {err['msg']}"])
                        errors.append(
                            {
                                "row": idx,
                                "error": f"Ошибка валидации данных: {error_messages}",
                            }
                        )

        return valid_models, errors


def initialize_excel_parser(
    required_columns: list[str],
    column_mappings: dict[str, str],
    model_class: type[BaseModel],
    field_parsers: Optional[dict[str, Callable[[str], Any]]] = None,
) -> ExcelParser:
    return ExcelParser(
        required_columns=required_columns,
        column_mappings=column_mappings,
        model_class=model_class,
        field_parsers=field_parsers,
    )
