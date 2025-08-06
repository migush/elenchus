"""
Info command for displaying framework information.
"""

import typer


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
