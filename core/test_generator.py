"""
Core test generation module for Step 2. LLM Test Generation.

This module handles reading PUT files, building LLM prompts,
interacting with the LLM, and logging all interactions.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import re
import ast
import py_compile
import subprocess
import os
import xml.etree.ElementTree as ET

from .llm import generate_text
from .experiment_recorder import ExperimentRecorder


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


def build_test_generation_prompt(
    put_id: str,
    put_source_code: str,
    previous_test_code: Optional[str] = None,
    feedback: Optional[str] = None,
) -> str:
    """
    Build a prompt for LLM test generation.

    Args:
        put_source_code: The full source code of the PUT

    Returns:
        Formatted prompt string for the LLM
    """
    base = f"""You are a Python testing expert. Generate a comprehensive Pytest-compatible test file for the following function.

Function to test:
```python
{put_source_code}
```

Context:
- The function above is saved in a module named: {put_id}.py
- When importing in the test, import from that module name, e.g., `from {put_id} import <function_name>`.

Requirements:
- Generate ONLY the test code, no explanations
- Use Pytest syntax and conventions
- Include multiple test cases covering edge cases
- Test both valid and invalid inputs
- Use descriptive test function names
- Import the function from the module `{put_id}`

Output the test code in a Python code block:
```python
# Your test code here
```"""

    extras = []
    if previous_test_code:
        extras.append(
            "Previous attempt (fix and improve this test, keep only Python test code in output):\n```python\n"
            + previous_test_code
            + "\n```"
        )
    if feedback:
        extras.append(
            "Issues found (address all of them; do not include this text in the output):\n"
            + feedback
        )

    if extras:
        return base + "\n\n" + "\n\n".join(extras)
    return base


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


def extract_python_code_from_response(response: str) -> Tuple[bool, str, str]:
    """
    Extract a Python code block from an LLM response.

    Returns:
        (extracted, code, reason)
    """
    # Prefer fenced blocks labeled as python/py
    labeled_block = re.search(
        r"```(?:python|py)\s*\n([\s\S]*?)\n```", response, re.IGNORECASE
    )
    if labeled_block:
        return True, labeled_block.group(1).strip(), "found_python_fence"

    # Fallback: any fenced block
    any_block = re.search(r"```\s*\n([\s\S]*?)\n```", response)
    if any_block:
        return True, any_block.group(1).strip(), "found_generic_fence"

    # Last resort: treat whole response as code
    # This is less safe, but lets us attempt validation
    return False, response.strip(), "no_fence_found"


def is_valid_python_code(code: str) -> Tuple[bool, Optional[str]]:
    """
    Check if code is syntactically valid Python.
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (line {e.lineno}, col {e.offset})"


def save_test_code_to_file(put_id: str, code: str, tests_dir: str) -> str:
    """
    Save extracted test code to a test file within tests_dir.
    """
    tests_path = Path(tests_dir)
    tests_path.mkdir(parents=True, exist_ok=True)
    test_filename = f"test_{put_id}.py"
    test_file_path = tests_path / test_filename

    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Optionally pre-compile to pyc to catch encoding-related issues
    try:
        py_compile.compile(str(test_file_path), doraise=True)
    except Exception:
        # Ignore here; syntax is already validated by AST. This catches extra issues but isn't fatal.
        pass

    return str(test_file_path)


def log_llm_interaction(
    put_id: str, prompt: str, response: str, log_dir: str, iteration: int = 1
) -> str:
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
    log_file = log_path / f"put_{put_id}_iter{iteration}.log"

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
    put_id: str,
    config: Dict[str, Any],
    log_dir: str = "logs",
    human_eval_dir: str = "HumanEval",
    tests_dir: Optional[str] = None,
    run: bool = False,
    measure_coverage: bool = False,
    prompt_id: str = "default",
    experiment_recorder: Optional[ExperimentRecorder] = None,
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
        "test_file": "",
        "syntax_ok": False,
        "ran": False,
        "passed": False,
        "returncode": None,
        "run_stdout": "",
        "run_stderr": "",
        "success": False,
        "error": "",
        "coverage_percent": None,
        "coverage_xml": "",
    }

    try:
        experiment_id: Optional[str] = None
        # Step 1: Read PUT file
        put_source_code = read_put_file(put_id, human_eval_dir)

        max_iterations = int(config.get("max_iterations", 1) or 1)
        previous_test_code: Optional[str] = None
        feedback: Optional[str] = None
        last_log_file: Optional[str] = None
        last_run_log_file: Optional[str] = None

        # Start experiment recording if enabled
        if experiment_recorder is not None and bool(
            config.get("track_experiments", True)
        ):
            try:
                experiment_id = experiment_recorder.start_experiment(
                    put_id, prompt_id, config
                )
            except Exception:
                experiment_id = None

        for iteration in range(1, max_iterations + 1):
            # Step 2: Build prompt (with feedback from previous attempt if any)
            prompt = build_test_generation_prompt(
                put_id,
                put_source_code,
                previous_test_code=previous_test_code,
                feedback=feedback,
            )
            result["prompt"] = prompt

            # Step 3: Generate test with LLM
            response = generate_test_with_llm(config, prompt)
            result["response"] = response

            # Step 4: Extract python test code
            _, test_code, extract_reason = extract_python_code_from_response(response)
            previous_test_code = test_code

            # Step 5: Validate syntax
            syntax_ok, syntax_err = is_valid_python_code(test_code)
            result["syntax_ok"] = bool(syntax_ok)

            # Record code generation attempt
            if experiment_id and experiment_recorder is not None:
                experiment_recorder.record_code_generation(
                    experiment_id=experiment_id,
                    iteration=iteration,
                    success=bool(syntax_ok),
                    code=test_code,
                    response=response,
                )

            # Step 6: Save to tests directory (overwrite latest attempt)
            effective_tests_dir = tests_dir or str(Path(log_dir).parent / "tests")
            test_file_path = save_test_code_to_file(
                put_id, test_code, effective_tests_dir
            )
            result["test_file"] = test_file_path

            # Step 7: Log interaction (per-iteration)
            last_log_file = log_llm_interaction(
                put_id, prompt, response, log_dir, iteration
            )
            result["log_file"] = last_log_file

            # If syntax invalid, prepare feedback and continue if iterations remain
            if not syntax_ok:
                feedback = f"The test code is not valid Python ({extract_reason}). Parser error: {syntax_err}.\nPlease fix all syntax errors and ensure the test imports from module '{put_id}'."
                if iteration == max_iterations:
                    raise Exception(
                        f"Generated test is not valid Python after {max_iterations} attempts: {syntax_err}"
                    )
                continue

            # Step 8: Optionally run pytest on the generated test
            if run:
                # Prepare coverage path per iteration if requested
                cov_xml_path = None
                if measure_coverage:
                    coverage_dir = Path(log_dir).resolve().parent / "coverage"
                    coverage_dir.mkdir(parents=True, exist_ok=True)
                    cov_xml_path = str(
                        (
                            coverage_dir / f"put_{put_id}_cov_iter{iteration}.xml"
                        ).resolve()
                    )

                # Measure execution time
                _run_start = datetime.now()
                run_info = run_test_file(
                    result["test_file"],
                    human_eval_dir,
                    module_name=put_id,
                    cov_xml_path=cov_xml_path,
                )
                _run_end = datetime.now()
                test_exec_seconds = (_run_end - _run_start).total_seconds()
                result["ran"] = True
                result["passed"] = run_info.get("passed", False)
                result["returncode"] = run_info.get("returncode")
                result["run_stdout"] = run_info.get("stdout", "")
                result["run_stderr"] = run_info.get("stderr", "")

                # Parse coverage if generated
                if measure_coverage and cov_xml_path and os.path.exists(cov_xml_path):
                    # Only report coverage when the test run passed to avoid misleading values
                    if result["passed"]:
                        result["coverage_xml"] = cov_xml_path
                        result["coverage_percent"] = parse_coverage_xml(cov_xml_path)
                    else:
                        result["coverage_xml"] = cov_xml_path
                        result["coverage_percent"] = None

                # Write run output to log file per iteration
                run_log_path = (
                    Path(log_dir).resolve() / f"put_{put_id}_run_iter{iteration}.log"
                )
                with open(run_log_path, "w", encoding="utf-8") as f:
                    f.write(run_info.get("stdout", ""))
                    if run_info.get("stderr"):
                        f.write("\n[stderr]\n")
                        f.write(run_info.get("stderr", ""))
                last_run_log_file = str(run_log_path)

                if result["passed"]:
                    # Success path
                    break

                # Prepare feedback from pytest failure and iterate
                feedback = (
                    "The generated test failed when executed with pytest. "
                    "Analyze the failure output below and correct the test accordingly.\n\n"
                    f"Pytest return code: {result['returncode']}\n\n"
                    f"Output (truncated):\n{_truncate_text(result['run_stdout'], 3000)}\n\n"
                )

                # Record test generation attempt
                if experiment_id and experiment_recorder is not None:
                    coverage_val = result.get("coverage_percent") or 0.0
                    experiment_recorder.record_test_generation(
                        experiment_id=experiment_id,
                        iteration=iteration,
                        success=bool(result.get("passed", False)),
                        tests=previous_test_code or "",
                        coverage=float(coverage_val),
                    )

                if iteration == max_iterations:
                    # Will exit loop and mark result as not passing
                    break
                continue
            else:
                # If not running, a syntactically valid test counts as success
                break

        # Mark as successful if syntax ok and either no run requested OR tests passed
        if result["syntax_ok"] and (not run or result.get("passed", False)):
            result["success"] = True
        else:
            if run and not result.get("passed"):
                result["error"] = (
                    result.get("error")
                    or f"Test did not pass after {max_iterations} attempts (see logs)."
                )

        # Finalize experiment if recording
        if experiment_id and experiment_recorder is not None:
            try:
                # Estimate test_count by counting pytest-style functions
                test_code_snapshot = previous_test_code or ""
                test_count_estimate = len(
                    re.findall(r"^def\s+test_", test_code_snapshot, re.MULTILINE)
                )

                final_stats: Dict[str, Any] = {
                    "code_generation_success": bool(result.get("syntax_ok", False)),
                    "code_iterations_needed": (
                        max_iterations if not result.get("syntax_ok") else iteration
                    ),
                    "test_generation_success": (
                        bool(result.get("passed", False))
                        if run
                        else bool(result.get("syntax_ok", False))
                    ),
                    "test_iterations_needed": iteration,
                    "test_coverage": float(result.get("coverage_percent") or 0.0),
                    "test_count": int(test_count_estimate),
                    "test_execution_time": float(
                        locals().get("test_exec_seconds", 0.0)
                    ),
                    "system_prompt": "",
                    "user_prompt": result.get("prompt", ""),
                    "llm_response": result.get("response", ""),
                }
                experiment_recorder.finalize_experiment(experiment_id, final_stats)
            except Exception:
                pass

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


def run_test_file(
    test_file: str,
    human_eval_dir: str,
    module_name: Optional[str] = None,
    cov_xml_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run a single pytest test file, ensuring the HumanEval directory is importable.

    Returns dict with keys: passed (bool), returncode (int), stdout, stderr
    """
    # Build environment with PYTHONPATH including the human_eval_dir
    env = os.environ.copy()
    pythonpath_parts = []
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    pythonpath_parts.insert(0, str(Path(human_eval_dir).resolve()))
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    # Run pytest quietly on the specific file
    cmd = [
        "python",
        "-m",
        "pytest",
        "-q",
        str(Path(test_file).resolve()),
    ]

    # Add coverage arguments if requested
    if module_name and cov_xml_path:
        cmd.extend([f"--cov={module_name}", f"--cov-report=xml:{cov_xml_path}"])

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=str(Path(test_file).parent.resolve()),
    )

    return {
        "passed": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _truncate_text(text: str, limit: int) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def parse_coverage_xml(xml_path: str) -> Optional[float]:
    """
    Parse Cobertura XML produced by coverage.py and return line-rate as percentage.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        line_rate = root.attrib.get("line-rate")
        if line_rate is not None:
            return round(float(line_rate) * 100.0, 2)
    except Exception:
        return None
    return None
