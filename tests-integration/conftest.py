"""
Shared fixtures and configuration for integration tests.

These tests require a valid DEEPL_API_KEY environment variable.
They make real API calls to DeepL and should not be run in CI without proper setup.
"""

import os

import pytest
import pytest_asyncio
from dotenv import load_dotenv

from mcp_deepl.api_client import DeepLClient

load_dotenv()


def pytest_configure(config):
    """Check for required environment variables before running tests."""
    if not os.environ.get("DEEPL_API_KEY"):
        pytest.exit(
            "ERROR: DEEPL_API_KEY environment variable is required.\n"
            "Set it in .env or export before running integration tests:\n"
            "  export DEEPL_API_KEY=your_key_here\n"
            "  make test-integration"
        )


@pytest.fixture
def api_key() -> str:
    """Get the DeepL API key from environment."""
    key = os.environ.get("DEEPL_API_KEY")
    if not key:
        pytest.skip("DEEPL_API_KEY not set")
    return key


@pytest_asyncio.fixture
async def client(api_key: str) -> DeepLClient:
    """Create a DeepL client for testing."""
    client = DeepLClient(api_token=api_key)
    yield client
    await client.close()
