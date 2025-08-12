"""
Configuration management for Elenchus CLI.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
import typer
from dotenv import load_dotenv

from .schema import (
    get_default_config,
    get_env_mapping,
    get_sensitive_fields,
    get_field_metadata,
)
from .validation import validate_config, convert_value


class Config:
    """Configuration management for Elenchus CLI."""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        # Load environment variables first
        self._load_env_vars()
        # Then load config file (will be merged with env vars)
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".elenchus"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def _load_env_vars(self) -> None:
        """Load environment variables from .env file and os.environ."""
        # Load .env file if it exists
        load_dotenv()

        # Store environment variables for later use
        self.env_config = {}
        env_mapping = get_env_mapping()

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Get field metadata for type conversion
                metadata = get_field_metadata(config_key)
                field_type = metadata.get("type", "str")

                # Convert value to appropriate type
                converted_value = convert_value(value, field_type)
                if converted_value is not None:
                    self.env_config[config_key] = converted_value

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        # Start with default config to ensure all required fields are present
        config = self._create_default_config()

        # Override with file config if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    file_config = yaml.safe_load(f) or {}
                    config.update(file_config)
                # Save the merged config back to file to ensure all required fields are present
                self._save_config(config)
            except Exception as e:
                typer.echo(f"Warning: Could not load config file: {e}")
        else:
            # Create comprehensive default config file
            self._save_config(config)

        # Override with environment variables (highest priority)
        config.update(self.env_config)

        return config

    def _create_default_config(self) -> Dict:
        """Create a comprehensive default configuration."""
        return {
            "human_eval_url": "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
            "output_dir": "generated_tests",
            "experiments_dir": "experiments",
            "max_iterations": 5,
            "llm_model": "gpt-4",
            "llm_api_key": None,
            "llm_temperature": 0.1,
            "llm_max_tokens": 2000,
            "llm_provider": "openai",
            "llm_base_url": None,
            "llm_timeout": 30,
            "log_level": "INFO",
            "log_file": None,
            "default_prompt_id": "default",
            "track_experiments": True,
        }

    def _save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            typer.echo(f"Warning: Could not save config file: {e}")

    def _validate_config(self, config: Dict) -> tuple[bool, list[str]]:
        """Validate configuration using schema rules."""
        return validate_config(config)

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and save to file."""
        self.config[key] = value
        self._save_config(self.config)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = get_default_config()
        # Keep environment variables
        self.config.update(self.env_config)
        self._save_config(self.config)

    def show(self) -> None:
        """Display current configuration."""
        typer.echo("Current configuration:")
        sensitive_fields = get_sensitive_fields()

        for key, value in self.config.items():
            # Mask sensitive values
            if key in sensitive_fields and value:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            typer.echo(f"  - {key}: {display_value}")

    def show_env_vars(self) -> None:
        """Display environment variables."""
        typer.echo("Environment variables:")
        env_mapping = get_env_mapping()
        sensitive_fields = get_sensitive_fields()

        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                # Mask sensitive values
                if config_key in sensitive_fields:
                    display_value = f"{value[:8]}..." if len(value) > 8 else "***"
                else:
                    display_value = value
                typer.echo(f"  - {env_var}: {display_value}")
            else:
                typer.echo(f"  - {env_var}: (not set)")

    def validate(self) -> bool:
        """Validate current configuration."""
        is_valid, errors = self._validate_config(self.config)
        if is_valid:
            typer.echo("✅ Configuration is valid!")
            return True
        else:
            typer.echo("❌ Configuration validation failed:")
            for error in errors:
                typer.echo(f"  - {error}")

            # Provide helpful guidance for missing required fields
            missing_required = [error for error in errors if "Required field" in error]
            if missing_required:
                typer.echo("\n💡 To fix missing required fields:")
                typer.echo(
                    "  1. Use 'elenchus set-config <field> <value>' for each missing field"
                )
                typer.echo(
                    "  2. Or set environment variables (see 'elenchus config --env-vars')"
                )
                typer.echo(
                    "  3. Or edit the config file directly: ~/.elenchus/config.yaml"
                )

            return False

    def export_env_vars(self) -> None:
        """Export configuration as environment variables."""
        typer.echo("# Elenchus Configuration Environment Variables")
        typer.echo("# Add these to your .env file or export them:")
        typer.echo()

        env_mapping = get_env_mapping()
        for env_var, config_key in env_mapping.items():
            value = self.config.get(config_key)
            if value is not None:
                typer.echo(f"{env_var}={value}")
            else:
                typer.echo(f"# {env_var}=")

    def get_config_with_priority(self, cli_args: Dict = None) -> Dict:
        """Get configuration with proper priority order: CLI args > env vars > config file > defaults."""
        # Start with current config (which already has env vars > file > defaults)
        final_config = self.config.copy()

        # Override with CLI arguments if provided
        if cli_args:
            for key, value in cli_args.items():
                if value is not None:
                    final_config[key] = value

        return final_config

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information for all fields."""
        from .schema import get_all_fields, get_field_metadata

        schema_info = {}
        for field_name in get_all_fields():
            metadata = get_field_metadata(field_name)
            schema_info[field_name] = {
                "description": metadata.get("description", ""),
                "type": metadata.get("type", "str"),
                "env_var": metadata.get("env_var", ""),
                "required": metadata.get("required", False),
                "sensitive": metadata.get("sensitive", False),
                "validation": metadata.get("validation", ""),
                "default": self.config.get(field_name),
            }
        return schema_info


# Global configuration instance
config = Config()
