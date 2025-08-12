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
        metadata={
            "env_var": "ELENCHUS_HUMAN_EVAL_URL",
            "description": "HumanEval dataset URL",
            "type": "str",
            "required": True,
        },
    )

    output_dir: str = field(
        metadata={
            "env_var": "ELENCHUS_OUTPUT_DIR",
            "description": "Default output directory",
            "type": "str",
            "required": True,
            "validation": "path",
        },
    )

    # Experiments storage (CSV-based)
    experiments_dir: str = field(
        metadata={
            "env_var": "ELENCHUS_EXPERIMENTS_DIR",
            "description": "Root directory for experiments (results/prompts/models/analysis)",
            "type": "str",
            "required": True,
            "validation": "path",
        },
    )

    max_iterations: int = field(
        metadata={
            "env_var": "ELENCHUS_MAX_ITERATIONS",
            "description": "Maximum iterations for test generation",
            "type": "int",
            "required": True,
            "validation": "positive_int",
        },
    )

    # LLM configuration
    llm_model: str = field(
        metadata={
            "env_var": "ELENCHUS_LLM_MODEL",
            "description": "LLM model to use",
            "type": "str",
            "required": True,
        },
    )

    llm_api_key: Optional[str] = field(
        metadata={
            "env_var": "ELENCHUS_LLM_API_KEY",
            "description": "LLM API key (required for LLM operations)",
            "type": "str",
            "required": False,
            "sensitive": True,
        },
    )

    llm_temperature: float = field(
        metadata={
            "env_var": "ELENCHUS_LLM_TEMPERATURE",
            "description": "LLM temperature (0.0-2.0)",
            "type": "float",
            "required": True,
            "validation": "temperature",
        },
    )

    llm_max_tokens: int = field(
        metadata={
            "env_var": "ELENCHUS_LLM_MAX_TOKENS",
            "description": "Maximum tokens for LLM responses",
            "type": "int",
            "required": True,
            "validation": "positive_int",
        },
    )

    llm_provider: str = field(
        metadata={
            "env_var": "ELENCHUS_LLM_PROVIDER",
            "description": "LLM provider (openai, azure, local, etc.)",
            "type": "str",
            "required": True,
        },
    )

    llm_base_url: Optional[str] = field(
        metadata={
            "env_var": "ELENCHUS_LLM_BASE_URL",
            "description": "Custom LLM endpoint URL",
            "type": "str",
            "required": False,
        },
    )

    # NEW FIELD: Timeout configuration
    llm_timeout: int = field(
        metadata={
            "env_var": "ELENCHUS_LLM_TIMEOUT",
            "description": "LLM request timeout in seconds",
            "type": "int",
            "required": True,
            "validation": "positive_int",
        },
    )

    # Logging configuration
    log_level: LogLevel = field(
        metadata={
            "env_var": "ELENCHUS_LOG_LEVEL",
            "description": "Logging level",
            "type": "LogLevel",
            "required": True,
            "validation": "log_level",
        },
    )

    log_file: Optional[str] = field(
        metadata={
            "env_var": "ELENCHUS_LOG_FILE",
            "description": "Log file path",
            "type": "str",
            "required": False,
            "validation": "path",
        },
    )

    # Experiment configuration
    default_prompt_id: str = field(
        metadata={
            "env_var": "ELENCHUS_DEFAULT_PROMPT_ID",
            "description": "Default prompt technique ID",
            "type": "str",
            "required": True,
        },
    )

    track_experiments: bool = field(
        metadata={
            "env_var": "ELENCHUS_TRACK_EXPERIMENTS",
            "description": "Whether to record experiments to CSV",
            "type": "bool",
            "required": True,
        },
    )


# Schema instance for easy access - created when needed
_SCHEMA_INSTANCE = None


def get_schema_instance() -> ConfigSchema:
    """Get the schema instance, creating it if necessary."""
    global _SCHEMA_INSTANCE
    if _SCHEMA_INSTANCE is None:
        # This should only be called after config is loaded
        # For now, return a minimal instance for schema inspection
        _SCHEMA_INSTANCE = ConfigSchema(
            human_eval_url="",
            output_dir="",
            experiments_dir="",
            max_iterations=0,
            llm_model="",
            llm_api_key="",
            llm_temperature=0.0,
            llm_max_tokens=0,
            llm_provider="",
            llm_base_url="",
            llm_timeout=0,
            log_level=LogLevel.INFO,
            log_file="",
            default_prompt_id="",
            track_experiments=False,
        )
    return _SCHEMA_INSTANCE


def get_env_mapping() -> Dict[str, str]:
    """Get environment variable mapping from schema."""
    mapping = {}
    for field_name, field_obj in get_schema_instance().__dataclass_fields__.items():
        env_var = field_obj.metadata.get("env_var")
        if env_var:
            mapping[env_var] = field_name
    return mapping


def get_default_config() -> Dict[str, Any]:
    """Get default configuration from schema."""
    # No more defaults in schema - all values must be provided via config files or environment
    return {}


def get_sensitive_fields() -> List[str]:
    """Get list of sensitive fields that should be masked."""
    sensitive_fields = []
    for field_name, field_obj in get_schema_instance().__dataclass_fields__.items():
        if field_obj.metadata.get("sensitive"):
            sensitive_fields.append(field_name)
    return sensitive_fields


def get_validation_rules() -> Dict[str, Dict[str, Any]]:
    """Get validation rules from schema."""
    rules = {}
    for field_name, field_obj in get_schema_instance().__dataclass_fields__.items():
        validation = field_obj.metadata.get("validation")
        if validation:
            rules[field_name] = {
                "type": field_obj.metadata.get("type"),
                "validation": validation,
                "required": field_obj.metadata.get("required", True),
            }
        else:
            # Include all fields in validation rules, not just those with validation
            rules[field_name] = {
                "type": field_obj.metadata.get("type"),
                "required": field_obj.metadata.get("required", True),
            }
    return rules


def get_field_metadata(field_name: str) -> Dict[str, Any]:
    """Get metadata for a specific field."""
    if field_name in get_schema_instance().__dataclass_fields__:
        return get_schema_instance().__dataclass_fields__[field_name].metadata
    return {}


def get_all_fields() -> List[str]:
    """Get list of all configuration fields."""
    return list(get_schema_instance().__dataclass_fields__.keys())
