"""
CSV Manager for experimental results storage and retrieval.
"""

import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd


class ExperimentCSVManager:
    """Manages experimental results stored in CSV files."""

    def __init__(self, experiments_dir: str = "experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.results_dir = self.experiments_dir / "results"
        self.prompts_dir = self.experiments_dir / "prompts"
        self.models_dir = self.experiments_dir / "models"
        self.analysis_dir = self.experiments_dir / "analysis"
        self.content_dir = self.experiments_dir / "content"

        # Create directories if they don't exist
        self._ensure_directories()

        # Initialize reference files
        self._init_reference_files()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        for directory in [
            self.results_dir,
            self.prompts_dir,
            self.models_dir,
            self.analysis_dir,
            self.content_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for content storage
        (self.content_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (self.content_dir / "responses").mkdir(parents=True, exist_ok=True)

    def _init_reference_files(self):
        """Initialize reference CSV files if they don't exist."""
        # Initialize prompt techniques file
        prompt_file = self.prompts_dir / "prompt_techniques.csv"
        if not prompt_file.exists():
            self._create_prompt_techniques_file(prompt_file)

        # Initialize model registry file
        model_file = self.models_dir / "model_registry.csv"
        if not model_file.exists():
            self._create_model_registry_file(model_file)

    def _create_prompt_techniques_file(self, file_path: Path):
        """Create initial prompt techniques CSV file."""
        headers = [
            "prompt_id",
            "name",
            "description",
            "category",
            "version",
            "created_at",
            "is_active",
        ]
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            # Add default prompt technique
            writer.writerow(
                [
                    "default",
                    "Default Prompt",
                    "Standard prompt for test generation",
                    "zero-shot",
                    "1.0",
                    datetime.now().isoformat(),
                    "True",
                ]
            )

    def _create_model_registry_file(self, file_path: Path):
        """Create initial model registry CSV file."""
        headers = [
            "model_name",
            "provider",
            "architecture",
            "estimated_size",
            "capabilities",
            "cost_per_1k_tokens",
            "max_context_length",
            "created_at",
        ]
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            # Add some common models
            common_models = [
                [
                    "gpt-4",
                    "openai",
                    "transformer",
                    "175b",
                    "code-generation,testing",
                    '{"input": 0.03, "output": 0.06}',
                    8192,
                    datetime.now().isoformat(),
                ],
                [
                    "gpt-3.5-turbo",
                    "openai",
                    "transformer",
                    "7b",
                    "code-generation,testing",
                    '{"input": 0.0015, "output": 0.002}',
                    4096,
                    datetime.now().isoformat(),
                ],
                [
                    "claude-3-sonnet",
                    "anthropic",
                    "transformer",
                    "70b",
                    "code-generation,testing",
                    '{"input": 0.003, "output": 0.015}',
                    200000,
                    datetime.now().isoformat(),
                ],
            ]
            for model in common_models:
                writer.writerow(model)

    def get_current_results_file(self) -> str:
        """Get the current month's CSV file path."""
        current_month = datetime.now().strftime("%Y_%m")
        filename = f"experiments_{current_month}.csv"
        file_path = self.results_dir / filename

        # Create file with headers if it doesn't exist
        if not file_path.exists():
            self._create_results_file(file_path)

        return str(file_path)

    def _create_results_file(self, file_path: Path):
        """Create a new results CSV file with headers."""
        headers = [
            "experiment_id",
            "timestamp",
            "put_id",
            "prompt_id",
            "prompt_version",
            "model_name",
            "model_provider",
            "model_architecture",
            "model_size",
            "code_generation_success",
            "code_iterations_needed",
            "test_generation_success",
            "test_iterations_needed",
            "test_coverage",
            "test_count",
            "test_execution_time",
            "system_prompt_file",
            "user_prompt_file",
            "llm_response_file",
            "temperature",
            "max_tokens",
            "timeout",
            "total_tokens_used",
            "cost_estimate",
            "errors",
            "warnings",
        ]

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def save_content_to_file(
        self, content: str, content_type: str, experiment_id: str, iteration: int = 1
    ) -> str:
        """Save content to a file and return the file path."""
        if content_type == "prompt":
            content_dir = self.content_dir / "prompts"
            filename = f"{experiment_id}_prompt_iter{iteration}.txt"
        elif content_type == "response":
            content_dir = self.content_dir / "responses"
            filename = f"{experiment_id}_response_iter{iteration}.txt"
        else:
            raise ValueError(f"Unknown content type: {content_type}")

        file_path = content_dir / filename

        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # Return relative path from experiments directory
        return str(file_path.relative_to(self.experiments_dir))

    def append_experiment_result(self, result: Dict[str, Any]):
        """Append an experiment result to the current CSV file."""
        file_path = self.get_current_results_file()

        # Convert result to CSV row
        row = [
            result.get("experiment_id", ""),
            result.get("timestamp", datetime.now().isoformat()),
            result.get("put_id", ""),
            result.get("prompt_id", ""),
            result.get("prompt_version", "1.0"),
            result.get("model_name", ""),
            result.get("model_provider", ""),
            result.get("model_architecture", ""),
            result.get("model_size", ""),
            result.get("code_generation_success", False),
            result.get("code_iterations_needed", 0),
            result.get("test_generation_success", False),
            result.get("test_iterations_needed", 0),
            result.get("test_coverage", 0.0),
            result.get("test_count", 0),
            result.get("test_execution_time", 0.0),
            result.get("system_prompt_file", ""),
            result.get("user_prompt_file", ""),
            result.get("llm_response_file", ""),
            result.get("temperature", 0.0),
            result.get("max_tokens", 0),
            result.get("timeout", 0),
            result.get("total_tokens_used", 0),
            result.get("cost_estimate", 0.0),
            json.dumps(result.get("errors", [])),
            json.dumps(result.get("warnings", [])),
        ]

        with open(file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def read_content_from_file(self, file_path: str) -> str:
        """Read content from a file path relative to experiments directory."""
        full_path = self.experiments_dir / file_path
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def read_experiment_results(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """Read and filter results from CSV files."""
        # Read all CSV files in results directory
        all_results = []

        for csv_file in self.results_dir.glob("experiments_*.csv"):
            try:
                df = pd.read_csv(csv_file)
                all_results.append(df)
            except Exception as e:
                print(f"Warning: Could not read {csv_file}: {e}")

        if not all_results:
            return pd.DataFrame()

        # Combine all results
        combined_df = pd.concat(all_results, ignore_index=True)

        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if key in combined_df.columns:
                    if isinstance(value, (list, tuple)):
                        combined_df = combined_df[combined_df[key].isin(value)]
                    else:
                        combined_df = combined_df[combined_df[key] == value]

        return combined_df

    def get_experiment_with_content(
        self, experiment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a single experiment with its content loaded from files."""
        df = self.read_experiment_results({"experiment_id": experiment_id})
        if df.empty:
            return None

        experiment = df.iloc[0].to_dict()

        # Load content from files
        if experiment.get("system_prompt_file") and pd.notna(
            experiment["system_prompt_file"]
        ):
            experiment["system_prompt"] = self.read_content_from_file(
                experiment["system_prompt_file"]
            )
        if experiment.get("user_prompt_file") and pd.notna(
            experiment["user_prompt_file"]
        ):
            experiment["user_prompt"] = self.read_content_from_file(
                experiment["user_prompt_file"]
            )
        if experiment.get("llm_response_file") and pd.notna(
            experiment["llm_response_file"]
        ):
            experiment["llm_response"] = self.read_content_from_file(
                experiment["llm_response_file"]
            )

        return experiment

    def get_statistics(self, group_by: List[str]) -> Dict[str, Any]:
        """Get aggregated statistics for analysis."""
        df = self.read_experiment_results()

        if df.empty:
            return {}

        # Basic statistics
        stats = {
            "total_experiments": len(df),
            "successful_code_generation": df["code_generation_success"].sum(),
            "successful_test_generation": df["test_generation_success"].sum(),
            "avg_code_iterations": df["code_iterations_needed"].mean(),
            "avg_test_iterations": df["test_iterations_needed"].mean(),
            "avg_test_coverage": df["test_coverage"].mean(),
        }

        # Grouped statistics
        if group_by:
            for group in group_by:
                if group in df.columns:
                    grouped_stats = (
                        df.groupby(group)
                        .agg(
                            {
                                "code_generation_success": ["count", "sum", "mean"],
                                "test_generation_success": ["count", "sum", "mean"],
                                "code_iterations_needed": "mean",
                                "test_iterations_needed": "mean",
                                "test_coverage": "mean",
                            }
                        )
                        .round(3)
                    )
                    stats[f"grouped_by_{group}"] = grouped_stats.to_dict()

        return stats

    def get_prompt_techniques(self) -> pd.DataFrame:
        """Read prompt techniques from CSV."""
        file_path = self.prompts_dir / "prompt_techniques.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        return pd.DataFrame()

    def get_model_registry(self) -> pd.DataFrame:
        """Read model registry from CSV."""
        file_path = self.models_dir / "model_registry.csv"
        if file_path.exists():
            return pd.read_csv(file_path)
        return pd.DataFrame()

    def add_prompt_technique(self, technique: Dict[str, Any]):
        """Add a new prompt technique to the CSV file."""
        file_path = self.prompts_dir / "prompt_techniques.csv"

        # Read existing data
        df = pd.read_csv(file_path)

        # Check if prompt_id already exists
        if technique["prompt_id"] in df["prompt_id"].values:
            print(f"Warning: Prompt technique {technique['prompt_id']} already exists")
            return

        # Add new technique
        new_row = pd.DataFrame([technique])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save back to CSV
        df.to_csv(file_path, index=False)

    def add_model_info(self, model_info: Dict[str, Any]):
        """Add new model information to the CSV file."""
        file_path = self.models_dir / "model_registry.csv"

        # Read existing data
        df = pd.read_csv(file_path)

        # Check if model already exists
        if model_info["model_name"] in df["model_name"].values:
            print(f"Warning: Model {model_info['model_name']} already exists")
            return

        # Add new model
        new_row = pd.DataFrame([model_info])
        df = pd.concat([df, new_row], ignore_index=True)

        # Save back to CSV
        df.to_csv(file_path, index=False)
