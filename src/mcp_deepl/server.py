"""FastMCP server for DeepL Translation API."""

import logging
import os
import sys
from importlib.resources import files
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from starlette.requests import Request
from starlette.responses import JSONResponse

from .api_client import DeepLAPIError, DeepLClient
from .api_models import (
    DocumentDownloadResponse,
    DocumentStatusResponse,
    GlossariesResponse,
    Glossary,
    LanguageDetectionResponse,
    LanguagesResponse,
    TranslationResponse,
    UsageResponse,
)

# Load environment variables from .env file
load_dotenv()

# Diagnostics go to stderr (stdout carries JSON-RPC), never to the client: MCP's logging
# capability is deprecated as of the 2026-07-28 protocol (SEP-2577). A failure the caller
# must see is raised as a ToolError.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp_deepl")

# Create MCP server
mcp = FastMCP(
    "DeepL",
    instructions=(
        "Before using DeepL tools, read the skill://deepl/usage resource "
        "for tool selection guidance and language code conventions."
    ),
)

# Load skill content from package data
SKILL_CONTENT = files("mcp_deepl").joinpath("SKILL.md").read_text()


@mcp.resource("skill://deepl/usage")
def deepl_skill() -> str:
    """How to effectively use DeepL tools: tool selection, language codes, glossary workflow."""
    return SKILL_CONTENT


# Global client instance
_client: DeepLClient | None = None


def get_client() -> DeepLClient:
    """Get or create the API client instance."""
    global _client
    if _client is None:
        api_token = os.environ.get("DEEPL_API_KEY")
        if not api_token:
            logger.error("DEEPL_API_KEY is not set")
            raise ToolError("DEEPL_API_KEY environment variable is required")
        _client = DeepLClient(api_token=api_token)
    return _client


# Health endpoint for HTTP transport
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint for monitoring."""
    return JSONResponse({"status": "healthy", "service": "mcp-deepl"})


# MCP Tools - Text Translation


@mcp.tool()
async def translate_text(
    text: str | list[str],
    target_lang: str,
    source_lang: str | None = None,
    formality: str | None = None,
    preserve_formatting: bool = False,
    tag_handling: str | None = None,
    split_sentences: str = "1",
) -> TranslationResponse:
    """Translate text between languages.

    Args:
        text: Text to translate (string or list of strings)
        target_lang: Target language code (e.g., "DE", "FR", "ES")
        source_lang: Source language code (optional, auto-detect if not provided)
        formality: Formality level (default, more, less, prefer_more, prefer_less)
        preserve_formatting: Preserve formatting (default: false)
        tag_handling: Tag handling mode (xml, html)
        split_sentences: Split sentences (0=none, 1=default, nonewlines=no newlines)

    Returns:
        Translation response with translated text
    """
    client = get_client()
    try:
        return await client.translate_text(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            formality=formality,
            preserve_formatting=preserve_formatting,
            tag_handling=tag_handling,
            split_sentences=split_sentences,
        )
    except DeepLAPIError as e:
        logger.warning("Translation error: %s", e.message)
        raise ToolError(f"Translation error: {e.message}") from e


@mcp.tool()
async def translate_with_glossary(
    text: str | list[str],
    target_lang: str,
    glossary_id: str,
    source_lang: str | None = None,
    formality: str | None = None,
) -> TranslationResponse:
    """Translate using a custom glossary.

    Args:
        text: Text to translate
        target_lang: Target language code
        glossary_id: Glossary ID to use
        source_lang: Source language code (optional)
        formality: Formality level

    Returns:
        Translation response
    """
    client = get_client()
    try:
        return await client.translate_with_glossary(
            text=text,
            target_lang=target_lang,
            glossary_id=glossary_id,
            source_lang=source_lang,
            formality=formality,
        )
    except DeepLAPIError as e:
        logger.warning("Translation error: %s", e.message)
        raise ToolError(f"Translation error: {e.message}") from e


# MCP Tools - Language Detection and Info


@mcp.tool()
async def detect_language(
    text: str,
) -> LanguageDetectionResponse:
    """Detect the language of text.

    Args:
        text: Text to detect language for

    Returns:
        Detected language information
    """
    client = get_client()
    try:
        return await client.detect_language(text)
    except DeepLAPIError as e:
        logger.warning("Language detection error: %s", e.message)
        raise ToolError(f"Language detection error: {e.message}") from e


@mcp.tool()
async def list_languages(
    language_type: str = "target",
) -> LanguagesResponse:
    """List all supported source and target languages.

    Args:
        language_type: Type of languages to list (source or target)

    Returns:
        List of supported languages
    """
    client = get_client()
    try:
        return await client.list_languages(language_type)
    except DeepLAPIError as e:
        logger.warning("Error listing languages: %s", e.message)
        raise ToolError(f"Error listing languages: {e.message}") from e


# MCP Tools - Usage


@mcp.tool()
async def get_usage() -> UsageResponse:
    """Get API usage statistics.

    Args:

    Returns:
        Usage statistics
    """
    client = get_client()
    try:
        return await client.get_usage()
    except DeepLAPIError as e:
        logger.warning("Error getting usage: %s", e.message)
        raise ToolError(f"Error getting usage: {e.message}") from e


# MCP Tools - Glossaries


@mcp.tool()
async def list_glossaries() -> GlossariesResponse:
    """List custom glossaries.

    Args:

    Returns:
        List of glossaries
    """
    client = get_client()
    try:
        return await client.list_glossaries()
    except DeepLAPIError as e:
        logger.warning("Error listing glossaries: %s", e.message)
        raise ToolError(f"Error listing glossaries: {e.message}") from e


@mcp.tool()
async def create_glossary(
    name: str,
    source_lang: str,
    target_lang: str,
    entries: dict[str, str],
    entries_format: str = "tsv",
) -> Glossary:
    """Create a custom glossary for consistent translations.

    Args:
        name: Glossary name
        source_lang: Source language code
        target_lang: Target language code
        entries: Dictionary of source:target translations
        entries_format: Format (tsv or csv)

    Returns:
        Created glossary information
    """
    client = get_client()
    try:
        return await client.create_glossary(
            name=name,
            source_lang=source_lang,
            target_lang=target_lang,
            entries=entries,
            entries_format=entries_format,
        )
    except DeepLAPIError as e:
        logger.warning("Error creating glossary: %s", e.message)
        raise ToolError(f"Error creating glossary: {e.message}") from e


@mcp.tool()
async def get_glossary(
    glossary_id: str,
) -> Glossary:
    """Get glossary details.

    Args:
        glossary_id: Glossary ID

    Returns:
        Glossary information
    """
    client = get_client()
    try:
        return await client.get_glossary(glossary_id)
    except DeepLAPIError as e:
        logger.warning("Error getting glossary: %s", e.message)
        raise ToolError(f"Error getting glossary: {e.message}") from e


@mcp.tool()
async def delete_glossary(
    glossary_id: str,
) -> dict[str, Any]:
    """Delete a glossary.

    Args:
        glossary_id: Glossary ID

    Returns:
        Success confirmation
    """
    client = get_client()
    try:
        return await client.delete_glossary(glossary_id)
    except DeepLAPIError as e:
        logger.warning("Error deleting glossary: %s", e.message)
        raise ToolError(f"Error deleting glossary: {e.message}") from e


# MCP Tools - Document Translation


@mcp.tool()
async def translate_document(
    document_path: str,
    target_lang: str,
    source_lang: str | None = None,
    formality: str | None = None,
    filename: str | None = None,
) -> dict[str, str]:
    """Translate entire documents (PDF, DOCX, PPTX, etc.).

    Note: This is a simplified implementation. Document upload requires
    multipart form data handling for production use.

    Args:
        document_path: Path or URL to document
        target_lang: Target language code
        source_lang: Source language code (optional)
        formality: Formality level
        filename: Original filename (for proper format detection)

    Returns:
        Document ID and key for status checking
    """
    logger.warning(
        "Document upload is a placeholder - production implementation "
        "requires multipart form data handling"
    )
    return {
        "document_id": "placeholder_id",
        "document_key": "placeholder_key",
        "note": "Document upload implementation requires multipart form data handling",
    }


@mcp.tool()
async def get_document_status(
    document_id: str,
    document_key: str,
) -> DocumentStatusResponse:
    """Check document translation status.

    Args:
        document_id: Document ID from upload
        document_key: Document key from upload

    Returns:
        Document status information
    """
    client = get_client()
    try:
        return await client.get_document_status(document_id, document_key)
    except DeepLAPIError as e:
        logger.warning("Error getting document status: %s", e.message)
        raise ToolError(f"Error getting document status: {e.message}") from e


@mcp.tool()
async def download_translated_document(
    document_id: str,
    document_key: str,
) -> DocumentDownloadResponse:
    """Download completed document translation.

    Args:
        document_id: Document ID
        document_key: Document key

    Returns:
        Document download information
    """
    client = get_client()
    try:
        return await client.download_translated_document(document_id, document_key)
    except DeepLAPIError as e:
        logger.warning("Error downloading document: %s", e.message)
        raise ToolError(f"Error downloading document: {e.message}") from e


# Create ASGI application for deployment
app = mcp.http_app()

# Stdio entrypoint for mpak/Claude Desktop
if __name__ == "__main__":
    mcp.run()
