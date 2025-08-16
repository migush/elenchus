"""
Prompt Manager for handling prompt techniques and versions.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from .csv_manager import ExperimentCSVManager


class PromptManager:
    """Manages prompt techniques stored in CSV files and loads templates from external files."""

    # Compiled regex pattern for validating template names
    TEMPLATE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def __init__(self, csv_manager: ExperimentCSVManager, prompts_dir: str = "prompts"):
        """
        Initialize PromptManager.

        Sets up paths under prompts_dir (templates directory and prompt_config.yaml), loads the prompt configuration, and validates referenced template files.

        Parameters:
            prompts_dir (str): Directory containing prompt assets (default "prompts"); used to locate the templates subdirectory and the prompt_config.yaml file.
        """
        self.csv_manager = csv_manager
        self.prompts_dir = Path(prompts_dir)
        self.template_dir = self.prompts_dir / "templates"

        # Cache the resolved template directory path to avoid repeated resolution
        try:
            self._resolved_template_dir = self.template_dir.resolve()
        except (RuntimeError, OSError) as e:
            raise ValueError(f"Failed to resolve template directory path: {e}")

        self.config_file = self.prompts_dir / "prompt_config.yaml"

        # Load prompt configuration
        self.prompt_config = self._load_prompt_config()

        # Validate template files exist
        self._validate_templates()

    def _load_prompt_config(self) -> Dict[str, Any]:
        """
        Load and return the prompt manager configuration from the YAML config file.

        Reads and parses the YAML file pointed to by self.config_file and returns the resulting dict.
        Raises FileNotFoundError if the config file does not exist.
        Raises ValueError if the file cannot be parsed as valid YAML.

        Returns:
            Dict[str, Any]: Parsed configuration dictionary.
        """
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Prompt configuration file not found: {self.config_file}"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing prompt configuration: {e}")

    def _validate_templates(self):
        """
        Validate prompt template configuration and ensure referenced template files exist.

        Checks that the loaded prompt configuration contains a non-empty "prompt_templates"
        mapping. For each category it verifies:
        - template info is a dictionary,
        - a "template_file" entry exists and is a non-empty string,
        - the file exists under the manager's templates directory.

        Raises:
            ValueError: If the "prompt_templates" section is missing, not a dict,
                empty, or any category has invalid template info or missing/invalid
                "template_file".
            FileNotFoundError: If a referenced template file does not exist under
                the templates directory.
        """
        if "prompt_templates" not in self.prompt_config:
            raise ValueError(
                "Missing 'prompt_templates' section in prompt configuration"
            )

        if not isinstance(self.prompt_config["prompt_templates"], dict):
            raise ValueError("'prompt_templates' must be a dictionary")

        if not self.prompt_config["prompt_templates"]:
            raise ValueError("'prompt_templates' dictionary cannot be empty")

        for category, template_info in self.prompt_config["prompt_templates"].items():
            if not isinstance(template_info, dict):
                raise ValueError(
                    f"Template info for category '{category}' must be a dictionary"
                )

            template_file = template_info.get("template_file")
            if not template_file or not isinstance(template_file, str):
                raise ValueError(
                    f"Missing or invalid template_file for category: {category}"
                )

            template_path = self.template_dir / template_file
            if not template_path.exists():
                raise FileNotFoundError(f"Template file not found: {template_path}")

    def _load_template_content(self, template_file: str) -> str:
        """
        Load and return the text content of a template file located in the manager's templates directory.

        Parameters:
            template_file (str): Template filename relative to the templates directory (e.g., "zero_shot.txt").

        Returns:
            str: The full contents of the template file (UTF-8 decoded).

        Raises:
            FileNotFoundError: If the resolved template file does not exist.
            RuntimeError: If the file cannot be read for any other reason.
        """
        template_path = self.template_dir / template_file

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Template file not found: {template_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading template file {template_path}: {e}")

    def _get_template_file_for_category(self, category: str) -> str:
        """
        Return the template filename associated with a prompt category.

        If the category exists in the loaded prompt configuration, returns the configured
        `template_file` value for that category. If the category is not present, returns
        the configuration's `default_template` value; if that is not set, returns
        "zero_shot.txt".

        Parameters:
            category (str): Prompt category name.

        Returns:
            str: Template filename (not a filesystem path).
        """
        if category not in self.prompt_config["prompt_templates"]:
            # Use default template if category not found
            return self.prompt_config.get("default_template", "zero_shot.txt")

        return self.prompt_config["prompt_templates"][category]["template_file"]

    def register_prompt_technique(self, technique: Dict[str, Any]):
        """
        Register a new prompt technique and persist it to the CSV store.

        Parameters:
            technique (dict): Technique record to register. Must include the following keys:
                - "prompt_id": unique identifier for the technique
                - "name": human-readable name
                - "description": short description
                - "category": technique category (e.g., "few-shot", "zero-shot")
                - "version": version string

            If "created_at" is not present, an ISO-8601 timestamp will be added.
            If "is_active" is not present, it will be set to True.

        Raises:
            ValueError: if any required field is missing.

        Side effects:
            Persists the technique by calling the CSV manager's add_prompt_technique method.
        """
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
        technique = df[(df["prompt_id"] == prompt_id) & df["is_active"]]

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
            df = df[df["is_active"]]

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

    def get_prompt_template(
        self, prompt_id: str, source_code: str = "", template_id: str = ""
    ) -> Optional[str]:
        """
        Get the prompt template for a given prompt ID.

        This method loads a template file based on the prompt technique's category,
        then formats it with the provided source code and template identifier.

        Args:
            prompt_id: The unique identifier for the prompt technique
            source_code: The source code to be inserted into the template.
                        Defaults to empty string for backward compatibility.
            template_id: The identifier used in the template for module naming.
                        Defaults to empty string for backward compatibility.

        Returns:
            Formatted template string with source code and template ID inserted,
            or None if the prompt technique is not found.

        Template Formatting:
            Templates use Python's str.format() method with these placeholders:
            - {source_code}: Replaces with the provided source code
            - {template_id}: Replaces with the template identifier (typically used
              for module naming in import statements)

            To include literal braces in templates, escape them by doubling:
            - Use {{ to represent a literal { character
            - Use }} to represent a literal } character

            Example template usage:
            ```python
            def test_function():
                from {template_id} import function_name
                # Test the following code:
                {source_code}
            ```

        Raises:
            ValueError: If the prompt technique is missing required 'category' field
        """
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

        # Get template file for the category
        template_file = self._get_template_file_for_category(category)

        # Load template content from file
        template_content = self._load_template_content(template_file)

        # Format template with provided values
        formatted_template = template_content.format(
            source_code=source_code, template_id=template_id
        )

        return formatted_template

    def get_available_templates(self) -> List[str]:
        """
        Return a sorted list of available template filenames ('.txt') in the templates directory.

        If the templates directory does not exist, returns an empty list.

        Returns:
            List[str]: Sorted list of template filenames (e.g., 'zero_shot.txt').
        """
        if not self.template_dir.exists():
            return []

        template_files = []
        for file_path in self.template_dir.glob("*.txt"):
            template_files.append(file_path.name)

        return sorted(template_files)

    def _validate_template_name(self, template_name: str):
        """
        Validate a template filename to prevent path traversal and ensure a safe name.

        Validates that `template_name` is a non-empty string, does not contain path
        separators or parent-directory references, and contains only letters,
        numbers, underscores, or hyphens.

        Parameters:
            template_name (str): The base name of the template (without directory or
                extension).

        Raises:
            ValueError: If `template_name` is empty or not a string, contains path
                separators or parent references (e.g. `..`), or contains characters
                outside the allowed set (letters, numbers, underscores, hyphens).
        """
        if not template_name or not isinstance(template_name, str):
            raise ValueError("Template name must be a non-empty string")

        # Check for path separators and parent references
        if os.path.sep in template_name or ".." in template_name:
            raise ValueError(
                "Template name cannot contain path separators or parent references"
            )

        # Check for safe characters only (letters, numbers, underscores, hyphens)
        if not self.TEMPLATE_NAME_PATTERN.match(template_name):
            raise ValueError(
                "Template name can only contain letters, numbers, underscores, and hyphens"
            )

    def _get_validated_template_path(self, template_name: str) -> Path:
        """
        Return a safe Path to a template file inside the manager's templates directory.

        Validates the provided template name, appends the ".txt" extension, resolves the resulting path,
        and ensures the resolved path is contained within the manager's templates directory to prevent
        path traversal.

        Parameters:
            template_name (str): Template basename (without extension). Must be a non-empty string
                containing only allowed characters (no path separators or parent references).

        Returns:
            pathlib.Path: The (possibly non-existent) Path object for templates/{template_name}.txt
                under the manager's templates directory.

        Raises:
            ValueError: If the template name is invalid or if the resolved path would lie outside
                the templates directory.
        """
        self._validate_template_name(template_name)

        template_path = self.template_dir / f"{template_name}.txt"

        # Ensure the resolved path is within template_dir
        try:
            resolved_path = template_path.resolve()
            if not resolved_path.is_relative_to(self.template_dir.resolve()):
                raise ValueError("Template path would be outside template directory")
        except (RuntimeError, ValueError) as e:
            raise ValueError(f"Invalid template path: {e}")

        return template_path

    def add_custom_template(self, template_name: str, template_content: str):
        """
        Add a new custom template file under the templates directory.

        The provided template_name is validated (no path separators, only letters/numbers/underscores/hyphens) and resolved to
        templates/{template_name}.txt inside the prompts directory. The template_content is written to that file, creating or
        overwriting it.

        Parameters:
            template_name (str): Base name for the template file (without extension). Must pass name validation.
            template_content (str): UTF-8 content to write into the template file.

        Raises:
            RuntimeError: If writing the file fails.
        """
        template_path = self._get_validated_template_path(template_name)

        try:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"✅ Custom template '{template_name}' added successfully")
        except Exception as e:
            raise RuntimeError(f"Error creating custom template: {e}")

    def update_template(self, template_name: str, template_content: str):
        """
        Update an existing prompt template file.

        Template names are validated and resolved to the templates directory (e.g. a template_name "foo" maps to "templates/foo.txt"). The file is overwritten with the provided content.

        Parameters:
            template_name (str): The template's base name (no path separators). It will be resolved to `<templates_dir>/<template_name>.txt`.
            template_content (str): New content to write into the template file.

        Raises:
            ValueError: If the template name is invalid (path traversal or disallowed characters).
            FileNotFoundError: If the resolved template file does not exist.
            RuntimeError: If an I/O error or other problem occurs while writing the file.
        """
        template_path = self._get_validated_template_path(template_name)

        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")

        try:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            print(f"✅ Template '{template_name}' updated successfully")
        except Exception as e:
            raise RuntimeError(f"Error updating template: {e}")

    def delete_template(self, template_name: str):
        """
        Delete a template file stored in the templates directory.

        Attempts to remove the template file resolved from `template_name` (validated to prevent path traversal and restricted to allowed characters). Raises FileNotFoundError if the resolved template does not exist. Raises RuntimeError if an unexpected error occurs while deleting the file.
        """
        template_path = self._get_validated_template_path(template_name)

        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")

        try:
            template_path.unlink()
            print(f"✅ Template '{template_name}' deleted successfully")
        except Exception as e:
            raise RuntimeError(f"Error deleting template: {e}")
