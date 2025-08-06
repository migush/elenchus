"""
Run phase command for executing specific phases of the test generation process.
"""

import typer
from typing import Optional


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

    typer.echo(f"Running Phase {phase}")
    if config_file:
        typer.echo(f"Using config file: {config_file}")
    # TODO: Implement phase execution logic
    typer.echo(f"Phase {phase} completed!")
