"""
CLI command to list all available prompt techniques.
"""

import typer
from core.csv_manager import ExperimentCSVManager
from core.prompt_manager import PromptManager

app = typer.Typer()


@app.command()
def list_prompts():
    """
    List all available prompt techniques.

    Retrieves all prompt techniques (including inactive ones) and prints a formatted table to the console with columns:
    ID, Name, Category, Version, Active, Description. If no techniques are found, prints "No prompt techniques found."
    """
    csv_manager = ExperimentCSVManager()
    prompt_manager = PromptManager(csv_manager)
    prompts = prompt_manager.list_prompt_techniques(active_only=False)
    if not prompts:
        typer.echo("No prompt techniques found.")
        return
    typer.echo(
        f"{'ID':<20} {'Name':<25} {'Category':<15} {'Version':<8} {'Active':<8} Description"
    )
    typer.echo("-" * 100)
    for p in prompts:
        typer.echo(
            f"{p['prompt_id']:<20} {p['name']:<25} {p['category']:<15} {p['version']:<8} {str(p['is_active']):<8} {p['description']}"
        )
