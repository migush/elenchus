#!/usr/bin/env python3
"""
Elenchus CLI - Main entry point for the HumanEval test generation framework.
"""

import typer
import os
import tempfile
from typing import Optional, Iterable, Dict
from __init__ import __version__

import requests
import gzip
import json
import yaml
from pathlib import Path


class Config:
    """Configuration management for Elenchus CLI."""

    DEFAULT_CONFIG = {
        "human_eval_url": "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
        "output_dir": "generated_tests",
        "max_iterations": 5,
        "llm_model": "gpt-4",
    }

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        config_dir = Path.home() / ".elenchus"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir / "config.yaml")

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = yaml.safe_load(f) or {}
                    # Merge with defaults to ensure all keys exist
                    return {**self.DEFAULT_CONFIG, **config}
            except Exception as e:
                typer.echo(f"Warning: Could not load config file: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

    def _save_config(self, config: Dict) -> None:
        """Save configuration to file."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        except Exception as e:
            typer.echo(f"Warning: Could not save config file: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value and save to file."""
        self.config[key] = value
        self._save_config(self.config)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)

    def show(self) -> None:
        """Display current configuration."""
        typer.echo("Current configuration:")
        for key, value in self.config.items():
            typer.echo(f"  - {key}: {value}")


# Global configuration instance
config = Config()


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    with open(filename, "rb") as gzfp:
        with gzip.open(gzfp, "rt") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def write_task_to_output_dir(task: dict, output_dir: str) -> None:
    """
    Writes a task to a file in the specified output directory.
    The file will contain the prompt followed by the canonical solution.
    """
    # Create the file path from task_id
    task_id = task["task_id"].replace("/", "/he_")
    file_path = os.path.join(output_dir, f"{task_id}.py")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write the content to the file
    with open(file_path, "w") as f:
        f.write(task["prompt"])
        f.write(task["canonical_solution"])


def extract_human_eval_to_dir(
    output_dir: str, human_eval_url: Optional[str] = None
) -> None:
    """
    Downloads the HumanEval dataset and extracts PUTs to the specified output directory.
    """
    # Use provided URL or get from config
    url = human_eval_url or config.get("human_eval_url")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create a temporary file for downloading
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as temp_file:
        temp_path = temp_file.name

        # Download the file to temporary location
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save to temporary file
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)

    # Process each problem and write to output directory
    problem_count = 0
    for problem in stream_jsonl(temp_path):
        write_task_to_output_dir(problem, output_dir)
        problem_count += 1

    # Clean up temporary file
    os.unlink(temp_path)

    return problem_count


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


@app.command()
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


@app.command()
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


@app.command()
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
    is_global_option = len(sys.argv) > 1 and sys.argv[1].startswith("-")

    # Only insert --help if no command is provided and it's not a global option
    if len(sys.argv) == 1 or (
        not is_global_option and sys.argv[1] not in available_commands
    ):
        sys.argv.insert(1, "--help")
    app()
