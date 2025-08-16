# Prompt Templates

This directory contains the prompt templates used by the PromptManager for generating test code.

## Structure

```
prompts/
├── README.md                 # This file
├── prompt_config.yaml        # Configuration mapping categories to template files
└── templates/                # Directory containing actual template files
    ├── chain_of_thought.txt  # Chain-of-thought reasoning template
    ├── few_shot.txt          # Few-shot learning template
    └── zero_shot.txt         # Direct generation template
```

## Configuration

The `prompt_config.yaml` file maps prompt categories to their corresponding template files:

```yaml
prompt_templates:
  chain-of-thought:
    template_file: "chain_of_thought.txt"
    description: "Chain-of-thought reasoning for test generation"
    
  few-shot:
    template_file: "few_shot.txt"
    description: "Few-shot learning with examples for test generation"
    
  zero-shot:
    template_file: "zero_shot.txt"
    description: "Direct test generation without examples"
```

## Template Files

Each template file contains the actual prompt text with placeholders for dynamic content:

- `{source_code}` - The source code of the function to test
- `{template_id}` - The module name/ID for importing the function

### Template Formatting

Templates use Python's `str.format()` method with these placeholders:
- `{source_code}`: Replaces with the provided source code
- `{template_id}`: Replaces with the template identifier (typically used for module naming in import statements)

To include literal braces in templates, escape them by doubling:
- Use `{{` to represent a literal `{` character
- Use `}}` to represent a literal `}` character

Example template usage:
```python
def test_function():
    from {template_id} import function_name
    # Test the following code:
    {source_code}
```

## Adding New Templates

1. Create a new `.txt` file in the `templates/` directory
2. Add the template configuration to `prompt_config.yaml`
3. Use the PromptManager's `add_custom_template()` method programmatically

## Usage

The PromptManager automatically loads templates based on the prompt category:

```python
from core.prompt_manager import PromptManager

# Initialize with default prompts directory
prompt_manager = PromptManager(csv_manager)

# Or specify custom prompts directory
prompt_manager = PromptManager(csv_manager, prompts_dir="custom_prompts")

# Get template for a specific category
template = prompt_manager.get_prompt_template("my_category")

# Get template with source code and template ID
template = prompt_manager.get_prompt_template(
    "my_category", 
    source_code="def example(): pass", 
    template_id="example_module"
)
```

## Benefits of External Templates

- **Maintainability**: Easy to edit prompts without changing code
- **Version Control**: Track prompt changes separately from code
- **Collaboration**: Non-developers can edit prompts
- **Flexibility**: Add new templates without code changes
- **Testing**: Test prompt variations independently
