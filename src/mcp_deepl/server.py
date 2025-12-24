"""FastMCP server for DeepL Translation API."""

import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import Context, FastMCP
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

# Create MCP server
mcp = FastMCP("DeepL")

# Global client instance
_client: DeepLClient | None = None


def get_client() -> DeepLClient:
    """Get or create the API client instance."""
    global _client
    if _client is None:
        api_token = os.environ.get("DEEPL_API_KEY")
        if not api_token:
            error_msg = "DEEPL_API_KEY is not set - API calls will fail"
            raise ValueError(error_msg)
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
    ctx: Context | None = None,
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
        ctx: MCP context

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
        if ctx:
            await ctx.error(f"Translation error: {e.message}")
        raise


@mcp.tool()
async def translate_with_glossary(
    text: str | list[str],
    target_lang: str,
    glossary_id: str,
    source_lang: str | None = None,
    formality: str | None = None,
    ctx: Context | None = None,
) -> TranslationResponse:
    """Translate using a custom glossary.

    Args:
        text: Text to translate
        target_lang: Target language code
        glossary_id: Glossary ID to use
        source_lang: Source language code (optional)
        formality: Formality level
        ctx: MCP context

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
        if ctx:
            await ctx.error(f"Translation error: {e.message}")
        raise


# MCP Tools - Language Detection and Info


@mcp.tool()
async def detect_language(
    text: str,
    ctx: Context | None = None,
) -> LanguageDetectionResponse:
    """Detect the language of text.

    Args:
        text: Text to detect language for
        ctx: MCP context

    Returns:
        Detected language information
    """
    client = get_client()
    try:
        return await client.detect_language(text)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Language detection error: {e.message}")
        raise


@mcp.tool()
async def list_languages(
    language_type: str = "target",
    ctx: Context | None = None,
) -> LanguagesResponse:
    """List all supported source and target languages.

    Args:
        language_type: Type of languages to list (source or target)
        ctx: MCP context

    Returns:
        List of supported languages
    """
    client = get_client()
    try:
        return await client.list_languages(language_type)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error listing languages: {e.message}")
        raise


# MCP Tools - Usage


@mcp.tool()
async def get_usage(
    ctx: Context | None = None,
) -> UsageResponse:
    """Get API usage statistics.

    Args:
        ctx: MCP context

    Returns:
        Usage statistics
    """
    client = get_client()
    try:
        return await client.get_usage()
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error getting usage: {e.message}")
        raise


# MCP Tools - Glossaries


@mcp.tool()
async def list_glossaries(
    ctx: Context | None = None,
) -> GlossariesResponse:
    """List custom glossaries.

    Args:
        ctx: MCP context

    Returns:
        List of glossaries
    """
    client = get_client()
    try:
        return await client.list_glossaries()
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error listing glossaries: {e.message}")
        raise


@mcp.tool()
async def create_glossary(
    name: str,
    source_lang: str,
    target_lang: str,
    entries: dict[str, str],
    entries_format: str = "tsv",
    ctx: Context | None = None,
) -> Glossary:
    """Create a custom glossary for consistent translations.

    Args:
        name: Glossary name
        source_lang: Source language code
        target_lang: Target language code
        entries: Dictionary of source:target translations
        entries_format: Format (tsv or csv)
        ctx: MCP context

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
        if ctx:
            await ctx.error(f"Error creating glossary: {e.message}")
        raise


@mcp.tool()
async def get_glossary(
    glossary_id: str,
    ctx: Context | None = None,
) -> Glossary:
    """Get glossary details.

    Args:
        glossary_id: Glossary ID
        ctx: MCP context

    Returns:
        Glossary information
    """
    client = get_client()
    try:
        return await client.get_glossary(glossary_id)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error getting glossary: {e.message}")
        raise


@mcp.tool()
async def delete_glossary(
    glossary_id: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Delete a glossary.

    Args:
        glossary_id: Glossary ID
        ctx: MCP context

    Returns:
        Success confirmation
    """
    client = get_client()
    try:
        return await client.delete_glossary(glossary_id)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error deleting glossary: {e.message}")
        raise


# MCP Tools - Document Translation


@mcp.tool()
async def translate_document(
    document_path: str,
    target_lang: str,
    source_lang: str | None = None,
    formality: str | None = None,
    filename: str | None = None,
    ctx: Context | None = None,
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
        ctx: MCP context

    Returns:
        Document ID and key for status checking
    """
    if ctx:
        await ctx.warning(
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
    ctx: Context | None = None,
) -> DocumentStatusResponse:
    """Check document translation status.

    Args:
        document_id: Document ID from upload
        document_key: Document key from upload
        ctx: MCP context

    Returns:
        Document status information
    """
    client = get_client()
    try:
        return await client.get_document_status(document_id, document_key)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error getting document status: {e.message}")
        raise


@mcp.tool()
async def download_translated_document(
    document_id: str,
    document_key: str,
    ctx: Context | None = None,
) -> DocumentDownloadResponse:
    """Download completed document translation.

    Args:
        document_id: Document ID
        document_key: Document key
        ctx: MCP context

    Returns:
        Document download information
    """
    client = get_client()
    try:
        return await client.download_translated_document(document_id, document_key)
    except DeepLAPIError as e:
        if ctx:
            await ctx.error(f"Error downloading document: {e.message}")
        raise


# Create ASGI application for deployment
app = mcp.http_app()
