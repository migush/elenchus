"""
Main CLI application for Elenchus.
"""

import sys
import typer
from functools import wraps

# Import version from parent package
try:
    # Try to import from the installed package first
    import importlib.metadata

    __version__ = importlib.metadata.version("elenchus")
except ImportError:
    # Fallback to dynamic import from source
    import importlib.util
    import os

    # Get the path to the parent directory's __init__.py (current working directory)
    parent_dir = os.getcwd()
    init_path = os.path.join(parent_dir, "__init__.py")

    if os.path.exists(init_path):
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("elenchus_init", init_path)
        elenchus_init = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(elenchus_init)
        __version__ = elenchus_init.__version__
    else:
        # Fallback version
        __version__ = "0.1.0"


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


def lazy_command(module_path: str, function_name: str):
    """Decorator for lazy loading of command functions."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Import the module only when the command is executed
                module = __import__(module_path, fromlist=[function_name])
                command_func = getattr(module, function_name)

                # Validate that the retrieved attribute is callable
                if not callable(command_func):
                    raise RuntimeError(
                        f"Attribute '{function_name}' from module '{module_path}' is not callable. "
                        f"Got type: {type(command_func).__name__}"
                    )

                # Call the original function with the same signature
                return command_func(*args, **kwargs)

            except ImportError as e:
                raise RuntimeError(
                    f"Failed to import module '{module_path}': {e}"
                ) from e
            except AttributeError as e:
                raise RuntimeError(
                    f"Function '{function_name}' not found in module '{module_path}': {e}"
                ) from e

        return wrapper

    return decorator


# Register commands with lazy imports to avoid heavy modules loading on startup
@app.command(name="extract")
@lazy_command("cli.commands.extract", "extract")
def extract_cmd(
    output_dir: str = typer.Option(
        None, "--output-dir", "-o", help="Output directory for extracted PUTs"
    ),
    human_eval_url: str = typer.Option(
        None, "--url", "-u", help="Custom HumanEval dataset URL"
    ),
):
    """Extract PUTs (Programs Under Test) from HumanEval dataset."""
    pass


@app.command(name="generate-tests")
@lazy_command("cli.commands.generate", "generate_tests")
def generate_tests_cmd(
    input_dir: str = typer.Option(
        "HumanEval",
        "--input-dir",
        "-i",
        help="Input directory containing extracted PUTs",
    ),
    file: str = typer.Option(None, "--file", "-f", help="Path to a specific PUT file"),
    output_dir: str = typer.Option(
        None, "--output-dir", "-o", help="Output directory for generated tests"
    ),
    max_iterations: int = typer.Option(
        None,
        "--max-iterations",
        "-m",
        help="Maximum number of test generation iterations",
    ),
    run: bool = typer.Option(
        False, "--run", help="Run each generated test with pytest and report pass/fail"
    ),
    limit: int = typer.Option(
        None, "--limit", "-n", help="Process only the first N PUTs"
    ),
    coverage: bool = typer.Option(
        False,
        "--coverage",
        help="Measure coverage for the target module using pytest-cov",
    ),
    prompt_id: str = typer.Option(
        None, "--prompt-id", "-p", help="Prompt technique ID to use"
    ),
):
    """Generate tests for extracted PUTs using LLM."""
    pass


@app.command(name="run-phase")
@lazy_command("cli.commands.run_phase", "run_phase")
def run_phase_cmd(
    phase: str = typer.Argument(..., help="Phase to run (I, II, III, or IV)"),
    config_file: str = typer.Option(
        None, "--config", "-c", help="Configuration file path"
    ),
):
    """Run a specific phase of the test generation process."""
    pass


@app.command(name="config")
@lazy_command("cli.commands.config", "config_cmd")
def config_cmd_wrapper(
    env: bool = typer.Option(
        False, "--env-vars", "-e", help="Show environment variables"
    ),
):
    """Show or edit configuration."""
    pass


@app.command(name="set-config")
@lazy_command("cli.commands.set_config", "set_config_cmd")
def set_config_cmd_wrapper(
    field: str = typer.Option(None, "--field", "-f", help="Configuration field to set"),
    value: str = typer.Option(None, "--value", "-v", help="Value to set"),
):
    """Set a configuration field dynamically."""
    pass


@app.command(name="info")
@lazy_command("cli.commands.info", "info")
def info_cmd():
    """Show detailed information about the framework."""
    pass


@app.command(name="test-config")
@lazy_command("cli.commands.test_config", "test_config_cmd")
def test_config_cmd_wrapper():
    """Test configuration and LLM connectivity."""
    pass


@app.command(name="list-prompts")
@lazy_command("cli.commands.list_prompts", "list_prompts")
def list_prompts_cmd():
    """List all available prompt techniques."""
    pass


def run_app():
    """
    Run the Typer CLI, ensuring help is shown when no arguments are provided.

    If the process was invoked without additional command-line arguments, inserts `--help` into sys.argv so the CLI prints usage and exits; otherwise invokes the Typer app normally.
    """

    if len(sys.argv) == 1:
        sys.argv.insert(1, "--help")
    app()
