"""Unit tests for the MCP server tools."""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp import Client

from mcp_deepl.api_models import (
    DocumentDownloadResponse,
    DocumentStatusResponse,
    GlossariesResponse,
    Glossary,
    LanguageDetectionResponse,
    LanguagesResponse,
    TranslationResponse,
    UsageResponse,
)
from mcp_deepl.server import SKILL_CONTENT, mcp


@pytest.fixture
def mcp_server():
    """Return the MCP server instance."""
    return mcp


EXPECTED_TOOLS = {
    "translate_text",
    "translate_with_glossary",
    "detect_language",
    "list_languages",
    "get_usage",
    "list_glossaries",
    "create_glossary",
    "get_glossary",
    "delete_glossary",
    "translate_document",
    "get_document_status",
    "download_translated_document",
}


class TestSkillResource:
    """Test the skill resource and server instructions."""

    @pytest.mark.asyncio
    async def test_initialize_returns_instructions(self, mcp_server):
        """Server instructions reference the skill resource."""
        async with Client(mcp_server) as client:
            result = await client.initialize()
            assert result.instructions is not None
            assert "skill://deepl/usage" in result.instructions

    @pytest.mark.asyncio
    async def test_skill_resource_listed(self, mcp_server):
        """skill://deepl/usage appears in resource listing."""
        async with Client(mcp_server) as client:
            resources = await client.list_resources()
            uris = [str(r.uri) for r in resources]
            assert "skill://deepl/usage" in uris

    @pytest.mark.asyncio
    async def test_skill_resource_readable(self, mcp_server):
        """Reading the skill resource returns the full skill content."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://deepl/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert "Tool Selection" in text
            assert "translate_text" in text
            assert "Language Codes" in text

    @pytest.mark.asyncio
    async def test_skill_content_matches_constant(self, mcp_server):
        """Resource content matches the SKILL_CONTENT constant."""
        async with Client(mcp_server) as client:
            contents = await client.read_resource("skill://deepl/usage")
            text = contents[0].text if hasattr(contents[0], "text") else str(contents[0])
            assert text == SKILL_CONTENT


class TestMCPTools:
    """Test the MCP server tools."""

    @pytest.mark.asyncio
    async def test_tools_list(self, mcp_server):
        """Verify all 12 tools are registered with schemas."""
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert EXPECTED_TOOLS == tool_names
            for tool in tools:
                assert tool.description
                assert tool.inputSchema

    @pytest.mark.asyncio
    async def test_translate_text(self, mcp_server):
        """Test translate_text tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.translate_text.return_value = TranslationResponse(
                translations=[{"detected_source_language": "EN", "text": "Hallo Welt"}]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "translate_text", {"text": "Hello world", "target_lang": "DE"}
                )

            assert result is not None
            mock_client.translate_text.assert_called_once_with(
                text="Hello world",
                target_lang="DE",
                source_lang=None,
                formality=None,
                preserve_formatting=False,
                tag_handling=None,
                split_sentences="1",
            )

    @pytest.mark.asyncio
    async def test_translate_text_with_options(self, mcp_server):
        """Test translate_text with formality, preserve_formatting, tag_handling."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.translate_text.return_value = TranslationResponse(
                translations=[{"detected_source_language": "EN", "text": "Hallo Welt"}]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "translate_text",
                    {
                        "text": "Hello world",
                        "target_lang": "DE",
                        "formality": "more",
                        "preserve_formatting": True,
                        "tag_handling": "html",
                    },
                )

            assert result is not None
            mock_client.translate_text.assert_called_once_with(
                text="Hello world",
                target_lang="DE",
                source_lang=None,
                formality="more",
                preserve_formatting=True,
                tag_handling="html",
                split_sentences="1",
            )

    @pytest.mark.asyncio
    async def test_translate_with_glossary(self, mcp_server):
        """Test translate_with_glossary tool passes glossary_id through."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.translate_with_glossary.return_value = TranslationResponse(
                translations=[{"detected_source_language": "EN", "text": "Smartphone App"}]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "translate_with_glossary",
                    {
                        "text": "smartphone app",
                        "target_lang": "DE",
                        "glossary_id": "gl-123",
                    },
                )

            assert result is not None
            mock_client.translate_with_glossary.assert_called_once_with(
                text="smartphone app",
                target_lang="DE",
                glossary_id="gl-123",
                source_lang=None,
                formality=None,
            )

    @pytest.mark.asyncio
    async def test_detect_language(self, mcp_server):
        """Test detect_language tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.detect_language.return_value = LanguageDetectionResponse(
                detected_language="FR", text="Bonjour le monde"
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("detect_language", {"text": "Bonjour le monde"})

            assert result is not None
            mock_client.detect_language.assert_called_once_with("Bonjour le monde")

    @pytest.mark.asyncio
    async def test_list_languages(self, mcp_server):
        """Test list_languages tool with default (target) type."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.list_languages.return_value = LanguagesResponse(
                languages=[
                    {"language": "DE", "name": "German", "supports_formality": True},
                    {"language": "FR", "name": "French", "supports_formality": True},
                ]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("list_languages", {})

            assert result is not None
            mock_client.list_languages.assert_called_once_with("target")

    @pytest.mark.asyncio
    async def test_list_languages_source(self, mcp_server):
        """Test list_languages tool with source type."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.list_languages.return_value = LanguagesResponse(
                languages=[
                    {"language": "EN", "name": "English", "supports_formality": None},
                ]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("list_languages", {"language_type": "source"})

            assert result is not None
            mock_client.list_languages.assert_called_once_with("source")

    @pytest.mark.asyncio
    async def test_get_usage(self, mcp_server):
        """Test get_usage tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.get_usage.return_value = UsageResponse(
                character_count=123456, character_limit=500000
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("get_usage", {})

            assert result is not None
            mock_client.get_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_glossaries(self, mcp_server):
        """Test list_glossaries tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.list_glossaries.return_value = GlossariesResponse(
                glossaries=[
                    Glossary(
                        glossary_id="gl-1",
                        name="Test",
                        ready=True,
                        source_lang="EN",
                        target_lang="DE",
                        creation_time="2025-01-01T00:00:00",
                        entry_count=5,
                    )
                ]
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("list_glossaries", {})

            assert result is not None
            mock_client.list_glossaries.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_glossary(self, mcp_server):
        """Test create_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.create_glossary.return_value = Glossary(
                glossary_id="gl-new",
                name="New Glossary",
                ready=True,
                source_lang="EN",
                target_lang="DE",
                creation_time="2025-01-01T00:00:00",
                entry_count=2,
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "create_glossary",
                    {
                        "name": "New Glossary",
                        "source_lang": "EN",
                        "target_lang": "DE",
                        "entries": {"app": "App", "cloud": "Cloud"},
                    },
                )

            assert result is not None
            mock_client.create_glossary.assert_called_once_with(
                name="New Glossary",
                source_lang="EN",
                target_lang="DE",
                entries={"app": "App", "cloud": "Cloud"},
                entries_format="tsv",
            )

    @pytest.mark.asyncio
    async def test_get_glossary(self, mcp_server):
        """Test get_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.get_glossary.return_value = Glossary(
                glossary_id="gl-1",
                name="Test",
                ready=True,
                source_lang="EN",
                target_lang="DE",
                creation_time="2025-01-01T00:00:00",
                entry_count=5,
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool("get_glossary", {"glossary_id": "gl-1"})

            assert result is not None
            mock_client.get_glossary.assert_called_once_with("gl-1")

    @pytest.mark.asyncio
    async def test_delete_glossary(self, mcp_server):
        """Test delete_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.delete_glossary.return_value = {
                "success": True,
                "glossary_id": "gl-1",
            }

            async with Client(mcp_server) as client:
                result = await client.call_tool("delete_glossary", {"glossary_id": "gl-1"})

            assert result is not None
            mock_client.delete_glossary.assert_called_once_with("gl-1")

    @pytest.mark.asyncio
    async def test_translate_document(self, mcp_server):
        """Test translate_document tool returns placeholder."""
        async with Client(mcp_server) as client:
            result = await client.call_tool(
                "translate_document",
                {"document_path": "/tmp/doc.pdf", "target_lang": "DE"},
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_document_status(self, mcp_server):
        """Test get_document_status tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.get_document_status.return_value = DocumentStatusResponse(
                document_id="doc-1",
                status="done",
                billed_characters=500,
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "get_document_status",
                    {"document_id": "doc-1", "document_key": "key-1"},
                )

            assert result is not None
            mock_client.get_document_status.assert_called_once_with("doc-1", "key-1")

    @pytest.mark.asyncio
    async def test_download_translated_document(self, mcp_server):
        """Test download_translated_document tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.download_translated_document.return_value = DocumentDownloadResponse(
                success=True,
                document_id="doc-1",
                content_type="application/pdf",
                size=1024,
                note="Downloaded",
            )

            async with Client(mcp_server) as client:
                result = await client.call_tool(
                    "download_translated_document",
                    {"document_id": "doc-1", "document_key": "key-1"},
                )

            assert result is not None
            mock_client.download_translated_document.assert_called_once_with("doc-1", "key-1")
