"""
Info command for displaying framework information.
"""

import typer


def info():
    """Show detailed information about the framework."""
    typer.echo("Elenchus - CSV-based Experimental Results & Test Generation Framework")
    typer.echo("=" * 50)
    typer.echo("A framework for automatically generating comprehensive")
    typer.echo("test suites for HumanEval programming problems using LLMs.")
    typer.echo()
    typer.echo(
        "Experimental results are stored in CSV files under the 'experiments' directory:"
    )
    typer.echo("  - results/: monthly experiment CSVs")
    typer.echo("  - prompts/: prompt technique registry CSV")
    typer.echo("  - models/: model registry CSV")
    typer.echo("  - analysis/: generated analysis and exports")
    typer.echo()
    typer.echo("Phases:")
    typer.echo("  Phase I: Test generation and executability")
    typer.echo("  Phase II: Test suite optimization")
    typer.echo("  Phase III: Coverage analysis")
    typer.echo("  Phase IV: Final validation")
    typer.echo()
    typer.echo("For more information, see the implementation plan.")
