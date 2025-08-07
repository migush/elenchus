"""
Main CLI application for Elenchus.
"""

import sys
import typer

from __init__ import __version__

# Import command functions
from .commands.extract import extract
from .commands.generate import generate_tests
from .commands.run_phase import run_phase
from .commands.config import config_cmd
from .commands.info import info


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


# Register commands
app.command(name="extract")(extract)
app.command(name="generate-tests")(generate_tests)
app.command(name="run-phase")(run_phase)
app.command(name="config")(config_cmd)
app.command(name="info")(info)


def run_app():
    """Run the CLI application with proper help handling."""

    if len(sys.argv) == 1:
        sys.argv.insert(1, "--help")
    app()
