# MCP Server DeepL

Production-ready MCP server for DeepL Translation API with comprehensive tooling, type safety, and enterprise-grade architecture.

## Features

- **Official Client**: Built on the official `deepl-python` library for reliability
- **Full API Coverage**: Complete implementation of DeepL API (translation, glossaries, usage tracking)
- **Strongly Typed**: All responses use Pydantic models for type safety
- **Dual Transport**: Supports both stdio and HTTP (streamable-http) modes
- **Async/Await**: Async wrapper for seamless MCP integration
- **Type Safe**: Full mypy strict mode compliance
- **Production Ready**: Docker support, comprehensive tests, CI/CD pipeline
- **Developer Friendly**: Makefile commands, auto-formatting, fast feedback
- **High-Quality Translation**: Superior to Google Translate in quality
- **30+ Languages**: European and Asian languages
- **Document Translation**: PDF, DOCX, PPTX, XLSX, HTML, TXT
- **Custom Glossaries**: Consistent terminology across translations
- **Formality Control**: Formal/informal tone for supported languages

## Architecture

This server follows S-Tier MCP Server Architecture:

```
src/mcp_deepl/
├── __init__.py         # Package initialization
├── server.py           # FastMCP server with tool definitions
├── api_client.py       # Async wrapper around official DeepL Python client
└── api_models.py       # Pydantic models for type safety

tests/                  # Unit tests with pytest + AsyncMock
e2e/                    # End-to-end Docker integration tests
```

**Key Implementation Details:**
- Uses the official `deepl-python` library for reliable API communication
- Wraps the official client with async methods for MCP compatibility
- Maintains full type safety with Pydantic models
- Supports all DeepL API features including glossaries and document translation

## Installation

### Using uv (recommended)

```bash
# Install package
uv pip install -e .

# Install with dev dependencies
uv pip install -e . --group dev
```

### Traditional pip

```bash
pip install -e .
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your DeepL API key:

```bash
DEEPL_API_KEY=your_api_key_here
```

**How to get credentials:**

1. Go to [deepl.com/pro-api](https://www.deepl.com/pro-api)
2. Sign up for an account (Free or Pro)
3. Go to Account Settings
4. Find your API key under "Authentication Key for DeepL API"
5. Copy the key and store as `DEEPL_API_KEY`

**API Key Format:**

- Free tier keys end with `:fx` (e.g., `abc123:fx`)
- Pro keys do not have the `:fx` suffix
- The server automatically detects which endpoint to use

The `.env` file is automatically loaded when the server starts.

## Running the Server

### Stdio Mode (for Claude Desktop)

```bash
make run-stdio
# or
uv run fastmcp run src/mcp_deepl/server.py
```

### HTTP Mode

```bash
make run-http
# or
uv run uvicorn mcp_deepl.server:app --host 0.0.0.0 --port 8000

# Test the server is running
make test-http
```

### Docker

```bash
# Build image locally
make docker-build

# Build and push multi-platform image (amd64 + arm64)
make release VERSION=1.0.0

# Run container
make docker-run
```

## Claude Desktop Configuration

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

### Option 1: HTTP Mode (Recommended)

First, start the HTTP server:

```bash
make run-http
```

Then add this to your Claude Desktop config:

```json
{
  "mcpServers": {
    "deepl": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "http://localhost:8000/mcp"
      ]
    }
  }
}
```

**Benefits**: Better performance, easier debugging, can be deployed remotely

### Option 2: Stdio Mode

```json
{
  "mcpServers": {
    "deepl": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/mcp-deepl",
        "run",
        "fastmcp",
        "run",
        "src/mcp_deepl/server.py"
      ]
    }
  }
}
```

## Available MCP Tools

### Text Translation

- `translate_text(text, target_lang, ...)` - Translate text between languages
- `translate_with_glossary(text, target_lang, glossary_id, ...)` - Translate using custom glossary

### Language Detection and Info

- `detect_language(text)` - Detect the language of text
- `list_languages(language_type)` - List all supported languages

### Usage Tracking

- `get_usage()` - Get API usage statistics

### Glossaries

- `list_glossaries()` - List custom glossaries
- `create_glossary(name, source_lang, target_lang, entries)` - Create custom glossary
- `get_glossary(glossary_id)` - Get glossary details
- `delete_glossary(glossary_id)` - Delete a glossary

### Document Translation

- `translate_document(document_path, target_lang, ...)` - Translate entire documents
- `get_document_status(document_id, document_key)` - Check translation status
- `download_translated_document(document_id, document_key)` - Download translated document

## Development

### Quick Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make dev-install   # Install with dev dependencies
make format        # Format code with ruff
make lint          # Lint code with ruff
make typecheck     # Type check with mypy
make test          # Run tests with pytest
make test-cov      # Run tests with coverage
make test-e2e      # Run E2E Docker tests (requires Docker)
make test-http     # Test HTTP server is running
make check         # Run all checks (lint + typecheck + test)
make clean         # Clean up artifacts
make all           # Full workflow (clean + install + format + check)
```

### Running Tests

```bash
# Run unit tests
make test

# Run with coverage report
make test-cov

# Run E2E Docker tests (requires Docker, not run in CI)
make test-e2e

# Run specific test file
uv run pytest tests/test_server.py -v
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Fix linting issues automatically
make lint-fix

# Type check
make typecheck

# Run all checks
make check
```

### Docker Commands

```bash
# Build local image
make docker-build

# Build and push multi-platform image
make release VERSION=1.0.0

# Run container
make docker-run
```

**Multi-Platform Build Setup** (first time only):

```bash
# Create and use a new buildx builder
docker buildx create --name multiplatform --use

# Verify the builder
docker buildx inspect --bootstrap
```

The `release` command builds for both `linux/amd64` and `linux/arm64` architectures and pushes directly to your container registry.

## Health Check & Troubleshooting

The server exposes a health check endpoint at `/health`:

```bash
curl http://localhost:8000/health
# {"status":"healthy","service":"mcp-deepl"}

# Or use the Makefile command
make test-http
```

### Troubleshooting HTTP Mode

If Claude Desktop can't connect to the server:

1. **Check server is running**: `make test-http`
2. **Verify port**: Ensure port 8000 is not in use by another service
3. **Check logs**: Look at the server output for any errors
4. **Test MCP endpoint**: `curl http://localhost:8000/` should return MCP protocol info
5. **Verify .env**: Ensure `DEEPL_API_KEY` is set in your `.env` file

### Changing the Port

To use a different port (e.g., 9000):

```bash
uv run uvicorn mcp_deepl.server:app --host 0.0.0.0 --port 9000
```

Then update your Claude Desktop config to use `http://localhost:9000/mcp`

## Rate Limits

**Free Tier:**

- 500,000 characters per month
- Suitable for testing and small projects

**Pro Plans:**

- Unlimited characters based on plan
- Higher priority processing
- Additional features

Monitor usage with `get_usage()` tool.

## Supported Languages

**European Languages:**
Bulgarian (BG), Czech (CS), Danish (DA), German (DE), Greek (EL), English (EN), Spanish (ES), Estonian (ET), Finnish (FI), French (FR), Hungarian (HU), Indonesian (ID), Italian (IT), Lithuanian (LT), Latvian (LV), Dutch (NL), Polish (PL), Portuguese (PT), Romanian (RO), Russian (RU), Slovak (SK), Slovenian (SL), Swedish (SV), Turkish (TR), Ukrainian (UK)

**Asian Languages:**
Chinese (ZH), Japanese (JA), Korean (KO)

## Example Usage

### Simple Translation

```python
# Translate text
result = await translate_text(
    text="Hello, world!",
    target_lang="DE"
)

# With formality control
result = await translate_text(
    text="How are you?",
    target_lang="DE",
    formality="more"  # Formal German
)
```

### Using Glossaries

```python
# Create glossary for consistent terminology
glossary = await create_glossary(
    name="Product Terms",
    source_lang="EN",
    target_lang="DE",
    entries={
        "smartphone": "Smartphone",
        "tablet": "Tablet-PC",
        "app": "App"
    }
)

# Translate using glossary
result = await translate_with_glossary(
    text="Our new smartphone app",
    target_lang="DE",
    glossary_id=glossary.glossary_id
)
```

### Language Detection

```python
# Detect language
result = await detect_language(text="Bonjour le monde")
# Returns: {"detected_language": "FR", ...}
```

## Requirements

- Python 3.13+
- deepl (official DeepL Python client)
- fastapi
- fastmcp
- pydantic
- python-dotenv
- uvicorn

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT

## API Documentation

- [DeepL API Documentation](https://www.deepl.com/docs-api)
- [Text Translation](https://www.deepl.com/docs-api/translate-text/)
- [Document Translation](https://www.deepl.com/docs-api/translate-documents/)
- [Glossaries](https://www.deepl.com/docs-api/glossaries/)
