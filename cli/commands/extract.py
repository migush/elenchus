"""
Extract command for downloading and extracting HumanEval dataset.
"""

import typer
from typing import Optional

from core.extractor import extract_human_eval_to_dir
from config.manager import config


def extract(
    output_dir: str = typer.Option(
        ".", "--output-dir", "-o", help="Output directory for extracted PUTs"
    ),
    human_eval_url: Optional[str] = typer.Option(
        None, "--url", "-u", help="Custom HumanEval dataset URL"
    ),
):
    """Extract PUTs (Programs Under Test) from HumanEval dataset."""
    typer.echo(f"Downloading and extracting HumanEval dataset to {output_dir}")

    if human_eval_url:
        typer.echo(f"Using custom URL: {human_eval_url}")
    else:
        typer.echo(f"Using configured URL: {config.get('human_eval_url')}")

    try:
        problem_count = extract_human_eval_to_dir(output_dir, human_eval_url)
        typer.echo(f"Successfully extracted {problem_count} PUTs to {output_dir}")
    except Exception as e:
        typer.echo(f"Error during extraction: {e}")
        raise typer.Exit(1)
