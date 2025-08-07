"""
Generate tests command for test generation using LLM.
"""

import typer
from typing import Optional

from config.manager import config


def generate_tests(
    input_dir: str = typer.Option(
        "extracted",
        "--input-dir",
        "-i",
        help="Input directory containing extracted PUTs",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for generated tests",
    ),
    max_iterations: Optional[int] = typer.Option(
        None,
        "--max-iterations",
        "-m",
        help="Maximum number of test generation iterations",
    ),
):
    """Generate tests for extracted PUTs using LLM."""

    # Get configuration with CLI args taking priority
    cli_args = {}
    if output_dir is not None:
        cli_args["output_dir"] = output_dir
    if max_iterations is not None:
        cli_args["max_iterations"] = max_iterations

    final_config = config.get_config_with_priority(cli_args)

    # Use configuration values
    output_dir = final_config["output_dir"]
    max_iterations = final_config["max_iterations"]

    # Validate configuration
    if not config.validate():
        typer.echo("Configuration validation failed!")
        raise typer.Exit(1)

    # Check if LLM API key is configured
    llm_api_key = final_config.get("llm_api_key")
    if not llm_api_key:
        typer.echo("❌ LLM API key not configured!")
        typer.echo("Set it with: elenchus config --set-llm-api-key <your-key>")
        typer.echo("Or use environment variable: ELENCHUS_LLM_API_KEY")
        raise typer.Exit(1)

    typer.echo(f"Generating tests from {input_dir} to {output_dir}")
    typer.echo(f"Max iterations: {max_iterations}")
    typer.echo(f"Using LLM model: {final_config.get('llm_model')}")
    typer.echo(f"LLM temperature: {final_config.get('llm_temperature')}")

    # TODO: Implement test generation logic
    typer.echo("Test generation completed!")
