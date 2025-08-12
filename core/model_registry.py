"""
Model Registry for managing model information and metadata.
"""

from typing import Dict, Any, List, Optional
from .csv_manager import ExperimentCSVManager


class ModelRegistry:
    """Manages model information stored in CSV files."""

    def __init__(self, csv_manager: ExperimentCSVManager):
        self.csv_manager = csv_manager

    def register_model(self, model_info: Dict[str, Any]):
        """Register model information to CSV."""
        required_fields = ["model_name", "provider"]

        # Validate required fields
        for field in required_fields:
            if field not in model_info:
                raise ValueError(f"Missing required field: {field}")

        # Add timestamp if not provided
        if "created_at" not in model_info:
            from datetime import datetime

            model_info["created_at"] = datetime.now().isoformat()

        # Estimate missing fields if not provided
        if "architecture" not in model_info:
            model_info["architecture"] = self._estimate_model_architecture(
                model_info["model_name"]
            )

        if "estimated_size" not in model_info:
            model_info["estimated_size"] = self._estimate_model_size(
                model_info["model_name"]
            )

        if "capabilities" not in model_info:
            model_info["capabilities"] = "code-generation,testing"

        if "max_context_length" not in model_info:
            model_info["max_context_length"] = self._estimate_context_length(
                model_info["model_name"]
            )

        # Add to CSV
        self.csv_manager.add_model_info(model_info)
        print(f"✅ Model '{model_info['model_name']}' registered successfully")

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve model information from CSV."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            return None

        # Filter by model name
        model = df[df["model_name"] == model_name]

        if model.empty:
            return None

        # Convert to dictionary
        return model.iloc[0].to_dict()

    def list_models(
        self, provider: Optional[str] = None, architecture: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List available models from CSV with optional filtering."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            return []

        # Apply filters
        if provider:
            df = df[df["provider"] == provider]

        if architecture:
            df = df[df["architecture"] == architecture]

        # Convert to list of dictionaries
        return df.to_dict("records")

    def update_model_info(self, model_name: str, updates: Dict[str, Any]):
        """Update an existing model's information."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            print(f"Warning: No models found")
            return

        # Find the model
        mask = df["model_name"] == model_name
        if not mask.any():
            print(f"Warning: Model '{model_name}' not found")
            return

        # Update the model
        for key, value in updates.items():
            if key in df.columns:
                df.loc[mask, key] = value

        # Save back to CSV
        file_path = self.csv_manager.models_dir / "model_registry.csv"
        df.to_csv(file_path, index=False)

        print(f"✅ Model '{model_name}' updated successfully")

    def get_providers(self) -> List[str]:
        """Get list of available model providers."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            return []

        # Get unique providers
        providers = df["provider"].unique().tolist()
        return [p for p in providers if p]  # Filter out None/NaN

    def get_architectures(self) -> List[str]:
        """Get list of available model architectures."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            return []

        # Get unique architectures
        architectures = df["architecture"].unique().tolist()
        return [a for a in architectures if a]  # Filter out None/NaN

    def get_model_sizes(self) -> List[str]:
        """Get list of available model sizes."""
        df = self.csv_manager.get_model_registry()

        if df.empty:
            return []

        # Get unique sizes
        sizes = df["estimated_size"].unique().tolist()
        return [s for s in sizes if s]  # Filter out None/NaN

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
        elif "bert" in model_name_lower:
            return "transformer"
        elif "t5" in model_name_lower:
            return "transformer"
        else:
            return "unknown"

    def _estimate_model_size(self, model_name: str) -> str:
        """Estimate model size based on model name."""
        model_name_lower = model_name.lower()

        # GPT models
        if "gpt-4o" in model_name_lower:
            return "175b"  # Estimated
        elif "gpt-4" in model_name_lower:
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
        elif "claude-2" in model_name_lower:
            return "137b"  # Estimated

        # Llama models
        elif "llama-2-70b" in model_name_lower:
            return "70b"
        elif "llama-2-13b" in model_name_lower:
            return "13b"
        elif "llama-2-7b" in model_name_lower:
            return "7b"
        elif "llama-3-70b" in model_name_lower:
            return "70b"
        elif "llama-3-8b" in model_name_lower:
            return "8b"

        # Mistral models
        elif "mistral-7b" in model_name_lower:
            return "7b"
        elif "mixtral-8x7b" in model_name_lower:
            return "47b"  # 8x7b = 47b total
        elif "mistral-large" in model_name_lower:
            return "70b"  # Estimated

        # Code-specific models
        elif "codellama" in model_name_lower:
            if "70b" in model_name_lower:
                return "70b"
            elif "13b" in model_name_lower:
                return "13b"
            elif "7b" in model_name_lower:
                return "7b"
            else:
                return "7b"  # Default

        # Smaller models
        elif any(size in model_name_lower for size in ["1b", "1.5b", "2b", "3b"]):
            for size in ["1b", "1.5b", "2b", "3b"]:
                if size in model_name_lower:
                    return size

        else:
            return "unknown"

    def _estimate_context_length(self, model_name: str) -> int:
        """Estimate context length based on model name."""
        model_name_lower = model_name.lower()

        # GPT models
        if "gpt-4o" in model_name_lower:
            return 128000
        elif "gpt-4" in model_name_lower:
            return 8192
        elif "gpt-3.5" in model_name_lower:
            return 4096

        # Claude models
        elif "claude-3" in model_name_lower:
            return 200000
        elif "claude-2" in model_name_lower:
            return 100000

        # Llama models
        elif "llama-2" in model_name_lower or "llama-3" in model_name_lower:
            return 4096

        # Mistral models
        elif "mistral" in model_name_lower:
            return 32768

        # Code-specific models
        elif "codellama" in model_name_lower:
            return 16384

        else:
            return 4096  # Default conservative estimate

    def get_model_cost_estimate(
        self, model_name: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate cost for a model based on token usage."""
        model_info = self.get_model_info(model_name)

        if not model_info or "cost_per_1k_tokens" not in model_info:
            return 0.0

        try:
            cost_info = model_info["cost_per_1k_tokens"]
            if isinstance(cost_info, str):
                import json

                cost_info = json.loads(cost_info)

            input_cost = (input_tokens / 1000) * cost_info.get("input", 0.0)
            output_cost = (output_tokens / 1000) * cost_info.get("output", 0.0)

            return input_cost + output_cost
        except (json.JSONDecodeError, KeyError, TypeError):
            return 0.0

    def compare_models(self, model_names: List[str]) -> Dict[str, Any]:
        """Compare multiple models side by side."""
        comparison = {}

        for model_name in model_names:
            model_info = self.get_model_info(model_name)
            if model_info:
                comparison[model_name] = {
                    "provider": model_info.get("provider", "unknown"),
                    "architecture": model_info.get("architecture", "unknown"),
                    "estimated_size": model_info.get("estimated_size", "unknown"),
                    "max_context_length": model_info.get("max_context_length", 0),
                    "capabilities": model_info.get("capabilities", ""),
                    "cost_per_1k_tokens": model_info.get("cost_per_1k_tokens", "{}"),
                }

        return comparison
