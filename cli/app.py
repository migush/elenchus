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
from .commands.set_config import set_config_cmd
from .commands.info import info
from .commands.test_config import test_config_cmd
from .commands.list_prompts import list_prompts


def version_callback(value: bool):
    """
    Print the CLI version and exit when the version flag is set.
    
    If `value` is truthy (the user passed the global --version/-V flag), this prints the current
    Elenchus CLI version and terminates the application by raising typer.Exit.
    
    Parameters:
        value (bool): The parsed value of the global version flag.
    
    Raises:
        typer.Exit: Always raised when `value` is truthy to stop CLI execution after printing the version.
    """
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
app.command(name="set-config")(set_config_cmd)
app.command(name="info")(info)
app.command(name="test-config")(test_config_cmd)
app.command(name="list-prompts")(list_prompts)


def run_app():
    """
    Run the Typer CLI, ensuring help is shown when no arguments are provided.
    
    If the process was invoked without additional command-line arguments, inserts `--help` into sys.argv so the CLI prints usage and exits; otherwise invokes the Typer app normally.
    """

    if len(sys.argv) == 1:
        sys.argv.insert(1, "--help")
    app()
