"""
Experiment Analyzer for statistical analysis and reporting.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from .csv_manager import ExperimentCSVManager


class ExperimentAnalyzer:
    """Analyzes experimental results and generates reports."""

    def __init__(self, csv_manager: ExperimentCSVManager):
        self.csv_manager = csv_manager

    def analyze_prompt_techniques(self) -> Dict[str, Any]:
        """Analyze statistical significance of prompt techniques."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            return {"error": "No experimental data found"}

        # Group by prompt_id
        prompt_analysis = (
            df.groupby("prompt_id")
            .agg(
                {
                    "code_generation_success": ["count", "sum", "mean"],
                    "test_generation_success": ["count", "sum", "mean"],
                    "code_iterations_needed": ["mean", "std"],
                    "test_iterations_needed": ["mean", "std"],
                    "test_coverage": ["mean", "std"],
                }
            )
            .round(3)
        )

        # Calculate success rates
        prompt_analysis["code_success_rate"] = (
            prompt_analysis[("code_generation_success", "sum")]
            / prompt_analysis[("code_generation_success", "count")]
        ).round(3)

        prompt_analysis["test_success_rate"] = (
            prompt_analysis[("test_generation_success", "sum")]
            / prompt_analysis[("test_generation_success", "count")]
        ).round(3)

        # Statistical significance test (chi-square for success rates)
        if len(prompt_analysis) > 1:
            from scipy.stats import chi2_contingency

            # Create contingency table for code generation success
            code_contingency = (
                df.groupby("prompt_id")["code_generation_success"]
                .value_counts()
                .unstack(fill_value=0)
            )
            if code_contingency.shape[1] == 2:  # Both True and False present
                try:
                    chi2_code, p_value_code, _, _ = chi2_contingency(code_contingency)
                    code_significance = {
                        "chi2": round(chi2_code, 3),
                        "p_value": round(p_value_code, 6),
                        "significant": p_value_code < 0.05,
                    }
                except:
                    code_significance = {"error": "Could not calculate significance"}
            else:
                code_significance = {"error": "Insufficient data for significance test"}

            # Create contingency table for test generation success
            test_contingency = (
                df.groupby("prompt_id")["test_generation_success"]
                .value_counts()
                .unstack(fill_value=0)
            )
            if test_contingency.shape[1] == 2:  # Both True and False present
                try:
                    chi2_test, p_value_test, _, _ = chi2_contingency(test_contingency)
                    test_significance = {
                        "chi2": round(chi2_test, 3),
                        "p_value": round(p_value_test, 6),
                        "significant": p_value_test < 0.05,
                    }
                except:
                    test_significance = {"error": "Could not calculate significance"}
            else:
                test_significance = {"error": "Insufficient data for significance test"}
        else:
            code_significance = {
                "error": "Need at least 2 prompt techniques for comparison"
            }
            test_significance = {
                "error": "Need at least 2 prompt techniques for comparison"
            }

        return {
            "prompt_analysis": prompt_analysis.to_dict(),
            "code_generation_significance": code_significance,
            "test_generation_significance": test_significance,
            "summary": {
                "total_prompts": len(prompt_analysis),
                "best_code_success_rate": prompt_analysis["code_success_rate"].max(),
                "best_test_success_rate": prompt_analysis["test_success_rate"].max(),
                "best_code_prompt": prompt_analysis["code_success_rate"].idxmax(),
                "best_test_prompt": prompt_analysis["test_success_rate"].idxmax(),
            },
        }

    def analyze_model_impact(self) -> Dict[str, Any]:
        """Analyze impact of model size and architecture."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            return {"error": "No experimental data found"}

        # Model size analysis
        size_analysis = (
            df.groupby("model_size")
            .agg(
                {
                    "code_generation_success": ["count", "sum", "mean"],
                    "test_generation_success": ["count", "sum", "mean"],
                    "code_iterations_needed": ["mean", "std"],
                    "test_iterations_needed": ["mean", "std"],
                    "test_coverage": ["mean", "std"],
                }
            )
            .round(3)
        )

        # Model architecture analysis
        arch_analysis = (
            df.groupby("model_architecture")
            .agg(
                {
                    "code_generation_success": ["count", "sum", "mean"],
                    "test_generation_success": ["count", "sum", "mean"],
                    "code_iterations_needed": ["mean", "std"],
                    "test_iterations_needed": ["mean", "std"],
                    "test_coverage": ["mean", "std"],
                }
            )
            .round(3)
        )

        # Provider analysis
        provider_analysis = (
            df.groupby("model_provider")
            .agg(
                {
                    "code_generation_success": ["count", "sum", "mean"],
                    "test_generation_success": ["count", "sum", "mean"],
                    "code_iterations_needed": ["mean", "std"],
                    "test_iterations_needed": ["mean", "std"],
                    "test_coverage": ["mean", "std"],
                }
            )
            .round(3)
        )

        # Statistical significance tests
        significance_tests = {}

        # Test model size impact
        if len(size_analysis) > 1:
            significance_tests["model_size"] = self._test_categorical_impact(
                df, "model_size"
            )

        # Test architecture impact
        if len(arch_analysis) > 1:
            significance_tests["architecture"] = self._test_categorical_impact(
                df, "model_architecture"
            )

        # Test provider impact
        if len(provider_analysis) > 1:
            significance_tests["provider"] = self._test_categorical_impact(
                df, "model_provider"
            )

        return {
            "size_analysis": size_analysis.to_dict(),
            "architecture_analysis": arch_analysis.to_dict(),
            "provider_analysis": provider_analysis.to_dict(),
            "significance_tests": significance_tests,
            "summary": {
                "total_models": len(df["model_name"].unique()),
                "total_sizes": len(size_analysis),
                "total_architectures": len(arch_analysis),
                "total_providers": len(provider_analysis),
                "best_performing_size": (
                    size_analysis[("code_generation_success", "mean")].idxmax()
                    if not size_analysis.empty
                    else "N/A"
                ),
                "best_performing_architecture": (
                    arch_analysis[("code_generation_success", "mean")].idxmax()
                    if not arch_analysis.empty
                    else "N/A"
                ),
            },
        }

    def _test_categorical_impact(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Test the impact of a categorical variable on success rates."""
        try:
            from scipy.stats import chi2_contingency

            # Test code generation success
            code_contingency = (
                df.groupby(column)["code_generation_success"]
                .value_counts()
                .unstack(fill_value=0)
            )
            if code_contingency.shape[1] == 2:  # Both True and False present
                chi2_code, p_value_code, _, _ = chi2_contingency(code_contingency)
                code_significance = {
                    "chi2": round(chi2_code, 3),
                    "p_value": round(p_value_code, 6),
                    "significant": p_value_code < 0.05,
                }
            else:
                code_significance = {"error": "Insufficient data"}

            # Test test generation success
            test_contingency = (
                df.groupby(column)["test_generation_success"]
                .value_counts()
                .unstack(fill_value=0)
            )
            if test_contingency.shape[1] == 2:  # Both True and False present
                chi2_test, p_value_test, _, _ = chi2_contingency(test_contingency)
                test_significance = {
                    "chi2": round(chi2_test, 3),
                    "p_value": round(p_value_test, 6),
                    "significant": p_value_test < 0.05,
                }
            else:
                test_significance = {"error": "Insufficient data"}

            return {
                "code_generation": code_significance,
                "test_generation": test_significance,
            }

        except Exception as e:
            return {
                "code_generation": {"error": str(e)},
                "test_generation": {"error": str(e)},
            }

    def generate_report(self, output_path: str = None):
        """Generate comprehensive analysis report."""
        if output_path is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = (
                self.csv_manager.analysis_dir / f"analysis_report_{timestamp}.csv"
            )

        # Get all analyses
        prompt_analysis = self.analyze_prompt_techniques()
        model_analysis = self.analyze_model_impact()

        # Create summary report
        report_data = []

        # Add prompt technique results
        if "prompt_analysis" in prompt_analysis:
            for prompt_id, metrics in prompt_analysis["prompt_analysis"].items():
                report_data.append(
                    {
                        "analysis_type": "prompt_technique",
                        "category": prompt_id,
                        "code_success_rate": metrics.get(
                            ("code_generation_success", "mean"), 0
                        ),
                        "test_success_rate": metrics.get(
                            ("test_generation_success", "mean"), 0
                        ),
                        "avg_code_iterations": metrics.get(
                            ("code_iterations_needed", "mean"), 0
                        ),
                        "avg_test_iterations": metrics.get(
                            ("test_iterations_needed", "mean"), 0
                        ),
                        "avg_test_coverage": metrics.get(("test_coverage", "mean"), 0),
                        "sample_size": metrics.get(
                            ("code_generation_success", "count"), 0
                        ),
                    }
                )

        # Add model size results
        if "size_analysis" in model_analysis:
            for size, metrics in model_analysis["size_analysis"].items():
                report_data.append(
                    {
                        "analysis_type": "model_size",
                        "category": size,
                        "code_success_rate": metrics.get(
                            ("code_generation_success", "mean"), 0
                        ),
                        "test_success_rate": metrics.get(
                            ("test_generation_success", "mean"), 0
                        ),
                        "avg_code_iterations": metrics.get(
                            ("code_iterations_needed", "mean"), 0
                        ),
                        "avg_test_iterations": metrics.get(
                            ("test_iterations_needed", "mean"), 0
                        ),
                        "avg_test_coverage": metrics.get(("test_coverage", "mean"), 0),
                        "sample_size": metrics.get(
                            ("code_generation_success", "count"), 0
                        ),
                    }
                )

        # Add architecture results
        if "architecture_analysis" in model_analysis:
            for arch, metrics in model_analysis["architecture_analysis"].items():
                report_data.append(
                    {
                        "analysis_type": "model_architecture",
                        "category": arch,
                        "code_success_rate": metrics.get(
                            ("code_generation_success", "mean"), 0
                        ),
                        "test_success_rate": metrics.get(
                            ("test_generation_success", "mean"), 0
                        ),
                        "avg_code_iterations": metrics.get(
                            ("code_iterations_needed", "mean"), 0
                        ),
                        "avg_test_iterations": metrics.get(
                            ("test_iterations_needed", "mean"), 0
                        ),
                        "avg_test_coverage": metrics.get(("test_coverage", "mean"), 0),
                        "sample_size": metrics.get(
                            ("code_generation_success", "count"), 0
                        ),
                    }
                )

        # Create DataFrame and save
        report_df = pd.DataFrame(report_data)
        report_df.to_csv(output_path, index=False)

        print(f"✅ Analysis report saved to: {output_path}")
        return str(output_path)

    def export_data(
        self,
        format: str = "csv",
        output_path: str = None,
        filters: Dict[str, Any] = None,
    ):
        """Export data for external analysis."""
        if output_path is None:
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.csv_manager.analysis_dir / f"export_{timestamp}.{format}"

        # Get filtered data
        df = self.csv_manager.read_experiment_results(filters)

        if df.empty:
            print("Warning: No data to export")
            return None

        if format.lower() == "csv":
            df.to_csv(output_path, index=False)
        elif format.lower() == "json":
            df.to_json(output_path, orient="records", indent=2)
        elif format.lower() == "excel":
            df.to_excel(output_path, index=False)
        else:
            print(f"Unsupported format: {format}")
            return None

        print(f"✅ Data exported to: {output_path}")
        return str(output_path)

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get overall summary statistics."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            return {"error": "No experimental data found"}

        # Overall statistics
        total_experiments = len(df)
        successful_code = df["code_generation_success"].sum()
        successful_tests = df["test_generation_success"].sum()

        # Success rates
        code_success_rate = (
            successful_code / total_experiments if total_experiments > 0 else 0
        )
        test_success_rate = (
            successful_tests / total_experiments if total_experiments > 0 else 0
        )

        # Average metrics
        avg_code_iterations = df["code_iterations_needed"].mean()
        avg_test_iterations = df["test_iterations_needed"].mean()
        avg_coverage = df["test_coverage"].mean()

        # Model diversity
        unique_models = df["model_name"].nunique()
        unique_prompts = df["prompt_id"].nunique()
        unique_puts = df["put_id"].nunique()

        return {
            "total_experiments": total_experiments,
            "successful_code_generation": successful_code,
            "successful_test_generation": successful_tests,
            "code_success_rate": round(code_success_rate, 3),
            "test_success_rate": round(test_success_rate, 3),
            "avg_code_iterations": round(avg_code_iterations, 2),
            "avg_test_iterations": round(avg_test_iterations, 2),
            "avg_test_coverage": round(avg_coverage, 3),
            "unique_models": unique_models,
            "unique_prompts": unique_prompts,
            "unique_puts": unique_puts,
            "date_range": {
                "earliest": df["timestamp"].min(),
                "latest": df["timestamp"].max(),
            },
        }

    def create_comparison_chart_data(
        self, group_by: str, metric: str
    ) -> Dict[str, Any]:
        """Create data for comparison charts."""
        df = self.csv_manager.read_experiment_results()

        if df.empty or group_by not in df.columns:
            return {"error": f"No data found or column '{group_by}' not found"}

        # Group by the specified column and calculate metrics
        grouped = (
            df.groupby(group_by)
            .agg(
                {
                    "code_generation_success": "mean",
                    "test_generation_success": "mean",
                    "code_iterations_needed": "mean",
                    "test_iterations_needed": "mean",
                    "test_coverage": "mean",
                }
            )
            .round(3)
        )

        # Add sample sizes
        sample_sizes = df.groupby(group_by).size()
        grouped["sample_size"] = sample_sizes

        return {
            "grouped_data": grouped.to_dict(),
            "categories": grouped.index.tolist(),
            "sample_sizes": sample_sizes.to_dict(),
            "metric": metric,
            "group_by": group_by,
        }
