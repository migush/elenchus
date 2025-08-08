"""
Generate tests command for test generation using LLM.
"""

import typer
from typing import Optional
from pathlib import Path

from config.manager import config
from core.test_generator import generate_test_for_put, get_all_put_ids


def generate_tests(
    input_dir: str = typer.Option(
        "HumanEval",
        "--input-dir",
        "-i",
        help="Input directory containing extracted PUTs",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for generated tests",
    ),
    max_iterations: Optional[int] = typer.Option(
        None,
        "--max-iterations",
        "-m",
        help="Maximum number of test generation iterations",
    ),
):
    """Generate tests for extracted PUTs using LLM."""

    # Get configuration with CLI args taking priority
    cli_args = {}
    if output_dir is not None:
        cli_args["output_dir"] = output_dir
    if max_iterations is not None:
        cli_args["max_iterations"] = max_iterations

    final_config = config.get_config_with_priority(cli_args)

    # Use configuration values
    output_dir = final_config["output_dir"]
    max_iterations = final_config["max_iterations"]

    # Validate configuration
    if not config.validate():
        typer.echo("Configuration validation failed!")
        raise typer.Exit(1)

    # Check if LLM API key is configured (only needed for non-local providers)
    llm_api_key = final_config.get("llm_api_key")
    llm_model = final_config.get("llm_model")

    # Check if we need an API key for this provider
    # Local providers typically don't need API keys
    local_providers = ["ollama/", "local/", "huggingface/"]
    needs_api_key = not any(
        llm_model and llm_model.startswith(provider) for provider in local_providers
    )

    if not llm_api_key and needs_api_key:
        typer.echo("❌ LLM API key not configured!")
        typer.echo("Set it with: elenchus set-config llm_api_key <your-key>")
        typer.echo("Or use environment variable: ELENCHUS_LLM_API_KEY")
        raise typer.Exit(1)

    typer.echo(f"Generating tests from {input_dir} to {output_dir}")
    typer.echo(f"Max iterations: {max_iterations}")
    typer.echo(f"Using LLM model: {final_config.get('llm_model')}")
    typer.echo(f"LLM temperature: {final_config.get('llm_temperature')}")

    # Get all PUT IDs from the input directory
    put_ids = get_all_put_ids(input_dir)

    if not put_ids:
        typer.echo(f"❌ No PUT files found in {input_dir}")
        raise typer.Exit(1)

    typer.echo(f"Found {len(put_ids)} PUT files to process")

    # Create output directory structure
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create logs directory
    logs_dir = output_path / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Process each PUT
    successful = 0
    failed = 0

    for i, put_id in enumerate(put_ids, 1):
        typer.echo(f"\n[{i}/{len(put_ids)}] Processing {put_id}...")

        try:
            result = generate_test_for_put(put_id, final_config, str(logs_dir))

            if result["success"]:
                typer.echo(f"✅ {put_id}: Success (log: {result['log_file']})")
                successful += 1
            else:
                typer.echo(f"❌ {put_id}: Failed - {result['error']}")
                failed += 1

        except Exception as e:
            typer.echo(f"❌ {put_id}: Unexpected error - {e}")
            failed += 1

    # Summary
    typer.echo(f"\n{'='*50}")
    typer.echo("Test Generation Summary")
    typer.echo(f"{'='*50}")
    typer.echo(f"Total PUTs processed: {len(put_ids)}")
    typer.echo(f"Successful: {successful}")
    typer.echo(f"Failed: {failed}")
    typer.echo(f"Logs directory: {logs_dir}")
    typer.echo("Test generation completed!")
