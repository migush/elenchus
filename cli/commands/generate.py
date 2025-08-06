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
    output_dir: str = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for generated tests",
    ),
    max_iterations: int = typer.Option(
        None,
        "--max-iterations",
        "-m",
        help="Maximum number of test generation iterations",
    ),
):
    """Generate tests for extracted PUTs using LLM."""
    # Use config values if not provided
    output_dir = output_dir or config.get("output_dir")
    max_iterations = max_iterations or config.get("max_iterations")

    typer.echo(f"Generating tests from {input_dir} to {output_dir}")
    typer.echo(f"Max iterations: {max_iterations}")
    # TODO: Implement test generation logic
    typer.echo("Test generation completed!")
