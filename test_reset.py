#!/usr/bin/env python3
"""Test script to verify reset method fix."""

import os
import pytest
from unittest.mock import Mock

from config.manager import Config
from config.schema import get_default_config


def test_config_reset_method():
    """Test that Config.reset() method works without AttributeError and resets to defaults."""
    # Test Config instance creation
    config = Config()
    assert isinstance(config, Config), f"Expected Config instance, got {type(config)}"

    # Test reset method (should not raise AttributeError now)
    config.reset()

    # Verify the config was reset to defaults
    default_config = get_default_config()
    for key, expected_value in default_config.items():
        assert (
            config.config[key] == expected_value
        ), f"Config key '{key}' should be reset to {expected_value}, got {config.config[key]}"


def test_config_reset_calls_save_config(monkeypatch):
    """Test that Config.reset() calls _save_config with the reset configuration."""
    # Create a mock for _save_config
    mock_save = Mock()

    # Create Config instance and patch the _save_config method
    config = Config()
    monkeypatch.setattr(config, "_save_config", mock_save)

    # Call reset
    config.reset()

    # Verify _save_config was called
    assert mock_save.called, "Config.reset() should call _save_config"

    # Verify it was called with the reset config
    call_args = mock_save.call_args
    assert call_args is not None, "_save_config should be called with arguments"

    # The first argument should be the config dict
    saved_config = call_args[0][0]
    assert isinstance(saved_config, dict), "Saved config should be a dictionary"

    # Verify it contains the expected default values
    default_config = get_default_config()
    for key, expected_value in default_config.items():
        assert (
            saved_config[key] == expected_value
        ), f"Saved config key '{key}' should be {expected_value}, got {saved_config[key]}"


def test_config_reset_preserves_environment_variables(monkeypatch):
    """Test that Config.reset() preserves environment variables after resetting to defaults."""
    # Set up environment variables
    test_env_vars = {
        "ELENCHUS_LLM_API_KEY": "test-api-key-12345",
        "ELENCHUS_LLM_MODEL": "test-model",
    }

    # Mock os.environ.get to return our test values
    def mock_get_env(key, default=None):
        return test_env_vars.get(key, default)

    # Create Config instance and patch environment variable loading
    config = Config()
    monkeypatch.setattr(os.environ, "get", mock_get_env)

    # Mock _save_config to avoid file operations
    mock_save = Mock()
    monkeypatch.setattr(config, "_save_config", mock_save)

    # Call reset
    config.reset()

    # Verify environment variables are preserved
    assert (
        config.config["llm_api_key"] == "test-api-key-12345"
    ), "Environment variable llm_api_key should be preserved"
    assert (
        config.config["llm_model"] == "test-model"
    ), "Environment variable llm_model should be preserved"

    # Verify other config values are reset to defaults
    default_config = get_default_config()
    assert (
        config.config["max_iterations"] == default_config["max_iterations"]
    ), "max_iterations should be reset to default"
    assert (
        config.config["llm_temperature"] == default_config["llm_temperature"]
    ), "llm_temperature should be reset to default"
