# Installation Guide

## Development Installation

For development work, install the package in editable mode:

```bash
# From the project root directory
pip install -e .
```

This will install the `elenchus` package in editable mode, making imports work correctly.

## Alternative: Using pixi

Since this project uses pixi for environment management, you can also:

```bash
# Install pixi if you haven't already
curl -fsSL https://pixi.sh/install.sh | bash

# Install the project dependencies
pixi install

# Activate the environment
pixi shell

# Install the package in editable mode within the pixi environment
pip install -e .
```

## Why This Fixes Import Issues

The original code had a hacky `sys.path.insert()` approach that could cause import conflicts and is generally not recommended. By installing the package properly:

1. **Proper package structure**: The `elenchus` package becomes available in the Python path
2. **Clean imports**: No more `sys.path` manipulation needed
3. **Consistent behavior**: Works the same in development and production
4. **Standard practice**: Follows Python packaging best practices

## Troubleshooting

If you still encounter import issues:

1. Make sure you're in the project root directory when running `pip install -e .`
2. Verify the package is installed: `pip list | grep elenchus`
3. Check that you're using the correct Python environment
4. Try uninstalling and reinstalling: `pip uninstall elenchus && pip install -e .`
