"""
Configuration validation using schema-driven rules.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
from .schema import get_validation_rules, LogLevel


def validate_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate configuration using schema rules."""
    rules = get_validation_rules()
    errors = []

    # Check required fields
    for field_name, rule in rules.items():
        if rule.get("required", False):
            if field_name not in config or config[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing")
                continue

        # Skip validation if field is not present (optional fields)
        if field_name not in config or config[field_name] is None:
            continue

        # Validate field value
        field_errors = validate_field(field_name, config[field_name], rule)
        errors.extend(field_errors)

    return len(errors) == 0, errors


def validate_field(field_name: str, value: Any, rule: Dict[str, Any]) -> List[str]:
    """Validate a single field."""
    errors = []

    # Check if required field is present
    if rule.get("required") and value is None:
        errors.append(f"{field_name} is required")
        return errors

    # Skip validation for None values (optional fields)
    if value is None:
        return errors

    # Type validation
    expected_type = rule.get("type")
    if expected_type == "LogLevel":
        if not isinstance(value, str) or value not in [
            level.value for level in LogLevel
        ]:
            errors.append(
                f"{field_name} must be one of: {', '.join([level.value for level in LogLevel])}"
            )
    elif expected_type == "int":
        if not isinstance(value, int):
            errors.append(f"{field_name} must be an integer")
    elif expected_type == "float":
        if not isinstance(value, (int, float)):
            errors.append(f"{field_name} must be a number")
    elif expected_type == "str":
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string")

    # Custom validation rules
    validation_type = rule.get("validation")
    if validation_type == "positive_int":
        if isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{field_name} must be a positive integer")
    elif validation_type == "temperature":
        if isinstance(value, (int, float)) and (value < 0.0 or value > 2.0):
            errors.append(f"{field_name} must be between 0.0 and 2.0")
    elif validation_type == "path":
        if isinstance(value, str):
            try:
                Path(value).resolve()
            except Exception:
                errors.append(f"{field_name} must be a valid path: {value}")
    elif validation_type == "log_level":
        if isinstance(value, str) and value.upper() not in [
            level.value for level in LogLevel
        ]:
            errors.append(
                f"{field_name} must be one of: {', '.join([level.value for level in LogLevel])}"
            )

    return errors


def convert_value(value: str, field_type: str) -> Any:
    """Convert string value to appropriate type."""
    if value is None:
        return None

    try:
        if field_type == "int":
            return int(value)
        elif field_type == "float":
            return float(value)
        elif field_type == "LogLevel":
            return LogLevel(value.upper())
        else:
            return value
    except (ValueError, KeyError):
        return value  # Return original value if conversion fails
