"""
Configuration management for Elenchus CLI.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict
import typer


class Config:
    """Configuration management for Elenchus CLI."""

    DEFAULT_CONFIG = {
        "human_eval_url": "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
        "output_dir": "generated_tests",
        "max_iterations": 5,
        "llm_model": "gpt-4",
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".elenchus"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = yaml.safe_load(f) or {}
                    # Merge with defaults to ensure all keys exist
                    return {**self.DEFAULT_CONFIG, **config}
            except Exception as e:
                typer.echo(f"Warning: Could not load config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def _save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            typer.echo(f"Warning: Could not save config file: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and save to file."""
        self.config[key] = value
        self._save_config(self.config)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)

    def show(self) -> None:
        """Display current configuration."""
        typer.echo("Current configuration:")
        for key, value in self.config.items():
            typer.echo(f"  - {key}: {value}")


# Global configuration instance
config = Config()
