"""
Prompt Manager for handling prompt techniques and versions.
"""

from typing import Dict, Any, List, Optional
from .csv_manager import ExperimentCSVManager


class PromptManager:
    """Manages prompt techniques stored in CSV files."""

    def __init__(self, csv_manager: ExperimentCSVManager):
        self.csv_manager = csv_manager

    def register_prompt_technique(self, technique: Dict[str, Any]):
        """Register a new prompt technique to CSV."""
        required_fields = ["prompt_id", "name", "description", "category", "version"]

        # Validate required fields
        for field in required_fields:
            if field not in technique:
                raise ValueError(f"Missing required field: {field}")

        # Add timestamp if not provided
        if "created_at" not in technique:
            from datetime import datetime

            technique["created_at"] = datetime.now().isoformat()

        # Set default active status
        if "is_active" not in technique:
            technique["is_active"] = True

        # Add to CSV
        self.csv_manager.add_prompt_technique(technique)
        print(f"✅ Prompt technique '{technique['prompt_id']}' registered successfully")

    def get_prompt_technique(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve prompt technique details from CSV."""
        df = self.csv_manager.get_prompt_techniques()

        if df.empty:
            return None

        # Filter by prompt_id and active status
        technique = df[(df["prompt_id"] == prompt_id) & (df["is_active"] == True)]

        if technique.empty:
            return None

        # Convert to dictionary
        return technique.iloc[0].to_dict()

    def list_prompt_techniques(
        self, category: Optional[str] = None, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """List available prompt techniques from CSV."""
        df = self.csv_manager.get_prompt_techniques()

        if df.empty:
            return []

        # Apply filters
        if active_only:
            df = df[df["is_active"] == True]

        if category:
            df = df[df["category"] == category]

        # Convert to list of dictionaries
        return df.to_dict("records")

    def update_prompt_technique(self, prompt_id: str, updates: Dict[str, Any]):
        """Update an existing prompt technique."""
        df = self.csv_manager.get_prompt_techniques()

        if df.empty:
            print(f"Warning: No prompt techniques found")
            return

        # Find the technique
        mask = df["prompt_id"] == prompt_id
        if not mask.any():
            print(f"Warning: Prompt technique '{prompt_id}' not found")
            return

        # Update the technique
        for key, value in updates.items():
            if key in df.columns:
                df.loc[mask, key] = value

        # Save back to CSV
        file_path = self.csv_manager.prompts_dir / "prompt_techniques.csv"
        df.to_csv(file_path, index=False)

        print(f"✅ Prompt technique '{prompt_id}' updated successfully")

    def deactivate_prompt_technique(self, prompt_id: str):
        """Deactivate a prompt technique."""
        self.update_prompt_technique(prompt_id, {"is_active": False})

    def activate_prompt_technique(self, prompt_id: str):
        """Activate a prompt technique."""
        self.update_prompt_technique(prompt_id, {"is_active": True})

    def get_prompt_categories(self) -> List[str]:
        """Get list of available prompt categories."""
        df = self.csv_manager.get_prompt_techniques()

        if df.empty:
            return []

        # Get unique categories
        categories = df["category"].unique().tolist()
        return [cat for cat in categories if cat]  # Filter out None/NaN

    def create_chain_of_thought_prompt(
        self, prompt_id: str, name: str, description: str
    ):
        """Create a chain-of-thought prompt technique."""
        technique = {
            "prompt_id": prompt_id,
            "name": name,
            "description": description,
            "category": "chain-of-thought",
            "version": "1.0",
        }
        self.register_prompt_technique(technique)

    def create_few_shot_prompt(self, prompt_id: str, name: str, description: str):
        """Create a few-shot prompt technique."""
        technique = {
            "prompt_id": prompt_id,
            "name": name,
            "description": description,
            "category": "few-shot",
            "version": "1.0",
        }
        self.register_prompt_technique(technique)

    def create_zero_shot_prompt(self, prompt_id: str, name: str, description: str):
        """Create a zero-shot prompt technique."""
        technique = {
            "prompt_id": prompt_id,
            "name": name,
            "description": description,
            "category": "zero-shot",
            "version": "1.0",
        }
        self.register_prompt_technique(technique)

    def get_prompt_template(self, prompt_id: str) -> Optional[str]:
        """Get the prompt template for a given prompt ID."""
        technique = self.get_prompt_technique(prompt_id)

        if not technique:
            return None

        # Get category from technique, with fallback to config
        category = technique.get("category")
        if not category:
            # This should be handled by configuration validation
            raise ValueError(
                f"Prompt technique {prompt_id} missing required 'category' field"
            )

        # For now, return a basic template based on category
        # TODO: Move these templates to configuration files
        if category == "chain-of-thought":
            return """You are a Python testing expert. Think through this step by step:

1. First, analyze the function to understand what it does
2. Identify the key functionality and edge cases
3. Consider what could go wrong
4. Generate comprehensive tests

Function to test:
```python
{put_source_code}
```

Context:
- The function above is saved in a module named: {put_id}.py
- When importing in the test, import from that module name

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

        elif category == "few-shot":
            return """You are a Python testing expert. Here are some examples of good test patterns:

Example 1 - Testing a simple function:
```python
def test_simple_function():
    result = simple_function(2, 3)
    assert result == 5
    
def test_edge_case():
    result = simple_function(0, 0)
    assert result == 0
```

Example 2 - Testing with different input types:
```python
def test_valid_inputs():
    assert function("hello") == "HELLO"
    assert function("world") == "WORLD"
    
def test_invalid_inputs():
    with pytest.raises(ValueError):
        function("")
```

Now generate tests for this function:
```python
{put_source_code}
```

Context:
- The function above is saved in a module named: {put_id}.py
- When importing in the test, import from that module name

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

        else:  # zero-shot
            return """You are a Python testing expert. Generate a comprehensive Pytest-compatible test file for the following function.

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
