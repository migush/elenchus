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
        # Defer loading until actually needed
        self._config = None
        self._env_config = None
        self._loaded = False

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".elenchus"
        return str(config_dir / "config.yaml")

    def _ensure_config_dir_exists(self):
        """Ensure the configuration directory exists."""
        config_dir = Path(self.config_file).parent
        config_dir.mkdir(exist_ok=True)

    def _ensure_loaded(self):
        """Ensure configuration is loaded."""
        if not self._loaded:
            self._load_env_vars()
            self._config = self._load_config()
            self._loaded = True

    def _load_env_vars(self) -> None:
        """Load environment variables from .env file and os.environ."""
        # Load .env file if it exists
        load_dotenv()

        # Store environment variables for later use
        self._env_config = {}
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
                    self._env_config[config_key] = converted_value

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
        config.update(self._env_config)

        return config

    def _create_default_config(self) -> Dict:
        """Create a comprehensive default configuration."""
        # Use schema.get_default_config() as the single source of truth
        return get_default_config()

    def _save_config(self, config: Dict) -> None:
        """
        Write the provided configuration dictionary to the instance's config file as YAML.

        Creates the parent directory for self.config_file if it doesn't exist and writes `config` using YAML block style. Errors are caught and reported via a warning message; the function does not raise on I/O or serialization failures.
        """
        try:
            self._ensure_config_dir_exists()
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            typer.echo(f"Warning: Could not save config file: {e}")

    def _validate_config(self, config: Dict) -> tuple[bool, list[str]]:
        """Validate configuration using schema rules."""
        return validate_config(config)

    def get(self, key: str, default=None):
        """Get a configuration value."""
        self._ensure_loaded()
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and save to file."""
        self._ensure_loaded()
        self.config[key] = value
        self._save_config(self.config)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._ensure_loaded()
        self.config = get_default_config()
        # Keep environment variables
        self.config.update(self._env_config)
        self._save_config(self.config)

    def show(self) -> None:
        """Display current configuration."""
        self._ensure_loaded()
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
        self._ensure_loaded()
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
        self._ensure_loaded()
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
        self._ensure_loaded()
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
        """
        Return the effective configuration dictionary using the precedence:
        CLI args > environment variables > config file > defaults.

        Parameters:
            cli_args (Dict, optional): Mapping of configuration keys to values provided by the caller (typically parsed CLI options).
                Keys with value `None` are ignored (do not override lower-precedence sources).

        Returns:
            Dict: A new dictionary containing the merged configuration with the described priority order.
        """
        self._ensure_loaded()
        # Start with default config to ensure all required fields are present
        final_config = get_default_config().copy()

        # Overlay config file values
        final_config.update(self.config)

        # Overlay environment variable values
        if hasattr(self, "env_config") and self.env_config:
            final_config.update(self.env_config)

        # Overlay CLI arguments if provided
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

    @property
    def config(self):
        """Get configuration, loading it if necessary."""
        self._ensure_loaded()
        return self._config

    @property
    def env_config(self):
        """Get environment configuration, loading it if necessary."""
        self._ensure_loaded()
        return self._env_config


# Global configuration instance - lazy loaded
_config_instance = None


def get_config():
    """Get the global configuration instance, creating it if needed."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# For backward compatibility, provide a config variable that lazy-loads
class LazyConfig:
    """Lazy-loading configuration wrapper."""

    def __getattr__(self, name):
        return getattr(get_config(), name)

    def __getitem__(self, key):
        return get_config()[key]

    def get(self, key, default=None):
        return get_config().get(key, default)


config = LazyConfig()
