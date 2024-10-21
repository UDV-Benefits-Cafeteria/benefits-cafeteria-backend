from typing import Optional


def benefit_range_filter_parser(value: Optional[str], field: str) -> Optional[dict]:
    if value:
        parts = value.split(",")
        range_filter = {}
        for part in parts:
            try:
                key, val = part.split(":")
                if key not in ["gte", "lte", "gt", "lt"]:
                    raise ValueError(f"Invalid range operator: {key}")
                if field in ["coins_cost", "real_currency_cost", "min_level_cost"]:
                    val = float(val)
                range_filter[key] = val
            except ValueError:
                raise ValueError(f"Invalid format for range filter: {value}")
        return range_filter
    return None
