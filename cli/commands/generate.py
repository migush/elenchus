"""
Generate tests command for test generation using LLM.
"""

import typer
from typing import Optional
from pathlib import Path

from config.manager import config
from core.test_generator import generate_test_for_put, get_all_put_ids
from core.csv_manager import ExperimentCSVManager
from core.experiment_recorder import ExperimentRecorder


def generate_tests(
    input_dir: str = typer.Option(
        "HumanEval",
        "--input-dir",
        "-i",
        help="Input directory containing extracted PUTs",
    ),
    file: Optional[str] = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to a specific PUT file (e.g., HumanEval/he_0.py)",
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
    run: bool = typer.Option(
        False,
        "--run",
        help="Run each generated test with pytest and report pass/fail",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-n",
        help="Process only the first N PUTs",
    ),
    coverage: bool = typer.Option(
        False,
        "--coverage",
        help="Measure coverage for the target module using pytest-cov",
    ),
    prompt_id: Optional[str] = typer.Option(
        None,
        "--prompt-id",
        "-p",
        help="Prompt technique ID to use (defaults to config default_prompt_id)",
    ),
):
    """Generate tests for extracted PUTs using LLM."""

    # Get configuration with CLI args taking priority
    cli_args = {}
    if output_dir is not None:
        cli_args["output_dir"] = output_dir
    if max_iterations is not None:
        cli_args["max_iterations"] = max_iterations

    # Include prompt_id in CLI args if provided
    if prompt_id is not None:
        cli_args["default_prompt_id"] = prompt_id

    final_config = config.get_config_with_priority(cli_args)

    # Use configuration values - all must be present
    output_dir = final_config["output_dir"]
    max_iterations = final_config["max_iterations"]
    experiments_dir = final_config["experiments_dir"]
    prompt_id_val = final_config["default_prompt_id"]
    track_experiments = final_config["track_experiments"]

    # Validate configuration
    if not config.validate():
        typer.echo("Configuration validation failed!")
        raise typer.Exit(1)

    # Check if LLM API key is configured (only needed for non-local providers)
    llm_api_key = final_config.get("llm_api_key")
    llm_model = final_config["llm_model"]

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
    typer.echo(f"Using LLM model: {final_config['llm_model']}")
    typer.echo(f"LLM temperature: {final_config['llm_temperature']}")
    typer.echo(f"Prompt ID: {prompt_id_val}")

    # Determine targets: either a single file or a directory listing
    if file:
        file_path = Path(file)
        if not file_path.exists() or not file_path.is_file():
            typer.echo(f"❌ File not found: {file}")
            raise typer.Exit(1)
        # For a specific file, derive put_id and human_eval_dir from the path
        put_ids = [file_path.stem]
        input_dir = str(file_path.parent)
        typer.echo(f"Processing single file: {file} (put_id: {put_ids[0]})")
    else:
        # Get all PUT IDs from the input directory
        put_ids = get_all_put_ids(input_dir)
        if not put_ids:
            typer.echo(f"❌ No PUT files found in {input_dir}")
            raise typer.Exit(1)
        if limit is not None and limit > 0:
            put_ids = put_ids[:limit]
        typer.echo(f"Found {len(put_ids)} PUT files to process")

    # Create output directory structure
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create logs and tests directories
    logs_dir = output_path / "logs"
    logs_dir.mkdir(exist_ok=True)
    tests_dir = output_path / "tests"
    tests_dir.mkdir(exist_ok=True)

    # Prepare experiment recording
    csv_manager = ExperimentCSVManager(experiments_dir=experiments_dir)
    recorder = ExperimentRecorder(csv_manager) if track_experiments else None

    # Process each PUT
    successful = 0
    failed = 0

    for i, put_id in enumerate(put_ids, 1):
        typer.echo(f"\n[{i}/{len(put_ids)}] Processing {put_id}...")

        try:
            result = generate_test_for_put(
                put_id,
                final_config,
                log_dir=str(logs_dir),
                human_eval_dir=input_dir,
                tests_dir=str(tests_dir),
                run=run,
                measure_coverage=coverage,
                prompt_id=prompt_id_val,
                experiment_recorder=recorder,
            )

            if result["success"]:
                syntax_status = "OK" if result.get("syntax_ok") else "FAIL"
                run_suffix = ""
                if result.get("ran"):
                    run_suffix = f"; run: {'PASS' if result.get('passed') else 'FAIL'}"
                    if coverage and result.get("coverage_percent") is not None:
                        run_suffix += f"; cov: {result['coverage_percent']}%"
                typer.echo(
                    f"✅ {put_id}: Success (syntax: {syntax_status}{run_suffix})\n   test: {result.get('test_file')}\n   log:  {result.get('log_file')}"
                )
                successful += 1
            else:
                # Show failure; coverage percent only applies to passing tests.
                # If coverage is enabled but the test didn't pass, show 'cov: n/a' when a report exists.
                if coverage:
                    cov_suffix = ""
                    if (
                        result.get("coverage_xml")
                        and result.get("coverage_percent") is None
                    ):
                        cov_suffix = " (cov: n/a)"
                    typer.echo(f"❌ {put_id}: Failed - {result['error']}{cov_suffix}")
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
