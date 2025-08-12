#!/usr/bin/env python3
"""
Utility script to remove ALL experiment data completely.
Use with caution - this will delete all experiment results, content, and data.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.csv_manager import ExperimentCSVManager


def remove_all_experiments(experiments_dir: str = "experiments", dry_run: bool = True):
    """Remove all experiment data completely."""
    experiments_path = Path(experiments_dir)

    if not experiments_path.exists():
        print(f"❌ Experiments directory '{experiments_dir}' does not exist.")
        return

    print(f"🧹 Removing ALL experiments from: {experiments_path.absolute()}")

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print("   Use --execute to actually perform the deletion")

    # List what would be removed
    csv_manager = ExperimentCSVManager(experiments_dir)
    try:
        df = csv_manager.read_experiment_results()
        if not df.empty:
            print(f"\n📊 Found {len(df)} experiments to remove:")
            for _, row in df.iterrows():
                experiment_id = row.get("experiment_id", "N/A")
                timestamp = row.get("timestamp", "N/A")
                put_id = row.get("put_id", "N/A")
                print(f"   - {experiment_id} ({put_id}) at {timestamp}")
        else:
            print("\n📊 No experiments found in CSV")
    except Exception as e:
        print(f"⚠️  Could not read experiment CSV: {e}")

    # Check content directories
    content_dirs = ["prompts", "responses", "models", "analysis"]
    total_files = 0

    for content_dir in content_dirs:
        content_path = experiments_path / content_dir
        if content_path.exists():
            files = list(content_path.glob("*"))
            total_files += len(files)
            if files:
                print(f"\n📁 {content_dir}/ directory contains {len(files)} files")
                if not dry_run:
                    print(f"   Removing {content_dir}/ directory...")
                    shutil.rmtree(content_path)
                    print(f"   ✅ Removed {content_dir}/ directory")
                else:
                    print(f"   Would remove {content_dir}/ directory")

    # Remove results directory
    results_path = experiments_path / "results"
    if results_path.exists():
        csv_files = list(results_path.glob("*.csv"))
        total_files += len(csv_files)
        if csv_files:
            print(f"\n📊 results/ directory contains {len(csv_files)} CSV files")
            if not dry_run:
                print("   Removing results/ directory...")
                shutil.rmtree(results_path)
                print("   ✅ Removed results/ directory")
            else:
                print("   Would remove results/ directory")

    # Remove prompts and responses directories if they exist at root level
    for dir_name in ["prompts", "responses"]:
        dir_path = experiments_path / dir_name
        if dir_path.exists():
            files = list(dir_path.glob("*"))
            total_files += len(files)
            if files:
                print(f"\n📁 {dir_name}/ directory contains {len(files)} files")
                if not dry_run:
                    print(f"   Removing {dir_name}/ directory...")
                    shutil.rmtree(dir_path)
                    print(f"   ✅ Removed {dir_name}/ directory")
                else:
                    print(f"   Would remove {dir_name}/ directory")

    # Remove content subdirectories (prompts, responses)
    content_path = experiments_path / "content"
    if content_path.exists():
        for dir_name in ["prompts", "responses"]:
            content_dir_path = content_path / dir_name
            if content_dir_path.exists():
                files = list(content_dir_path.glob("*"))
                total_files += len(files)
                if files:
                    print(
                        f"\n📁 content/{dir_name}/ directory contains {len(files)} files"
                    )
                    if not dry_run:
                        print(f"   Removing content/{dir_name}/ directory...")
                        shutil.rmtree(content_dir_path)
                        print(f"   ✅ Removed content/{dir_name}/ directory")
                    else:
                        print(f"   Would remove content/{dir_name}/ directory")

    print(f"\n📈 Summary:")
    print(f"   Total files/directories found: {total_files}")

    if dry_run:
        print("\n🔍 This was a dry run. No files were actually deleted.")
        print("   To actually remove all experiments, run with --execute")
    else:
        print("\n✅ All experiment data has been removed!")
        print("   The experiments directory structure remains but is now empty.")


def main():
    parser = argparse.ArgumentParser(
        description="Remove ALL experiment data completely. Use with extreme caution!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  WARNING: This will permanently delete ALL experiment data!
   - All CSV results files
   - All prompt and response files
   - All model outputs
   - All analysis files
   
   This action cannot be undone!
        """,
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform the deletion (default is dry-run)",
    )

    parser.add_argument(
        "--experiments-dir",
        default="experiments",
        help="Path to experiments directory (default: experiments)",
    )

    args = parser.parse_args()

    # Confirm before executing
    if args.execute:
        print("🚨 WARNING: You are about to delete ALL experiment data!")
        print("   This action cannot be undone!")
        print()

        response = input("Are you absolutely sure? Type 'YES' to confirm: ")
        if response != "YES":
            print("❌ Operation cancelled.")
            return

        print()

    try:
        remove_all_experiments(args.experiments_dir, not args.execute)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
