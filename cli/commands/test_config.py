"""
Configuration testing command for validating configuration and LLM connectivity.
"""

import typer
from config.manager import config


def test_config_cmd():
    """Test configuration and LLM connectivity."""
    typer.echo("🔧 Testing Elenchus Configuration")
    typer.echo("=" * 50)

    # Test 1: Configuration Loading
    typer.echo("\n1. Configuration Loading Test")
    typer.echo("-" * 30)
    try:
        config.show()
        typer.echo("✅ Configuration loaded successfully")
    except Exception as e:
        typer.echo(f"❌ Configuration loading failed: {e}")
        raise typer.Exit(1)

    # Test 2: Configuration Validation
    typer.echo("\n2. Configuration Validation Test")
    typer.echo("-" * 30)
    if config.validate():
        typer.echo("✅ Configuration validation passed")
    else:
        typer.echo("❌ Configuration validation failed")
        raise typer.Exit(1)

    # Test 3: Environment Variables Test
    typer.echo("\n3. Environment Variables Test")
    typer.echo("-" * 30)
    env_vars_found = False
    for env_var, config_key in config.ENV_MAPPING.items():
        value = config.env_config.get(config_key)
        if value is not None:
            if not env_vars_found:
                typer.echo("Found environment variables:")
                env_vars_found = True
            # Mask sensitive values
            if config_key == "llm_api_key":
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            typer.echo(f"  - {env_var}: {display_value}")

    if not env_vars_found:
        typer.echo("ℹ️  No environment variables found (using defaults)")

    # Test 4: LLM Configuration Test
    typer.echo("\n4. LLM Configuration Test")
    typer.echo("-" * 30)
    llm_api_key = config.get("llm_api_key")
    llm_model = config.get("llm_model")
    llm_provider = config.get("llm_provider")

    if llm_api_key:
        typer.echo(f"✅ LLM API key configured (provider: {llm_provider})")
        typer.echo(f"✅ LLM model: {llm_model}")

        # Test 5: LLM Connectivity Test (if API key available)
        typer.echo("\n5. LLM Connectivity Test")
        typer.echo("-" * 30)
        try:
            # TODO: Implement actual LLM connectivity test when LLM integration is added
            typer.echo("ℹ️  LLM connectivity test not yet implemented")
            typer.echo("   (Will be available when LLM integration is added)")
        except Exception as e:
            typer.echo(f"❌ LLM connectivity test failed: {e}")
    else:
        typer.echo("⚠️  LLM API key not configured")
        typer.echo("   Set it with: elenchus config --set-llm-api-key <your-key>")
        typer.echo("   Or use environment variable: ELENCHUS_LLM_API_KEY")

    # Test 6: File System Test
    typer.echo("\n6. File System Test")
    typer.echo("-" * 30)
    output_dir = config.get("output_dir")
    try:
        from pathlib import Path

        output_path = Path(output_dir)
        if output_path.exists():
            typer.echo(f"✅ Output directory exists: {output_dir}")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            typer.echo(f"✅ Output directory created: {output_dir}")
    except Exception as e:
        typer.echo(f"❌ Output directory test failed: {e}")
        raise typer.Exit(1)

    # Test 7: Configuration Priority Test
    typer.echo("\n7. Configuration Priority Test")
    typer.echo("-" * 30)
    typer.echo("Configuration sources (highest to lowest priority):")
    typer.echo("  1. Command-line arguments")
    typer.echo("  2. Environment variables")
    typer.echo("  3. Configuration file (~/.elenchus/config.yaml)")
    typer.echo("  4. Default values")

    # Show which sources are active
    sources = []
    if config.env_config:
        sources.append("Environment variables")
    if config.config_file and Path(config.config_file).exists():
        sources.append("Configuration file")
    sources.append("Default values")

    typer.echo(f"\nActive sources: {' > '.join(sources)}")

    # Summary
    typer.echo("\n" + "=" * 50)
    typer.echo("🎉 Configuration Test Summary")
    typer.echo("=" * 50)
    typer.echo("✅ Configuration system is working correctly")

    if llm_api_key:
        typer.echo("✅ LLM configuration is ready")
        typer.echo("   You can now use LLM-dependent commands")
    else:
        typer.echo("⚠️  LLM configuration incomplete")
        typer.echo("   Set your API key to use LLM features")

    typer.echo("\nNext steps:")
    typer.echo("  - Run 'elenchus config --show' to see current settings")
    typer.echo("  - Run 'elenchus config --export' to see environment variables")
    typer.echo("  - Set LLM API key: elenchus config --set-llm-api-key <key>")
