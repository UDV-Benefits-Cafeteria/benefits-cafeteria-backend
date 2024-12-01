from io import BytesIO
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, ValidationError


class ExcelParser:
    def __init__(
        self,
        model_class: type[BaseModel],
        field_mappings: dict[str, list[str]],
        required_fields: Optional[list[str]] = None,
        field_parsers: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize the ExcelParser.

        :param model_class: The Pydantic model class for validation.
        :param field_mappings: Mapping from model field names to list of possible Excel column names.
        :param required_fields: List of required model field names.
        :param field_parsers: Optional dictionary of field-specific parsing functions with optional default values.
        """
        self.model_class = model_class
        self.field_mappings = field_mappings
        self.required_fields = required_fields or []
        self.field_parsers = field_parsers or {}

    def parse_excel(  # noqa: C901
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

        excel_columns = set(df.columns)

        # Build mappings from Excel columns to model fields and vice versa
        excel_to_model_field = {}
        model_field_to_excel_col = {}
        for model_field, possible_excel_cols in self.field_mappings.items():
            for col in possible_excel_cols:
                if col in excel_columns:
                    excel_to_model_field[col] = model_field
                    model_field_to_excel_col[model_field] = col
                    break  # Stop after finding the first matching column

        # Check that required fields have at least one column present in Excel file
        # If a column is not required it will still be parsed if it is present in field_mappings; all other columns are ignored
        missing_required_fields = []
        for field in self.required_fields:
            if field not in model_field_to_excel_col:
                missing_required_fields.append(field)

        if missing_required_fields:
            missing_cols = ", ".join(missing_required_fields)
            raise ValueError(f"Missing required fields: {missing_cols}")

        valid_models = []
        errors = []
        # Fields that caused an error inside a field parser
        # Added not to duplicate errors for one field
        error_fields = []

        for idx, (_, row) in enumerate(df.iterrows(), start=2):
            data = {}
            row_errors = []
            for model_field in self.field_mappings:
                # Get value from excel based on model_field_to_excel_col mapping
                excel_col = model_field_to_excel_col.get(model_field)
                value = row.get(excel_col) if excel_col else None

                # Apply field parsers if any
                if model_field in self.field_parsers:
                    parser_info = self.field_parsers[model_field]

                    # If tuple was given (function + default value)
                    if isinstance(parser_info, tuple):
                        parser, default_value = parser_info
                    else:
                        # Only function was given
                        parser, default_value = parser_info, None

                    try:
                        if default_value is not None:
                            value = parser(value, default_value)
                        else:
                            value = parser(value)

                    except ValueError as e:
                        row_errors.append(
                            {
                                "row": idx,
                                "error": f"Ошибка в поле '{excel_col}': {str(e)}",
                            }
                        )
                        error_fields.append(model_field)
                        value = None

                    except Exception as e:
                        row_errors.append(
                            {
                                "row": idx,
                                "error": f"Неожиданная ошибка в поле '{excel_col}': {str(e)}",
                            }
                        )
                        error_fields.append(model_field)
                        value = None

                # Check for null or 'NaN' values
                if pd.isnull(value) or (isinstance(value, str) and not value.strip()):
                    value = None

                data[model_field] = value

            # Catch pydantic data validation errors
            try:
                model_instance = self.model_class.model_validate(data)
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
            errors.extend(row_errors)
        return valid_models, errors


def initialize_excel_parser(
    required_fields: list[str],
    field_mappings: dict[str, list[str]],
    model_class: type[BaseModel],
    field_parsers: Optional[dict[str, Any]] = None,
) -> ExcelParser:
    return ExcelParser(
        required_fields=required_fields,
        field_mappings=field_mappings,
        model_class=model_class,
        field_parsers=field_parsers,
    )
