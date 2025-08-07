"""
Dynamic configuration set command.
"""

import typer
from typing import Optional

from config.manager import config
from config.schema import get_field_metadata


def set_config_cmd(
    field: str = typer.Argument(..., help="Configuration field to set"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration field dynamically."""

    # Get field metadata
    metadata = get_field_metadata(field)
    if not metadata:
        typer.echo(f"Error: Unknown configuration field '{field}'")
        typer.echo("Use 'elenchus config --schema' to see available fields")
        raise typer.Exit(1)

    # Validate and convert the value
    field_type = metadata.get("type", "str")
    validation = metadata.get("validation", "")

    try:
        converted_value = convert_and_validate_value(
            field, value, field_type, validation
        )
    except ValueError as e:
        typer.echo(f"Error: {e}")
        raise typer.Exit(1)

    # Set the value
    config.set(field, converted_value)

    # Show success message
    if metadata.get("sensitive"):
        typer.echo(f"{field} set (value hidden for security)")
    else:
        typer.echo(f"{field} set to: {converted_value}")


def convert_and_validate_value(
    field: str, value: str, field_type: str, validation: str
) -> any:
    """Convert and validate a value based on field type and validation rules."""

    # Type conversion
    if field_type == "int":
        try:
            converted_value = int(value)
        except ValueError:
            raise ValueError(f"{field} must be an integer")
    elif field_type == "float":
        try:
            converted_value = float(value)
        except ValueError:
            raise ValueError(f"{field} must be a number")
    elif field_type == "LogLevel":
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value.upper() not in valid_levels:
            raise ValueError(f"{field} must be one of: {', '.join(valid_levels)}")
        converted_value = value.upper()
    else:
        converted_value = value

    # Validation rules
    if validation == "positive_int":
        if converted_value <= 0:
            raise ValueError(f"{field} must be a positive integer")
    elif validation == "temperature":
        if converted_value < 0.0 or converted_value > 2.0:
            raise ValueError(f"{field} must be between 0.0 and 2.0")
    elif validation == "path":
        try:
            from pathlib import Path

            Path(converted_value).resolve()
        except Exception:
            raise ValueError(f"{field} must be a valid path: {converted_value}")

    return converted_value
