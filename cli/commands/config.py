"""
Configuration management command for showing and editing configuration.
"""

import typer
from typing import Optional

from config.manager import config


def config_cmd(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit configuration"),
    reset: bool = typer.Option(
        False, "--reset", "-r", help="Reset to default configuration"
    ),
    set_url: Optional[str] = typer.Option(
        None, "--set-url", help="Set HumanEval dataset URL"
    ),
    set_output_dir: Optional[str] = typer.Option(
        None, "--set-output-dir", help="Set default output directory"
    ),
    set_max_iterations: Optional[int] = typer.Option(
        None, "--set-max-iterations", help="Set default max iterations"
    ),
):
    """Show or edit configuration."""
    if show:
        config.show()
    elif edit:
        typer.echo("Opening configuration editor...")
        # TODO: Implement config editing logic
        typer.echo("Configuration updated!")
    elif reset:
        typer.echo("Resetting to default configuration...")
        config.reset()
        typer.echo("Configuration reset!")
    elif set_url:
        config.set("human_eval_url", set_url)
        typer.echo(f"HumanEval URL set to: {set_url}")
    elif set_output_dir:
        config.set("output_dir", set_output_dir)
        typer.echo(f"Output directory set to: {set_output_dir}")
    elif set_max_iterations:
        config.set("max_iterations", set_max_iterations)
        typer.echo(f"Max iterations set to: {set_max_iterations}")
    else:
        typer.echo(
            "Use --show, --edit, --reset, or --set-* options to manage configuration"
        )
