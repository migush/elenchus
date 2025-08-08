"""
Core test generation module for Step 2. LLM Test Generation.

This module handles reading PUT files, building LLM prompts,
interacting with the LLM, and logging all interactions.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .llm import generate_text


def read_put_file(put_id: str, human_eval_dir: str = "HumanEval") -> str:
    """
    Read PUT file from HumanEval directory.

    Args:
        put_id: The PUT identifier (e.g., "he_0")
        human_eval_dir: Directory containing PUT files

    Returns:
        The full source code of the PUT as a string

    Raises:
        FileNotFoundError: If the PUT file doesn't exist
    """
    put_file_path = Path(human_eval_dir) / f"{put_id}.py"

    if not put_file_path.exists():
        raise FileNotFoundError(f"PUT file not found: {put_file_path}")

    with open(put_file_path, "r", encoding="utf-8") as f:
        return f.read()


def build_test_generation_prompt(put_source_code: str) -> str:
    """
    Build a prompt for LLM test generation.

    Args:
        put_source_code: The full source code of the PUT

    Returns:
        Formatted prompt string for the LLM
    """
    return f"""You are a Python testing expert. Generate a comprehensive Pytest-compatible test file for the following function.

Function to test:
```python
{put_source_code}
```

Requirements:
- Generate ONLY the test code, no explanations
- Use Pytest syntax and conventions
- Include multiple test cases covering edge cases
- Test both valid and invalid inputs
- Use descriptive test function names
- Import the function from the module

Output the test code in a Python code block:
```python
# Your test code here
```"""


def generate_test_with_llm(config: Dict[str, Any], prompt: str) -> str:
    """
    Send prompt to LLM and receive response.

    Args:
        config: Configuration dictionary with LLM settings
        prompt: The prompt to send to the LLM

    Returns:
        The LLM response as a string

    Raises:
        Exception: If LLM interaction fails
    """
    try:
        return generate_text(config, prompt)
    except Exception as e:
        raise Exception(f"LLM interaction failed: {e}")


def log_llm_interaction(put_id: str, prompt: str, response: str, log_dir: str) -> str:
    """
    Log LLM interaction to a file.

    Args:
        put_id: The PUT identifier
        prompt: The prompt sent to LLM
        response: The LLM response
        log_dir: Directory to store log files

    Returns:
        Path to the created log file
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create log file path
    log_file = log_path / f"put_{put_id}.log"

    # Prepare log content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_content = f"""[{timestamp}] Processing PUT: {put_id}
[{timestamp}] Prompt sent to LLM:
{prompt}

[{timestamp}] LLM Response received:
{response}

[{timestamp}] Generation completed successfully
"""

    # Write log file atomically
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(log_content)

    return str(log_file)


def generate_test_for_put(
    put_id: str, config: Dict[str, Any], log_dir: str = "logs"
) -> Dict[str, Any]:
    """
    Generate test for a single PUT using LLM.

    Args:
        put_id: The PUT identifier (e.g., "he_0")
        config: Configuration dictionary with LLM settings
        log_dir: Directory to store log files

    Returns:
        Dictionary with results:
        - put_id: The PUT identifier
        - prompt: The prompt sent to LLM
        - response: The LLM response
        - log_file: Path to the log file
        - success: Boolean indicating success
        - error: Error message if failed
    """
    result = {
        "put_id": put_id,
        "prompt": "",
        "response": "",
        "log_file": "",
        "success": False,
        "error": "",
    }

    try:
        # Step 1: Read PUT file
        put_source_code = read_put_file(put_id)

        # Step 2: Build prompt
        prompt = build_test_generation_prompt(put_source_code)
        result["prompt"] = prompt

        # Step 3: Generate test with LLM
        response = generate_test_with_llm(config, prompt)
        result["response"] = response

        # Step 4: Log interaction
        log_file = log_llm_interaction(put_id, prompt, response, log_dir)
        result["log_file"] = log_file

        # Mark as successful
        result["success"] = True

    except FileNotFoundError as e:
        result["error"] = f"PUT file not found: {e}"
    except Exception as e:
        result["error"] = f"Generation failed: {e}"

    return result


def get_all_put_ids(human_eval_dir: str = "HumanEval") -> list:
    """
    Get list of all PUT IDs from HumanEval directory.

    Args:
        human_eval_dir: Directory containing PUT files

    Returns:
        List of PUT IDs sorted numerically
    """
    put_dir = Path(human_eval_dir)

    if not put_dir.exists():
        return []

    # Find all he_*.py files
    put_files = list(put_dir.glob("he_*.py"))

    # Extract IDs and sort numerically
    put_ids = []
    for file_path in put_files:
        put_id = file_path.stem  # Remove .py extension
        put_ids.append(put_id)

    # Sort numerically (he_0, he_1, he_10, he_100, etc.)
    def sort_key(put_id):
        # Extract number from he_X format
        try:
            return int(put_id.split("_")[1])
        except (IndexError, ValueError):
            return 0

    put_ids.sort(key=sort_key)
    return put_ids
