"""
Extract command for downloading and extracting HumanEval dataset.
"""

import typer
from typing import Optional

from core.extractor import extract_human_eval_to_dir
from config.manager import config


def extract(
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Output directory for extracted PUTs"
    ),
    human_eval_url: Optional[str] = typer.Option(
        None, "--url", "-u", help="Custom HumanEval dataset URL"
    ),
):
    """Extract PUTs (Programs Under Test) from HumanEval dataset."""

    # Get configuration with CLI args taking priority
    cli_args = {}
    if output_dir is not None:
        cli_args["output_dir"] = output_dir
    if human_eval_url is not None:
        cli_args["human_eval_url"] = human_eval_url

    final_config = config.get_config_with_priority(cli_args)

    # Use configuration values
    output_dir = final_config["output_dir"]
    human_eval_url = final_config["human_eval_url"]

    # Validate configuration
    if not config.validate():
        typer.echo("Configuration validation failed!")
        raise typer.Exit(1)

    typer.echo(f"Downloading and extracting HumanEval dataset to {output_dir}")
    typer.echo(f"Using URL: {human_eval_url}")

    try:
        problem_count = extract_human_eval_to_dir(output_dir, human_eval_url)
        typer.echo(f"Successfully extracted {problem_count} PUTs to {output_dir}")
    except Exception as e:
        typer.echo(f"Error during extraction: {e}")
        raise typer.Exit(1)
