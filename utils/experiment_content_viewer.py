#!/usr/bin/env python3
"""
Utility script to view experiment content from the new file-based storage system.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_manager import ExperimentCSVManager


def display_experiment_results(csv_manager: ExperimentCSVManager, limit: int = None):
    """Display experiment results in a table format."""
    df = csv_manager.read_experiment_results()

    if df.empty:
        print("No experiment results found.")
        return

    # Sort by timestamp (newest first)
    df = df.sort_values("timestamp", ascending=False)

    # Limit display if specified
    if limit:
        display_df = df.head(limit)
    else:
        display_df = df

    print(f"\nExperiment Results (showing {len(display_df)} of {len(df)}):")
    print("=" * 80)

    for _, row in display_df.iterrows():
        experiment_id = row.get("experiment_id", "N/A")
        timestamp = row.get("timestamp", "N/A")
        put_id = row.get("put_id", "N/A")
        model_name = row.get("model_name", "N/A")

        print(f"ID: {experiment_id}")
        print(f"Timestamp: {timestamp}")
        print(f"PUT ID: {put_id}")
        print(f"Model: {model_name}")
        print("-" * 40)


def view_experiment_content(csv_manager: ExperimentCSVManager, experiment_id: str):
    """View detailed content of a specific experiment."""
    experiment = csv_manager.get_experiment_with_content(experiment_id)

    if not experiment:
        print(f"Experiment {experiment_id} not found.")
        return

    print(f"\nExperiment Details: {experiment_id}")
    print("=" * 60)

    # Display basic info
    for key, value in experiment.items():
        if key not in ["system_prompt", "user_prompt", "llm_response"]:
            print(f"{key}: {value}")

    # Display prompts and responses
    if "system_prompt" in experiment:
        print(f"\nSystem Prompt:\n{experiment['system_prompt']}")

    if "user_prompt" in experiment:
        print(f"\nUser Prompt:\n{experiment['user_prompt']}")

    if "llm_response" in experiment:
        print(f"\nLLM Response:\n{experiment['llm_response']}")


def search_experiments(
    csv_manager: ExperimentCSVManager, query: str, field: str = "put_id"
):
    """Search experiments by a specific field."""
    df = csv_manager.read_experiment_results()

    if df.empty:
        print("No experiment results found.")
        return

    # Filter based on field type
    if field in ["syntax_ok", "passed", "ran"]:
        # Boolean fields
        if query.lower() in ["true", "1", "yes"]:
            filtered_df = df[df[field] == True]
        elif query.lower() in ["false", "0", "no"]:
            filtered_df = df[df[field] == False]
        else:
            print(f"Invalid boolean value for {field}. Use true/false, 1/0, or yes/no.")
            return
    else:
        # String fields - case-insensitive search
        filtered_df = df[
            df[field].astype(str).str.contains(query, case=False, na=False)
        ]

    if filtered_df.empty:
        print(f"No experiments found matching '{query}' in field '{field}'.")
        return

    print(f"\nSearch Results for '{query}' in '{field}' (found {len(filtered_df)}):")
    print("=" * 60)

    for _, row in filtered_df.iterrows():
        experiment_id = row.get("experiment_id", "N/A")
        timestamp = row.get("timestamp", "N/A")
        put_id = row.get("put_id", "N/A")
        model_name = row.get("model_name", "N/A")

        print(f"ID: {experiment_id}")
        print(f"Timestamp: {timestamp}")
        print(f"PUT ID: {put_id}")
        print(f"Model: {model_name}")
        print("-" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="View experiment content from file-based storage"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List recent experiments"
    )
    parser.add_argument(
        "--show", "-s", type=str, help="Show content of specific experiment by ID"
    )
    parser.add_argument("--search", type=str, help="Search experiments by query")
    parser.add_argument(
        "--field",
        type=str,
        default="put_id",
        help="Field to search in (default: put_id)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit number of experiments to show (default: 10)",
    )

    args = parser.parse_args()

    if not any([args.list, args.show, args.search]):
        parser.print_help()
        return

    try:
        csv_manager = ExperimentCSVManager()

        if args.list:
            display_experiment_results(csv_manager, args.limit)
        elif args.show:
            view_experiment_content(csv_manager, args.show)
        elif args.search:
            search_experiments(csv_manager, args.search, args.field)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
