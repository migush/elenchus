#!/usr/bin/env python3
"""
Utility script to clean up experiment results and associated files.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_manager import ExperimentCSVManager


class ExperimentCleanup:
    """Handles cleanup operations for experiment results and files."""

    def __init__(self, experiments_dir: str = "experiments"):
        self.experiments_dir = Path(experiments_dir)
        self.csv_manager = ExperimentCSVManager(experiments_dir)
        self.results_dir = self.experiments_dir / "results"
        self.content_dir = self.experiments_dir / "content"
        self.prompts_dir = self.content_dir / "prompts"
        self.responses_dir = self.content_dir / "responses"

    def list_experiments(self, limit: int = None, show_failed_only: bool = False):
        """List experiments with optional filtering."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            print("No experiment results found.")
            return

        # Apply filters
        if show_failed_only:
            df = df[
                (df["code_generation_success"] == False)
                | (df["test_generation_success"] == False)
            ]
            if df.empty:
                print("No failed experiments found.")
                return

        # Sort by timestamp (newest first)
        df = df.sort_values("timestamp", ascending=False)

        # Limit display if specified
        if limit:
            display_df = df.head(limit)
        else:
            display_df = df

        print(f"\nExperiment Results (showing {len(display_df)} of {len(df)}):")
        print("=" * 100)

        for _, row in display_df.iterrows():
            experiment_id = row.get("experiment_id", "N/A")
            timestamp = row.get("timestamp", "N/A")
            put_id = row.get("put_id", "N/A")
            model_name = row.get("model_name", "N/A")
            code_success = row.get("code_generation_success", False)
            test_success = row.get("test_generation_success", False)
            test_coverage = row.get("test_coverage", 0.0)

            status = "✅" if code_success and test_success else "❌"

            print(f"{status} ID: {experiment_id}")
            print(f"   Timestamp: {timestamp}")
            print(f"   PUT ID: {put_id}")
            print(f"   Model: {model_name}")
            print(f"   Code Success: {code_success}")
            print(f"   Test Success: {test_success}")
            print(f"   Test Coverage: {test_coverage}%")
            print("-" * 50)

    def remove_failed_experiments(
        self, dry_run: bool = True, min_coverage: float = 0.0
    ):
        """Remove experiments that failed code generation, test generation, or have low coverage."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            print("No experiment results found.")
            return

        # Identify failed experiments
        failed_mask = (
            (df["code_generation_success"] == False)
            | (df["test_generation_success"] == False)
            | (df["test_coverage"] < min_coverage)
        )

        failed_experiments = df[failed_mask]

        if failed_experiments.empty:
            print("No failed experiments found to remove.")
            return

        print(f"Found {len(failed_experiments)} failed experiments:")
        for _, row in failed_experiments.iterrows():
            experiment_id = row.get("experiment_id", "N/A")
            put_id = row.get("put_id", "N/A")
            code_success = row.get("code_generation_success", False)
            test_success = row.get("test_generation_success", False)
            test_coverage = row.get("test_coverage", 0.0)

            print(f"  - {experiment_id} (PUT: {put_id})")
            print(
                f"    Code Success: {code_success}, Test Success: {test_success}, Coverage: {test_coverage}%"
            )

        if dry_run:
            print(
                f"\n[DRY RUN] Would remove {len(failed_experiments)} failed experiments"
            )
            print("Run with --execute to actually remove them")
            return

        # Actually remove the experiments
        print(f"\nRemoving {len(failed_experiments)} failed experiments...")

        # Remove from CSV files
        for csv_file in self.results_dir.glob("experiments_*.csv"):
            try:
                df_csv = pd.read_csv(csv_file)
                original_count = len(df_csv)

                # Remove failed experiments
                df_csv = df_csv[
                    ~df_csv["experiment_id"].isin(failed_experiments["experiment_id"])
                ]

                if len(df_csv) < original_count:
                    # Create backup
                    backup_file = csv_file.with_suffix(".csv.backup")
                    shutil.copy2(csv_file, backup_file)
                    print(f"  Created backup: {backup_file.name}")

                    # Write updated CSV
                    df_csv.to_csv(csv_file, index=False)
                    removed_count = original_count - len(df_csv)
                    print(f"  Removed {removed_count} experiments from {csv_file.name}")

            except Exception as e:
                print(f"  Error processing {csv_file}: {e}")

        # Remove associated content files
        self._remove_content_files(failed_experiments["experiment_id"].tolist())

        print(f"✅ Successfully removed {len(failed_experiments)} failed experiments")

    def remove_orphaned_files(self, dry_run: bool = True):
        """Remove content files that don't have corresponding CSV entries."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            print("No experiment results found.")
            return

        # Get all experiment IDs from CSV
        csv_experiment_ids = set(df["experiment_id"].dropna())

        # Find orphaned prompt files
        orphaned_prompts = []
        for prompt_file in self.prompts_dir.glob("*_prompt_iter*.txt"):
            experiment_id = prompt_file.stem.split("_prompt_iter")[0]
            if experiment_id not in csv_experiment_ids:
                orphaned_prompts.append(prompt_file)

        # Find orphaned response files
        orphaned_responses = []
        for response_file in self.responses_dir.glob("*_response_iter*.txt"):
            experiment_id = response_file.stem.split("_response_iter")[0]
            if experiment_id not in csv_experiment_ids:
                orphaned_responses.append(response_file)

        total_orphaned = len(orphaned_prompts) + len(orphaned_responses)

        if total_orphaned == 0:
            print("No orphaned files found.")
            return

        print(f"Found {total_orphaned} orphaned files:")
        print(f"  - {len(orphaned_prompts)} orphaned prompt files")
        print(f"  - {len(orphaned_responses)} orphaned response files")

        if dry_run:
            print(f"\n[DRY RUN] Would remove {total_orphaned} orphaned files")
            print("Run with --execute to actually remove them")
            return

        # Actually remove the files
        print(f"\nRemoving {total_orphaned} orphaned files...")

        for file_path in orphaned_prompts + orphaned_responses:
            try:
                file_path.unlink()
                print(f"  Removed: {file_path.name}")
            except Exception as e:
                print(f"  Error removing {file_path.name}: {e}")

        print(f"✅ Successfully removed {total_orphaned} orphaned files")

    def archive_old_experiments(self, days_old: int = 30, dry_run: bool = True):
        """Archive experiments older than specified days."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            print("No experiment results found.")
            return

        # Convert timestamp to datetime and filter
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        cutoff_date = datetime.now() - timedelta(days=days_old)

        old_experiments = df[df["timestamp"] < cutoff_date]

        if old_experiments.empty:
            print(f"No experiments older than {days_old} days found.")
            return

        print(f"Found {len(old_experiments)} experiments older than {days_old} days:")
        for _, row in old_experiments.iterrows():
            experiment_id = row.get("experiment_id", "N/A")
            timestamp = row.get("timestamp", "N/A")
            put_id = row.get("put_id", "N/A")
            print(f"  - {experiment_id} (PUT: {put_id}) - {timestamp}")

        if dry_run:
            print(f"\n[DRY RUN] Would archive {len(old_experiments)} old experiments")
            print("Run with --execute to actually archive them")
            return

        # Create archive directory
        archive_dir = (
            self.experiments_dir
            / "archive"
            / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        archive_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nArchiving {len(old_experiments)} old experiments to {archive_dir}...")

        # Archive CSV entries
        for csv_file in self.results_dir.glob("experiments_*.csv"):
            try:
                df_csv = pd.read_csv(csv_file)
                original_count = len(df_csv)

                # Move old experiments to archive
                old_in_csv = df_csv[
                    df_csv["experiment_id"].isin(old_experiments["experiment_id"])
                ]
                if not old_in_csv.empty:
                    # Save archived data
                    archive_csv = archive_dir / f"archived_{csv_file.name}"
                    old_in_csv.to_csv(archive_csv, index=False)

                    # Remove from original CSV
                    df_csv = df_csv[
                        ~df_csv["experiment_id"].isin(old_experiments["experiment_id"])
                    ]
                    df_csv.to_csv(csv_file, index=False)

                    removed_count = original_count - len(df_csv)
                    print(
                        f"  Archived {removed_count} experiments from {csv_file.name}"
                    )

            except Exception as e:
                print(f"  Error processing {csv_file}: {e}")

        # Archive content files
        self._archive_content_files(
            old_experiments["experiment_id"].tolist(), archive_dir
        )

        print(
            f"✅ Successfully archived {len(old_experiments)} old experiments to {archive_dir}"
        )

    def cleanup_empty_csv_files(self, dry_run: bool = True):
        """Remove CSV files that are empty or only contain headers."""
        empty_files = []

        for csv_file in self.results_dir.glob("experiments_*.csv"):
            try:
                df = pd.read_csv(csv_file)
                if len(df) == 0:
                    empty_files.append(csv_file)
            except Exception as e:
                print(f"  Error reading {csv_file}: {e}")

        if not empty_files:
            print("No empty CSV files found.")
            return

        print(f"Found {len(empty_files)} empty CSV files:")
        for file_path in empty_files:
            print(f"  - {file_path.name}")

        if dry_run:
            print(f"\n[DRY RUN] Would remove {len(empty_files)} empty CSV files")
            print("Run with --execute to actually remove them")
            return

        # Actually remove the files
        print(f"\nRemoving {len(empty_files)} empty CSV files...")

        for file_path in empty_files:
            try:
                file_path.unlink()
                print(f"  Removed: {file_path.name}")
            except Exception as e:
                print(f"  Error removing {file_path.name}: {e}")

        print(f"✅ Successfully removed {len(empty_files)} empty CSV files")

    def _remove_content_files(self, experiment_ids: list):
        """Remove content files for specified experiment IDs."""
        for experiment_id in experiment_ids:
            # Remove prompt files
            for prompt_file in self.prompts_dir.glob(
                f"{experiment_id}_prompt_iter*.txt"
            ):
                try:
                    prompt_file.unlink()
                    print(f"    Removed prompt file: {prompt_file.name}")
                except Exception as e:
                    print(f"    Error removing prompt file {prompt_file.name}: {e}")

            # Remove response files
            for response_file in self.responses_dir.glob(
                f"{experiment_id}_response_iter*.txt"
            ):
                try:
                    response_file.unlink()
                    print(f"    Removed response file: {response_file.name}")
                except Exception as e:
                    print(f"    Error removing response file {response_file.name}: {e}")

    def _archive_content_files(self, experiment_ids: list, archive_dir: Path):
        """Archive content files for specified experiment IDs."""
        content_archive_dir = archive_dir / "content"
        content_archive_dir.mkdir(parents=True, exist_ok=True)

        (content_archive_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (content_archive_dir / "responses").mkdir(parents=True, exist_ok=True)

        for experiment_id in experiment_ids:
            # Archive prompt files
            for prompt_file in self.prompts_dir.glob(
                f"{experiment_id}_prompt_iter*.txt"
            ):
                try:
                    shutil.move(
                        str(prompt_file),
                        str(content_archive_dir / "prompts" / prompt_file.name),
                    )
                    print(f"    Archived prompt file: {prompt_file.name}")
                except Exception as e:
                    print(f"    Error archiving prompt file {prompt_file.name}: {e}")

            # Archive response files
            for response_file in self.responses_dir.glob(
                f"{experiment_id}_response_iter*.txt"
            ):
                try:
                    shutil.move(
                        str(response_file),
                        str(content_archive_dir / "responses" / response_file.name),
                    )
                    print(f"    Archived response file: {response_file.name}")
                except Exception as e:
                    print(
                        f"    Error archiving response file {response_file.name}: {e}"
                    )

    def get_storage_stats(self):
        """Display storage statistics for experiments."""
        df = self.csv_manager.read_experiment_results()

        if df.empty:
            print("No experiment results found.")
            return

        # Count files
        prompt_files = list(self.prompts_dir.glob("*.txt"))
        response_files = list(self.responses_dir.glob("*.txt"))
        csv_files = list(self.results_dir.glob("*.csv"))

        # Calculate file sizes
        total_size = 0
        for file_path in prompt_files + response_files + csv_files:
            if file_path.exists():
                total_size += file_path.stat().st_size

        # Statistics
        print("\n📊 Experiment Storage Statistics")
        print("=" * 50)
        print(f"Total Experiments: {len(df)}")
        print(
            f"Successful Experiments: {len(df[(df['code_generation_success'] == True) & (df['test_generation_success'] == True)])}"
        )
        print(
            f"Failed Experiments: {len(df[(df['code_generation_success'] == False) | (df['test_generation_success'] == False)])}"
        )
        print(f"CSV Files: {len(csv_files)}")
        print(f"Prompt Files: {len(prompt_files)}")
        print(f"Response Files: {len(response_files)}")
        print(f"Total Storage: {total_size / 1024:.2f} KB")

        # Check for orphaned files
        csv_experiment_ids = set(df["experiment_id"].dropna())
        orphaned_prompts = [
            f
            for f in prompt_files
            if f.stem.split("_prompt_iter")[0] not in csv_experiment_ids
        ]
        orphaned_responses = [
            f
            for f in response_files
            if f.stem.split("_response_iter")[0] not in csv_experiment_ids
        ]

        if orphaned_prompts or orphaned_responses:
            print(
                f"⚠️  Orphaned Files: {len(orphaned_prompts)} prompts, {len(orphaned_responses)} responses"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Clean up experiment results and associated files"
    )
    parser.add_argument("--list", "-l", action="store_true", help="List experiments")
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="Show only failed experiments when listing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of experiments to show (default: 10)",
    )

    # Cleanup operations
    parser.add_argument(
        "--remove-failed", action="store_true", help="Remove failed experiments"
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=0.0,
        help="Minimum test coverage threshold for failed experiments (default: 0.0)",
    )
    parser.add_argument(
        "--remove-orphaned", action="store_true", help="Remove orphaned content files"
    )
    parser.add_argument(
        "--archive-old",
        type=int,
        metavar="DAYS",
        help="Archive experiments older than specified days",
    )
    parser.add_argument(
        "--cleanup-empty", action="store_true", help="Remove empty CSV files"
    )

    # Execution control
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the cleanup (default is dry-run)",
    )
    parser.add_argument("--stats", action="store_true", help="Show storage statistics")

    args = parser.parse_args()

    if not any(
        [
            args.list,
            args.remove_failed,
            args.remove_orphaned,
            args.archive_old,
            args.cleanup_empty,
            args.stats,
        ]
    ):
        parser.print_help()
        return

    try:
        cleanup = ExperimentCleanup()

        if args.stats:
            cleanup.get_storage_stats()

        if args.list:
            cleanup.list_experiments(args.limit, args.failed_only)

        if args.remove_failed:
            cleanup.remove_failed_experiments(not args.execute, args.min_coverage)

        if args.remove_orphaned:
            cleanup.remove_orphaned_files(not args.execute)

        if args.archive_old:
            cleanup.archive_old_experiments(args.archive_old, not args.execute)

        if args.cleanup_empty:
            cleanup.cleanup_empty_csv_files(not args.execute)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
