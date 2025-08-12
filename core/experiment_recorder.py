"""
Experiment Recorder for tracking and saving experimental results.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from .csv_manager import ExperimentCSVManager


class ExperimentRecorder:
    """Records experiment progress and saves final results to CSV."""

    def __init__(self, csv_manager: ExperimentCSVManager):
        self.csv_manager = csv_manager
        self.active_experiments: Dict[str, Dict[str, Any]] = {}

    def start_experiment(
        self, put_id: str, prompt_id: str, model_config: Dict[str, Any]
    ) -> str:
        """Start recording an experiment and return experiment_id."""
        experiment_id = str(uuid.uuid4())

        # Initialize experiment record
        experiment = {
            "experiment_id": experiment_id,
            "put_id": put_id,
            "prompt_id": prompt_id,
            "model_name": model_config.get("llm_model", "unknown"),
            "model_provider": model_config.get("llm_provider", "unknown"),
            "model_architecture": self._estimate_model_architecture(
                model_config.get("llm_model", "")
            ),
            "model_size": self._estimate_model_size(model_config.get("llm_model", "")),
            "temperature": model_config.get("llm_temperature", 0.1),
            "max_tokens": model_config.get("llm_max_tokens", 2000),
            "timeout": model_config.get("llm_timeout", 30),
            "code_generation_history": [],
            "test_generation_history": [],
            "errors": [],
            "warnings": [],
            "start_time": datetime.now(),
        }

        self.active_experiments[experiment_id] = experiment
        return experiment_id

    def record_code_generation(
        self,
        experiment_id: str,
        iteration: int,
        success: bool,
        code: str,
        response: str,
    ):
        """Record a code generation attempt."""
        if experiment_id not in self.active_experiments:
            print(f"Warning: Experiment {experiment_id} not found")
            return

        experiment = self.active_experiments[experiment_id]

        # Record the attempt
        attempt = {
            "iteration": iteration,
            "success": success,
            "code": code,
            "response": response,
            "timestamp": datetime.now(),
        }

        experiment["code_generation_history"].append(attempt)

        # Update final success status
        if success:
            experiment["code_generation_success"] = True
            experiment["code_iterations_needed"] = iteration

    def record_test_generation(
        self,
        experiment_id: str,
        iteration: int,
        success: bool,
        tests: str,
        coverage: float,
    ):
        """Record a test generation attempt."""
        if experiment_id not in self.active_experiments:
            print(f"Warning: Experiment {experiment_id} not found")
            return

        experiment = self.active_experiments[experiment_id]

        # Record the attempt
        attempt = {
            "iteration": iteration,
            "success": success,
            "tests": tests,
            "coverage": coverage,
            "timestamp": datetime.now(),
        }

        experiment["test_generation_history"].append(attempt)

        # Update final success status
        if success:
            experiment["test_generation_success"] = True
            experiment["test_iterations_needed"] = iteration
            experiment["test_coverage"] = coverage

    def add_error(self, experiment_id: str, error: str):
        """Add an error to the experiment record."""
        if experiment_id in self.active_experiments:
            self.active_experiments[experiment_id]["errors"].append(error)

    def add_warning(self, experiment_id: str, warning: str):
        """Add a warning to the experiment record."""
        if experiment_id in self.active_experiments:
            self.active_experiments[experiment_id]["warnings"].append(warning)

    def finalize_experiment(self, experiment_id: str, final_stats: Dict[str, Any]):
        """Complete the experiment record and save to CSV."""
        if experiment_id not in self.active_experiments:
            print(f"Warning: Experiment {experiment_id} not found")
            return

        experiment = self.active_experiments[experiment_id]

        # Set default values if not already set
        if "code_generation_success" not in experiment:
            experiment["code_generation_success"] = False
            experiment["code_iterations_needed"] = len(
                experiment["code_generation_history"]
            )

        if "test_generation_success" not in experiment:
            experiment["test_generation_success"] = False
            experiment["test_iterations_needed"] = len(
                experiment["test_generation_history"]
            )

        # Update with final stats
        experiment.update(final_stats)

        # Add completion timestamp
        experiment["timestamp"] = datetime.now().isoformat()

        # Save content to files and get file paths
        system_prompt_file = ""
        user_prompt_file = ""
        llm_response_file = ""

        if final_stats.get("system_prompt"):
            system_prompt_file = self.csv_manager.save_content_to_file(
                final_stats["system_prompt"], "prompt", experiment_id, 1
            )

        if final_stats.get("user_prompt"):
            user_prompt_file = self.csv_manager.save_content_to_file(
                final_stats["user_prompt"], "prompt", experiment_id, 1
            )

        if final_stats.get("llm_response"):
            llm_response_file = self.csv_manager.save_content_to_file(
                final_stats["llm_response"], "response", experiment_id, 1
            )

        # Prepare result for CSV
        result = {
            "experiment_id": experiment["experiment_id"],
            "timestamp": experiment["timestamp"],
            "put_id": experiment["put_id"],
            "prompt_id": experiment["prompt_id"],
            "prompt_version": "1.0",  # Default version
            "model_name": experiment["model_name"],
            "model_provider": experiment["model_provider"],
            "model_architecture": experiment["model_architecture"],
            "model_size": experiment["model_size"],
            "code_generation_success": experiment["code_generation_success"],
            "code_iterations_needed": experiment["code_iterations_needed"],
            "test_generation_success": experiment["test_generation_success"],
            "test_iterations_needed": experiment["test_iterations_needed"],
            "test_coverage": experiment.get("test_coverage", 0.0),
            "test_count": experiment.get("test_count", 0),
            "test_execution_time": experiment.get("test_execution_time", 0.0),
            "system_prompt_file": system_prompt_file,
            "user_prompt_file": user_prompt_file,
            "llm_response_file": llm_response_file,
            "temperature": experiment["temperature"],
            "max_tokens": experiment["max_tokens"],
            "timeout": experiment["timeout"],
            "total_tokens_used": experiment.get("total_tokens_used", 0),
            "cost_estimate": experiment.get("cost_estimate", 0.0),
            "errors": experiment["errors"],
            "warnings": experiment["warnings"],
        }

        # Save to CSV
        self.csv_manager.append_experiment_result(result)

        # Remove from active experiments
        del self.active_experiments[experiment_id]

        print(f"✅ Experiment {experiment_id} completed and saved to CSV")
        print(
            f"   Content files: {system_prompt_file}, {user_prompt_file}, {llm_response_file}"
        )

    def _estimate_model_architecture(self, model_name: str) -> str:
        """Estimate model architecture based on model name."""
        model_name_lower = model_name.lower()

        if any(
            name in model_name_lower for name in ["gpt", "claude", "llama", "mistral"]
        ):
            return "transformer"
        elif "gemini" in model_name_lower:
            return "transformer"
        elif "palm" in model_name_lower:
            return "transformer"
        else:
            return "unknown"

    def _estimate_model_size(self, model_name: str) -> str:
        """Estimate model size based on model name."""
        model_name_lower = model_name.lower()

        # GPT models
        if "gpt-4" in model_name_lower:
            return "175b"  # Estimated
        elif "gpt-3.5" in model_name_lower:
            return "7b"  # Estimated

        # Claude models
        elif "claude-3-opus" in model_name_lower:
            return "200b"  # Estimated
        elif "claude-3-sonnet" in model_name_lower:
            return "70b"  # Estimated
        elif "claude-3-haiku" in model_name_lower:
            return "10b"  # Estimated

        # Llama models
        elif "llama-2-70b" in model_name_lower:
            return "70b"
        elif "llama-2-13b" in model_name_lower:
            return "13b"
        elif "llama-2-7b" in model_name_lower:
            return "7b"

        # Mistral models
        elif "mistral-7b" in model_name_lower:
            return "7b"
        elif "mixtral-8x7b" in model_name_lower:
            return "47b"  # 8x7b = 47b total

        else:
            return "unknown"

    def get_active_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get an active experiment by ID."""
        return self.active_experiments.get(experiment_id)

    def list_active_experiments(self) -> List[str]:
        """List all active experiment IDs."""
        return list(self.active_experiments.keys())
