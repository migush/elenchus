"""
Run phase command for executing specific phases of the test generation process.
"""

import typer
from typing import Optional

from config.manager import config


def run_phase(
    phase: str = typer.Argument(..., help="Phase to run (I, II, III, or IV)"),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Configuration file path"
    ),
):
    """Run a specific phase of the test generation process."""
    valid_phases = ["I", "II", "III", "IV"]
    if phase not in valid_phases:
        typer.echo(f"Error: Phase must be one of {valid_phases}")
        raise typer.Exit(1)

    # Validate configuration
    if not config.validate():
        typer.echo("Configuration validation failed!")
        raise typer.Exit(1)

    # Check if LLM API key is configured for LLM-dependent phases
    if phase in ["II", "III", "IV"]:  # Phases that use LLM
        llm_api_key = config.get("llm_api_key")
        if not llm_api_key:
            typer.echo("❌ LLM API key not configured!")
            typer.echo("Set it with: elenchus set-config llm_api_key <your-key>")
            typer.echo("Or use environment variable: ELENCHUS_LLM_API_KEY")
            raise typer.Exit(1)

    typer.echo(f"Running Phase {phase}")
    if config_file:
        typer.echo(f"Using config file: {config_file}")

    # Show relevant configuration for this phase
    typer.echo(f"Output directory: {config.get('output_dir')}")
    typer.echo(f"Max iterations: {config.get('max_iterations')}")

    if phase in ["II", "III", "IV"]:
        typer.echo(f"LLM model: {config.get('llm_model')}")
        typer.echo(f"LLM temperature: {config.get('llm_temperature')}")

    # TODO: Implement phase execution logic
    typer.echo(f"Phase {phase} completed!")
