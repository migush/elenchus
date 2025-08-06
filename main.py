#!/usr/bin/env python3
"""
Elenchus CLI - Main entry point for the HumanEval test generation framework.
"""

import typer
from typing import Optional
from __init__ import __version__


def version_callback(value: bool):
    if value:
        typer.echo(f"Elenchus CLI v{__version__}")
        raise typer.Exit()

app = typer.Typer(
    name="elenchus",
    help="HumanEval test generation framework",
    add_completion=False,
    no_args_is_help=True,
)

# Add global --version / -V option
@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version information and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    pass


@app.command()
def extract(
    input_dir: str = typer.Option("HumanEval", "--input-dir", "-i", help="Input directory containing HumanEval problems"),
    output_dir: str = typer.Option("extracted", "--output-dir", "-o", help="Output directory for extracted PUTs"),
):
    """Extract PUTs (Programs Under Test) from HumanEval dataset."""
    typer.echo(f"Extracting PUTs from {input_dir} to {output_dir}")
    # TODO: Implement PUT extraction logic
    typer.echo("PUT extraction completed!")


@app.command()
def generate_tests(
    input_dir: str = typer.Option("extracted", "--input-dir", "-i", help="Input directory containing extracted PUTs"),
    output_dir: str = typer.Option("generated_tests", "--output-dir", "-o", help="Output directory for generated tests"),
    max_iterations: int = typer.Option(5, "--max-iterations", "-m", help="Maximum number of test generation iterations"),
):
    """Generate tests for extracted PUTs using LLM."""
    typer.echo(f"Generating tests from {input_dir} to {output_dir}")
    typer.echo(f"Max iterations: {max_iterations}")
    # TODO: Implement test generation logic
    typer.echo("Test generation completed!")


@app.command()
def run_phase(
    phase: str = typer.Argument(..., help="Phase to run (I, II, III, or IV)"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Configuration file path"),
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


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit configuration"),
    reset: bool = typer.Option(False, "--reset", "-r", help="Reset to default configuration"),
):
    """Show or edit configuration."""
    if show:
        typer.echo("Current configuration:")
        # TODO: Implement config display logic
        typer.echo("  - Output directory: generated_tests")
        typer.echo("  - Max iterations: 5")
        typer.echo("  - LLM model: gpt-4")
    elif edit:
        typer.echo("Opening configuration editor...")
        # TODO: Implement config editing logic
        typer.echo("Configuration updated!")
    elif reset:
        typer.echo("Resetting to default configuration...")
        # TODO: Implement config reset logic
        typer.echo("Configuration reset!")
    else:
        typer.echo("Use --show, --edit, or --reset to manage configuration")


@app.command()
def info():
    """Show detailed information about the framework."""
    typer.echo("Elenchus - HumanEval Test Generation Framework")
    typer.echo("=" * 50)
    typer.echo("A framework for automatically generating comprehensive")
    typer.echo("test suites for HumanEval programming problems using LLMs.")
    typer.echo()
    typer.echo("Phases:")
    typer.echo("  Phase I: Test generation and executability")
    typer.echo("  Phase II: Test suite optimization")
    typer.echo("  Phase III: Coverage analysis")
    typer.echo("  Phase IV: Final validation")
    typer.echo()
    typer.echo("For more information, see the implementation plan.")


if __name__ == "__main__":
    import sys
    from typer.main import get_command, get_command_name
    
    # Get all available commands and options dynamically
    command = get_command(app)
    available_commands = [get_command_name(key) for key in command.commands.keys()]
    
    # Check if the first argument is a global option (starts with -)
    is_global_option = len(sys.argv) > 1 and sys.argv[1].startswith('-')
    
    # Only insert --help if no command is provided and it's not a global option
    if len(sys.argv) == 1 or (not is_global_option and sys.argv[1] not in available_commands):
        sys.argv.insert(1, "--help")
    app() 