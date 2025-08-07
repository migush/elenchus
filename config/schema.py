"""
Configuration schema for Elenchus CLI.
This defines all available configuration options in one place.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List
from enum import Enum


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ConfigSchema:
    """Configuration schema definition."""

    # HumanEval dataset configuration
    human_eval_url: str = field(
        default="https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
        metadata={
            "env_var": "ELENCHUS_HUMAN_EVAL_URL",
            "description": "HumanEval dataset URL",
            "type": "str",
            "required": False,
        },
    )

    output_dir: str = field(
        default="generated_tests",
        metadata={
            "env_var": "ELENCHUS_OUTPUT_DIR",
            "description": "Default output directory",
            "type": "str",
            "required": False,
            "validation": "path",
        },
    )

    max_iterations: int = field(
        default=5,
        metadata={
            "env_var": "ELENCHUS_MAX_ITERATIONS",
            "description": "Maximum iterations for test generation",
            "type": "int",
            "required": False,
            "validation": "positive_int",
        },
    )

    # LLM configuration
    llm_model: str = field(
        default="gpt-4",
        metadata={
            "env_var": "ELENCHUS_LLM_MODEL",
            "description": "LLM model to use",
            "type": "str",
            "required": False,
        },
    )

    llm_api_key: Optional[str] = field(
        default=None,
        metadata={
            "env_var": "ELENCHUS_LLM_API_KEY",
            "description": "LLM API key (required for LLM operations)",
            "type": "str",
            "required": False,
            "sensitive": True,
        },
    )

    llm_temperature: float = field(
        default=0.1,
        metadata={
            "env_var": "ELENCHUS_LLM_TEMPERATURE",
            "description": "LLM temperature (0.0-2.0)",
            "type": "float",
            "required": False,
            "validation": "temperature",
        },
    )

    llm_max_tokens: int = field(
        default=2000,
        metadata={
            "env_var": "ELENCHUS_LLM_MAX_TOKENS",
            "description": "Maximum tokens for LLM responses",
            "type": "int",
            "required": False,
            "validation": "positive_int",
        },
    )

    llm_provider: str = field(
        default="openai",
        metadata={
            "env_var": "ELENCHUS_LLM_PROVIDER",
            "description": "LLM provider (openai, azure, local, etc.)",
            "type": "str",
            "required": False,
        },
    )

    llm_base_url: Optional[str] = field(
        default=None,
        metadata={
            "env_var": "ELENCHUS_LLM_BASE_URL",
            "description": "Custom LLM endpoint URL",
            "type": "str",
            "required": False,
        },
    )

    # NEW FIELD: Timeout configuration
    llm_timeout: int = field(
        default=30,
        metadata={
            "env_var": "ELENCHUS_LLM_TIMEOUT",
            "description": "LLM request timeout in seconds",
            "type": "int",
            "required": False,
            "validation": "positive_int",
        },
    )

    # Logging configuration
    log_level: LogLevel = field(
        default=LogLevel.INFO,
        metadata={
            "env_var": "ELENCHUS_LOG_LEVEL",
            "description": "Logging level",
            "type": "LogLevel",
            "required": False,
            "validation": "log_level",
        },
    )

    log_file: Optional[str] = field(
        default=None,
        metadata={
            "env_var": "ELENCHUS_LOG_FILE",
            "description": "Log file path",
            "type": "str",
            "required": False,
            "validation": "path",
        },
    )


# Schema instance for easy access
SCHEMA = ConfigSchema()


def get_env_mapping() -> Dict[str, str]:
    """Get environment variable mapping from schema."""
    mapping = {}
    for field_name, field_obj in SCHEMA.__dataclass_fields__.items():
        env_var = field_obj.metadata.get("env_var")
        if env_var:
            mapping[env_var] = field_name
    return mapping


def get_default_config() -> Dict[str, Any]:
    """Get default configuration from schema."""
    config = {}
    for field_name, field_obj in SCHEMA.__dataclass_fields__.items():
        config[field_name] = field_obj.default
    return config


def get_sensitive_fields() -> List[str]:
    """Get list of sensitive fields that should be masked."""
    sensitive_fields = []
    for field_name, field_obj in SCHEMA.__dataclass_fields__.items():
        if field_obj.metadata.get("sensitive"):
            sensitive_fields.append(field_name)
    return sensitive_fields


def get_validation_rules() -> Dict[str, Dict[str, Any]]:
    """Get validation rules from schema."""
    rules = {}
    for field_name, field_obj in SCHEMA.__dataclass_fields__.items():
        validation = field_obj.metadata.get("validation")
        if validation:
            rules[field_name] = {
                "type": field_obj.metadata.get("type"),
                "validation": validation,
                "required": field_obj.metadata.get("required", False),
            }
    return rules


def get_field_metadata(field_name: str) -> Dict[str, Any]:
    """Get metadata for a specific field."""
    if field_name in SCHEMA.__dataclass_fields__:
        return SCHEMA.__dataclass_fields__[field_name].metadata
    return {}


def get_all_fields() -> List[str]:
    """Get list of all configuration fields."""
    return list(SCHEMA.__dataclass_fields__.keys())
