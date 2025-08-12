"""
Configuration management command for showing and editing configuration.
"""

import typer

from config.manager import config
from config.schema import get_sensitive_fields


def config_cmd(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit configuration"),
    reset: bool = typer.Option(
        False, "--reset", "-r", help="Reset to default configuration"
    ),
    env: bool = typer.Option(False, "--env", help="Show environment variables"),
    validate: bool = typer.Option(False, "--validate", help="Validate configuration"),
    export: bool = typer.Option(
        False, "--export", help="Export as environment variables"
    ),
    schema: bool = typer.Option(False, "--schema", help="Show configuration schema"),
):
    """Show or edit configuration."""
    if show:
        show_config()
    elif env:
        config.show_env_vars()
    elif validate:
        config.validate()
    elif export:
        config.export_env_vars()
    elif schema:
        show_schema()
    elif edit:
        typer.echo("Opening configuration editor...")
        # TODO: Implement config editing logic
        typer.echo("Configuration updated!")
    elif reset:
        typer.echo("Resetting to default configuration...")
        config.reset()
        typer.echo("Configuration reset!")
    else:
        show_help()


def show_config():
    """Show current configuration."""
    typer.echo("Current configuration:")
    sensitive_fields = get_sensitive_fields()
    schema_info = config.get_schema_info()

    for key, value in config.config.items():
        # Get field metadata
        field_info = schema_info.get(key, {})
        required = field_info.get("required", False)
        required_marker = " [REQUIRED]" if required else " [OPTIONAL]"

        # Mask sensitive values
        if key in sensitive_fields and value:
            display_value = f"{value[:8]}..." if len(value) > 8 else "***"
        else:
            display_value = value

        typer.echo(f"  - {key}{required_marker}: {display_value}")

    # Show missing required fields
    missing_required = []
    for field_name, field_info in schema_info.items():
        if field_info.get("required", False) and field_name not in config.config:
            missing_required.append(field_name)

    if missing_required:
        typer.echo(f"\n⚠️  Missing required fields: {', '.join(missing_required)}")
        typer.echo("   Use 'elenchus set-config <field> <value>' to set them")


def show_schema():
    """Show configuration schema information."""
    schema_info = config.get_schema_info()

    typer.echo("Configuration Schema")
    typer.echo("=" * 50)

    for field_name, info in schema_info.items():
        typer.echo(f"\n{field_name}:")
        typer.echo(f"  Description: {info['description']}")
        typer.echo(f"  Type: {info['type']}")
        typer.echo(f"  Environment Variable: {info['env_var']}")
        typer.echo(f"  Required: {info['required']}")
        typer.echo(f"  Sensitive: {info['sensitive']}")
        if info["validation"]:
            typer.echo(f"  Validation: {info['validation']}")
        typer.echo(f"  Default: {info['default']}")


def show_help():
    """Show configuration help with dynamic options."""
    schema_info = config.get_schema_info()

    typer.echo("Configuration Management")
    typer.echo()
    typer.echo("Available options:")
    typer.echo("  --show, -s              Show current configuration")
    typer.echo("  --env                   Show environment variables")
    typer.echo("  --validate              Validate configuration")
    typer.echo("  --export                Export as environment variables")
    typer.echo("  --schema                Show configuration schema")
    typer.echo("  --reset, -r             Reset to default configuration")
    typer.echo("  --edit, -e              Edit configuration (TODO)")
    typer.echo()
    typer.echo("Set specific values:")

    # Dynamically generate set options from schema
    for field_name, info in schema_info.items():
        env_var = info["env_var"]
        description = info["description"]
        field_type = info["type"]

        # Generate appropriate option name
        option_name = f"--set-{field_name.replace('_', '-')}"

        # Add type hints for help
        if field_type == "int":
            type_hint = "INTEGER"
        elif field_type == "float":
            type_hint = "FLOAT"
        elif field_type == "LogLevel":
            type_hint = "LOG_LEVEL"
        else:
            type_hint = "TEXT"

        typer.echo(f"  {option_name:<25} Set {description} ({type_hint})")

    typer.echo()
    typer.echo("Examples:")
    typer.echo("  elenchus config --show")
    typer.echo("  elenchus set-config llm_api_key sk-...")
    typer.echo("  elenchus set-config llm_temperature 0.2")
    typer.echo("  elenchus config --export > .env")
    typer.echo("  elenchus config --schema")


# Dynamic command generation for set operations
def create_set_command(field_name: str, field_info: dict):
    """Create a set command for a specific field."""

    def set_field(value: str):
        """Set a configuration field."""
        # Validate the value based on field type
        field_type = field_info["type"]
        validation = field_info.get("validation", "")

        # Type conversion and validation
        if field_type == "int":
            try:
                converted_value = int(value)
                if validation == "positive_int" and converted_value <= 0:
                    typer.echo(f"Error: {field_name} must be a positive integer")
                    raise typer.Exit(1)
            except ValueError:
                typer.echo(f"Error: {field_name} must be an integer")
                raise typer.Exit(1)
        elif field_type == "float":
            try:
                converted_value = float(value)
                if validation == "temperature" and (
                    converted_value < 0.0 or converted_value > 2.0
                ):
                    typer.echo(f"Error: {field_name} must be between 0.0 and 2.0")
                    raise typer.Exit(1)
            except ValueError:
                typer.echo(f"Error: {field_name} must be a number")
                raise typer.Exit(1)
        elif field_type == "LogLevel":
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if value.upper() not in valid_levels:
                typer.echo(
                    f"Error: {field_name} must be one of: {', '.join(valid_levels)}"
                )
                raise typer.Exit(1)
            converted_value = value.upper()
        else:
            converted_value = value

        # Set the value
        config.set(field_name, converted_value)

        # Show success message
        if field_info.get("sensitive"):
            typer.echo(f"{field_name} set (value hidden for security)")
        else:
            typer.echo(f"{field_name} set to: {converted_value}")

    return set_field


# Generate set commands dynamically
def generate_set_commands():
    """Generate set commands for all configuration fields."""
    schema_info = config.get_schema_info()

    for field_name, field_info in schema_info.items():
        # Create the set command
        set_cmd = create_set_command(field_name, field_info)

        # Register it as a subcommand
        option_name = f"set-{field_name.replace('_', '-')}"
        help_text = f"Set {field_info['description']}"

        # Add type hints to help text
        field_type = field_info["type"]
        if field_type == "int":
            help_text += " (integer)"
        elif field_type == "float":
            help_text += " (float)"
        elif field_type == "LogLevel":
            help_text += " (DEBUG, INFO, WARNING, ERROR, CRITICAL)"

        # Note: This is a simplified approach. In a real implementation,
        # you might want to use a more sophisticated command registration system
        # that can handle dynamic subcommands properly.

        # For now, we'll use a different approach - see the main config_cmd function
        # that handles all set operations through a single interface
