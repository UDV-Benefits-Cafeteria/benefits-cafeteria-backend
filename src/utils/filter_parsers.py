from typing import Optional


def range_filter_parser(value: Optional[str], field: str) -> Optional[dict]:
    if value:
        parts = value.split(",")
        range_filter = {}
        for part in parts:
            try:
                key, val = part.split(":")
                key = key.strip()
                val = val.strip()
                # These values are then passed directly to ElasticSearch, and so they should be compatible with it
                # gte lte gt lt - compatible values
                if key not in ["gte", "lte", "gt", "lt"]:
                    raise ValueError(f"Invalid range operator: {key}")
                range_filter[key] = val
            except ValueError as ve:
                raise ValueError(
                    f"Invalid format for range filter '{field}': {value}"
                ) from ve
        return range_filter
    return None
