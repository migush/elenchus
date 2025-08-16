#!/usr/bin/env python3
"""Test script to verify lazy_command decorator error handling."""

import pytest
from cli.app import lazy_command


# Test the lazy_command decorator
@lazy_command("nonexistent.module", "nonexistent_function")
def decorated_import_error():
    pass


@lazy_command("elenchus.cli.app", "nonexistent_function")
def decorated_attribute_error():
    pass


@lazy_command("elenchus.cli.app", "main")
def decorated_success():
    return "Success!"


def test_import_error():
    """Test that lazy_command raises RuntimeError for import errors."""
    with pytest.raises(RuntimeError):
        decorated_import_error()


def test_attribute_error():
    """Test that lazy_command raises RuntimeError for attribute errors."""
    with pytest.raises(RuntimeError):
        decorated_attribute_error()


def test_success():
    """Test that lazy_command works correctly for valid imports."""
    result = decorated_success()
    assert result is not None
