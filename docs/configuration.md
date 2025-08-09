# Elenchus Configuration Guide

This guide explains how to configure Elenchus CLI for your environment and use cases.

## Configuration Sources and Priority

Elenchus supports multiple configuration sources with the following priority order (highest to lowest):

1. **Command-line arguments** - Override all other sources
2. **Environment variables** - Override file and defaults
3. **Configuration file** - `~/.elenchus/config.yaml`
4. **Default values** - Built-in sensible defaults

## Configuration File

The configuration file is automatically created at `~/.elenchus/config.yaml` when you first run Elenchus.

### Example Configuration File

```yaml
# HumanEval dataset configuration
human_eval_url: "https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz"
output_dir: "generated_tests"
max_iterations: 5

# LLM configuration
llm_model: "gpt-4"
llm_api_key: null  # Set your API key here or use environment variable
llm_temperature: 0.1
llm_max_tokens: 2000
llm_provider: "openai"
llm_base_url: null  # For custom endpoints

# Logging configuration
log_level: "INFO"
log_file: null
```

## Environment Variables

You can set configuration values using environment variables. This is especially useful for sensitive information like API keys.

### Available Environment Variables

| Environment Variable | Configuration Key | Description |
|---------------------|-------------------|-------------|
| `ELENCHUS_HUMAN_EVAL_URL` | `human_eval_url` | HumanEval dataset URL |
| `ELENCHUS_OUTPUT_DIR` | `output_dir` | Default output directory |
| `ELENCHUS_MAX_ITERATIONS` | `max_iterations` | Maximum iterations for test generation |
| `ELENCHUS_LLM_MODEL` | `llm_model` | LLM model to use |
| `ELENCHUS_LLM_API_KEY` | `llm_api_key` | LLM API key (recommended to use env var) |
| `ELENCHUS_LLM_TEMPERATURE` | `llm_temperature` | LLM temperature (0.0-2.0) |
| `ELENCHUS_LLM_MAX_TOKENS` | `llm_max_tokens` | Maximum tokens for LLM responses |
| `ELENCHUS_LLM_PROVIDER` | `llm_provider` | LLM provider (openai, azure, ollama, etc.) |
| `ELENCHUS_LLM_BASE_URL` | `llm_base_url` | Custom LLM endpoint URL |
| `ELENCHUS_LOG_LEVEL` | `log_level` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `ELENCHUS_LOG_FILE` | `log_file` | Log file path |

### Example .env File

Create a `.env` file in your project directory:

```bash
# LLM Configuration
ELENCHUS_LLM_API_KEY=sk-your-api-key-here
ELENCHUS_LLM_MODEL=gpt-4
ELENCHUS_LLM_TEMPERATURE=0.1
ELENCHUS_LLM_MAX_TOKENS=2000

# Output Configuration
ELENCHUS_OUTPUT_DIR=./my_tests
ELENCHUS_MAX_ITERATIONS=10

# Logging
ELENCHUS_LOG_LEVEL=INFO
```

### Using Different LLM Providers

Elenchus uses LiteLLM directly for provider-agnostic LLM access. You can use any supported provider by setting the appropriate model name and API key:

#### OpenAI
```bash
export ELENCHUS_LLM_MODEL=gpt-4
export ELENCHUS_LLM_API_KEY=sk-your-openai-key
```

#### Anthropic Claude
```bash
export ELENCHUS_LLM_MODEL=claude-3-sonnet-20240229
export ELENCHUS_LLM_API_KEY=sk-ant-your-anthropic-key
```

#### Ollama (Local)
```bash
export ELENCHUS_LLM_MODEL=ollama/llama3.2:3b
export ELENCHUS_LLM_BASE_URL=http://localhost:11434
# No API key needed for local Ollama
```

#### Azure OpenAI
```bash
export ELENCHUS_LLM_MODEL=azure/your-deployment-name
export ELENCHUS_LLM_API_KEY=your-azure-key
export ELENCHUS_LLM_BASE_URL=https://your-resource.openai.azure.com
```

#### HuggingFace
```bash
export ELENCHUS_LLM_MODEL=huggingface/meta-llama/Llama-2-7b-chat-hf
export ELENCHUS_LLM_API_KEY=hf-your-huggingface-key
export ELENCHUS_LLM_BASE_URL=https://your-endpoint.huggingface.cloud
```

For a complete list of supported providers and models, see the [LiteLLM documentation](https://docs.litellm.ai/docs/).

### Ollama Setup

To use Ollama as your LLM provider:

1. **Install Ollama**: Follow the instructions at [ollama.ai](https://ollama.ai)

2. **Pull a model**: 
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Configure Elenchus for Ollama**:
   ```bash
   # Set the model to use Ollama format
   pixi run python main.py set-config llm_model ollama/llama3.2:3b
   
   # Set the Ollama server URL
   pixi run python main.py set-config llm_base_url http://localhost:11434
   ```

4. **Or use environment variables**:
   ```bash
   export ELENCHUS_LLM_MODEL=ollama/llama3.2:3b
   export ELENCHUS_LLM_BASE_URL=http://localhost:11434
   ```

5. **Test the configuration**:
   ```bash
   pixi run python main.py test-config
   ```

**Note**: No API key is required for local providers like Ollama. Cloud providers (OpenAI, Anthropic, etc.) require API keys.

## Configuration Commands

### Show Current Configuration

```bash
pixi run python main.py config --show
```

### Show Environment Variables

```bash
pixi run python main.py config --env
```

### Validate Configuration

```bash
pixi run python main.py config --validate
```

### Export as Environment Variables

```bash
pixi run python main.py config --export
```

### Set Configuration Values

```bash
# Set LLM API key
pixi run python main.py set-config llm_api_key sk-your-api-key-here

# Set LLM model
pixi run python main.py set-config llm_model gpt-4

# Set LLM temperature
pixi run python main.py set-config llm_temperature 0.2

# Set output directory
pixi run python main.py set-config output_dir ./custom_tests

# Set max iterations
pixi run python main.py set-config max_iterations 10
```

### Reset to Defaults

```bash
pixi run python main.py config --reset
```

## Testing Configuration

Use the test-config command to validate your configuration:

```bash
pixi run python main.py test-config
```

This command will:
- Test configuration loading
- Validate configuration values
- Check environment variables
- Test LLM configuration
- Verify file system access
- Show configuration priority

## Configuration Validation Rules

The following validation rules are applied to configuration values:

- **max_iterations**: Must be a positive integer
- **llm_temperature**: Must be between 0.0 and 2.0
- **llm_max_tokens**: Must be a positive integer
- **output_dir**: Must be a valid path
- **log_level**: Must be one of DEBUG, INFO, WARNING, ERROR, CRITICAL

## Security Considerations

### API Key Security

- **Never commit API keys to version control**
- Use environment variables for API keys in production
- The `--show` command masks API keys for security
- Consider using a secrets management system for production deployments

### Configuration File Permissions

- The configuration file is created with default permissions
- Consider restricting access to the configuration file:
  ```bash
  chmod 600 ~/.elenchus/config.yaml
  ```

## Troubleshooting

### Configuration Not Loading

1. Check if the configuration file exists:
   ```bash
   ls -la ~/.elenchus/config.yaml
   ```

2. Verify file permissions:
   ```bash
   ls -la ~/.elenchus/
   ```

3. Check for syntax errors in the YAML file:
   ```bash
   python -c "import yaml; yaml.safe_load(open('~/.elenchus/config.yaml'))"
   ```

### Environment Variables Not Working

1. Verify the environment variable is set:
   ```bash
   echo $ELENCHUS_LLM_API_KEY
   ```

2. Check if the .env file is being loaded:
   ```bash
   ls -la .env
   ```

3. Ensure the environment variable name matches exactly (case-sensitive)

### Validation Errors

1. Run the validation command to see specific errors:
   ```bash
   pixi run python main.py config --validate
   ```

2. Check the configuration values against the validation rules above

3. Use the test-config command for comprehensive testing:
   ```bash
   pixi run python main.py test-config
   ```

## Examples

### Basic Setup

1. Set your API key:
   ```bash
   pixi run python main.py set-config llm_api_key sk-your-key-here
   ```

2. Verify configuration:
   ```bash
   pixi run python main.py test-config
   ```

3. Start using Elenchus:
   ```bash
   pixi run python main.py extract
   ```

### Generate Tests

Use the generator with optional execution, coverage, limits, and single-file mode:

```bash
# Generate tests for the whole HumanEval directory
pixi run python main.py generate-tests --input-dir HumanEval --output-dir generated_tests

# Run each generated test and print pass/fail
pixi run python main.py generate-tests --input-dir HumanEval --output-dir generated_tests --run

# Measure line coverage (prints just the percent in CLI when available)
pixi run python main.py generate-tests --input-dir HumanEval --output-dir generated_tests --run --coverage

# Process only the first N PUTs
pixi run python main.py generate-tests --input-dir HumanEval --output-dir generated_tests --run --coverage --limit 5

# Process a single file by path
pixi run python main.py generate-tests --file HumanEval/he_4.py --output-dir generated_tests --run --coverage

# Increase or decrease iteration attempts used for syntax fixes and failing tests
pixi run python main.py generate-tests --max-iterations 3 --run --coverage -n 3
```

Notes:
- Coverage is reported inline in the CLI when tests pass (e.g., `cov: 92.00%`).
- When coverage is enabled but tests fail or the generated code is invalid, the CLI shows `cov: n/a` to avoid misleading values.

### Production Setup

1. Create a .env file with your configuration:
   ```bash
   cat > .env << EOF
   ELENCHUS_LLM_API_KEY=sk-your-production-key
   ELENCHUS_LLM_MODEL=gpt-4
   ELENCHUS_OUTPUT_DIR=/var/elenchus/tests
   ELENCHUS_LOG_LEVEL=INFO
   ELENCHUS_LOG_FILE=/var/log/elenchus.log
   EOF
   ```

2. Test the configuration:
   ```bash
   pixi run python main.py test-config
   ```

3. Export environment variables for your deployment:
   ```bash
   pixi run python main.py config --export > production.env
   ```

### Development Setup

1. Use a development API key:
   ```bash
   export ELENCHUS_LLM_API_KEY=sk-dev-key
   export ELENCHUS_LLM_MODEL=gpt-3.5-turbo
   export ELENCHUS_LOG_LEVEL=DEBUG
   ```

2. Test with verbose logging:
   ```bash
   pixi run python main.py test-config
   pixi run python main.py extract --verbose
   ``` 