"""
HumanEval dataset extraction functionality.
"""

import os
import tempfile
import requests
import gzip
import json
from typing import Optional, Iterable, Dict
import typer

from config.manager import config


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    with open(filename, "rb") as gzfp:
        with gzip.open(gzfp, "rt") as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def write_task_to_output_dir(task: dict, output_dir: str) -> None:
    """
    Writes a task to a file in the specified output directory.
    The file will contain the prompt followed by the canonical solution.
    """
    # Create the file path from task_id
    task_id = task["task_id"].replace("/", "/he_")
    file_path = os.path.join(output_dir, f"{task_id}.py")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write the content to the file
    with open(file_path, "w") as f:
        f.write(task["prompt"])
        f.write(task["canonical_solution"])


def extract_human_eval_to_dir(
    output_dir: str, human_eval_url: Optional[str] = None
) -> int:
    """
    Downloads the HumanEval dataset and extracts PUTs to the specified output directory.
    """
    # Use provided URL or get from config
    url = human_eval_url or config.get("human_eval_url")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create a temporary file for downloading
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as temp_file:
        temp_path = temp_file.name

        # Download the file to temporary location
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Save to temporary file
        for chunk in response.iter_content(chunk_size=8192):
            temp_file.write(chunk)

    # Process each problem and write to output directory
    problem_count = 0
    for problem in stream_jsonl(temp_path):
        write_task_to_output_dir(problem, output_dir)
        problem_count += 1

    # Clean up temporary file
    os.unlink(temp_path)

    return problem_count
