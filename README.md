# Elenchus

A comprehensive framework for generating and evaluating test code using Large Language Models.

## Features

- **Test Generation**: Generate test code using various prompting techniques
- **LLM Integration**: Support for multiple LLM providers and models
- **Experiment Tracking**: Record and analyze test generation experiments
- **Prompt Management**: Flexible prompt template system with external configuration
- **Configuration Management**: Environment-aware configuration with validation

## Installation

This project uses [pixi](https://pixi.sh/) for environment and dependency management.

### Prerequisites

- Python 3.13.5+
- pixi package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd elenchus
```

2. Install dependencies:
```bash
pixi install
```

3. For PyCharm integration (Linux/macOS only):
```bash
pixi install --feature pycharm
```

**Note**: The `pixi-pycharm` dependency is only officially supported on Linux and macOS. Windows support is not available.

## Usage

### Basic Commands

```bash
# Display help
pixi run elenchus --help

# Show configuration
pixi run elenchus config

# Generate tests
pixi run elenchus generate <source_file>

# Run experiments
pixi run elenchus run-phase <phase_name>
```

### Configuration

The system supports multiple configuration sources with priority order:
1. CLI arguments (highest priority)
2. Environment variables
3. Configuration file (`~/.elenchus/config.yaml`)
4. Schema defaults (lowest priority)

See [examples/config.yaml](examples/config.yaml) for a configuration example and [config/schema.py](config/schema.py) for the complete configuration schema.

## Development

### Code Quality

```bash
# Format code
pixi run format

# Check formatting
pixi run check-format
```

### Testing

```bash
# Run tests
pixi run pytest

# Run tests with coverage
pixi run pytest --cov
```

## Project Structure

- `core/`: Core functionality for test generation and LLM integration
- `cli/`: Command-line interface commands
- `config/`: Configuration management and validation
- `prompts/`: Prompt templates and configuration
- `experiments/`: Experiment data and results
- `docs/`: Project documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and formatting checks
5. Submit a pull request

## License

See [LICENSE](LICENSE) for details.
