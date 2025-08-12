"""
Simple LLM integration using LiteLLM directly.
"""

from typing import Dict, Any, List
import typer
from litellm import completion, acompletion
from litellm.exceptions import OpenAIError


def generate_text(config: Dict[str, Any], prompt: str, **kwargs) -> str:
    """Generate text using LiteLLM directly."""
    try:
        # Build completion arguments - all values must come from config
        completion_kwargs = {
            "model": config["llm_model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", config["llm_temperature"]),
            "max_tokens": kwargs.get("max_tokens", config["llm_max_tokens"]),
            "timeout": kwargs.get("timeout", config["llm_timeout"]),
        }

        # Add API key if provided
        api_key = config.get("llm_api_key")
        if api_key:
            completion_kwargs["api_key"] = api_key

        # Add base URL if provided
        base_url = config.get("llm_base_url")
        if base_url:
            completion_kwargs["api_base"] = base_url

        # Add any additional kwargs
        completion_kwargs.update(kwargs)

        # Call LiteLLM directly
        response = completion(**completion_kwargs)
        return response.choices[0].message.content

    except OpenAIError as e:
        typer.echo(f"❌ LLM error: {e}")
        raise
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}")
        raise


async def agenerate_text(config: Dict[str, Any], prompt: str, **kwargs) -> str:
    """Generate text asynchronously using LiteLLM directly."""
    try:
        # Build completion arguments - all values must come from config
        completion_kwargs = {
            "model": config["llm_model"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", config["llm_temperature"]),
            "max_tokens": kwargs.get("max_tokens", config["llm_max_tokens"]),
            "timeout": kwargs.get("timeout", config["llm_timeout"]),
        }

        # Add API key if provided
        api_key = config.get("llm_api_key")
        if api_key:
            completion_kwargs["api_key"] = api_key

        # Add base URL if provided
        base_url = config.get("llm_base_url")
        if base_url:
            completion_kwargs["api_base"] = base_url

        # Add any additional kwargs
        completion_kwargs.update(kwargs)

        # Call LiteLLM directly
        response = await acompletion(**completion_kwargs)
        return response.choices[0].message.content

    except OpenAIError as e:
        typer.echo(f"❌ LLM error: {e}")
        raise
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}")
        raise


def generate_with_messages(
    config: Dict[str, Any], messages: List[Dict[str, str]], **kwargs
) -> str:
    """Generate text using a list of messages."""
    try:
        # Build completion arguments - all values must come from config
        completion_kwargs = {
            "model": config["llm_model"],
            "messages": messages,
            "temperature": kwargs.get("temperature", config["llm_temperature"]),
            "max_tokens": kwargs.get("max_tokens", config["llm_max_tokens"]),
            "timeout": kwargs.get("timeout", config["llm_timeout"]),
        }

        # Add API key if provided
        api_key = config.get("llm_api_key")
        if api_key:
            completion_kwargs["api_key"] = api_key

        # Add base URL if provided
        base_url = config.get("llm_base_url")
        if base_url:
            completion_kwargs["api_base"] = base_url

        # Add any additional kwargs
        completion_kwargs.update(kwargs)

        # Call LiteLLM directly
        response = completion(**completion_kwargs)
        return response.choices[0].message.content

    except OpenAIError as e:
        typer.echo(f"❌ LLM error: {e}")
        raise
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}")
        raise


def test_llm_connection(config: Dict[str, Any]) -> bool:
    """Test LLM connection with a simple prompt."""
    try:
        test_prompt = "Hello, this is a test. Please respond with 'OK' if you can see this message."
        response = generate_text(config, test_prompt, max_tokens=10)
        typer.echo("✅ LLM connection test successful")
        typer.echo(f"   Model: {config.get('llm_model')}")
        typer.echo(f"   Response: {response.strip()}")
        return True
    except Exception as e:
        typer.echo(f"❌ LLM connection test failed: {e}")
        return False
