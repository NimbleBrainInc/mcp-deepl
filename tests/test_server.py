"""Unit tests for the MCP server tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context

from mcp_deepl.api_models import (
    GlossariesResponse,
    Glossary,
    Language,
    LanguageDetectionResponse,
    LanguagesResponse,
    Translation,
    TranslationResponse,
    UsageResponse,
)
from mcp_deepl.server import (
    create_glossary,
    delete_glossary,
    detect_language,
    get_glossary,
    get_usage,
    list_glossaries,
    list_languages,
    translate_text,
    translate_with_glossary,
)


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock MCP context."""
    ctx = MagicMock(spec=Context)
    ctx.warning = MagicMock()
    ctx.error = MagicMock()
    return ctx


class TestTranslationTools:
    """Test the translation tools."""

    @pytest.mark.asyncio
    async def test_translate_text(self, mock_context: MagicMock) -> None:
        """Test translate_text tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.translate_text.return_value = TranslationResponse(
                translations=[Translation(detected_source_language="EN", text="Hallo Welt")]
            )

            result = await translate_text(text="Hello world", target_lang="DE", ctx=mock_context)

            assert result.translations[0].text == "Hallo Welt"
            assert result.translations[0].detected_source_language == "EN"
            mock_client.translate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_translate_with_glossary(self, mock_context: MagicMock) -> None:
        """Test translate_with_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.translate_with_glossary.return_value = TranslationResponse(
                translations=[Translation(text="Smartphone App")]
            )

            result = await translate_with_glossary(
                text="smartphone app",
                target_lang="DE",
                glossary_id="test-glossary",
                ctx=mock_context,
            )

            assert result.translations[0].text == "Smartphone App"
            mock_client.translate_with_glossary.assert_called_once_with(
                text="smartphone app",
                target_lang="DE",
                glossary_id="test-glossary",
                source_lang=None,
                formality=None,
            )


class TestLanguageTools:
    """Test the language detection and listing tools."""

    @pytest.mark.asyncio
    async def test_detect_language(self, mock_context: MagicMock) -> None:
        """Test detect_language tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.detect_language.return_value = LanguageDetectionResponse(
                detected_language="FR", text="Bonjour le monde"
            )

            result = await detect_language(text="Bonjour le monde", ctx=mock_context)

            assert result.detected_language == "FR"
            assert result.text == "Bonjour le monde"
            mock_client.detect_language.assert_called_once_with("Bonjour le monde")

    @pytest.mark.asyncio
    async def test_list_languages(self, mock_context: MagicMock) -> None:
        """Test list_languages tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.list_languages.return_value = LanguagesResponse(
                languages=[
                    Language(language="DE", name="German", supports_formality=True),
                    Language(language="FR", name="French", supports_formality=True),
                ]
            )

            result = await list_languages(language_type="target", ctx=mock_context)

            assert len(result.languages) == 2
            assert result.languages[0].language == "DE"
            assert result.languages[0].supports_formality is True
            mock_client.list_languages.assert_called_once_with("target")


class TestUsageTools:
    """Test the usage tracking tools."""

    @pytest.mark.asyncio
    async def test_get_usage(self, mock_context: MagicMock) -> None:
        """Test get_usage tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.get_usage.return_value = UsageResponse(
                character_count=123456, character_limit=500000
            )

            result = await get_usage(ctx=mock_context)

            assert result.character_count == 123456
            assert result.character_limit == 500000
            mock_client.get_usage.assert_called_once()


class TestGlossaryTools:
    """Test the glossary management tools."""

    @pytest.mark.asyncio
    async def test_list_glossaries(self, mock_context: MagicMock) -> None:
        """Test list_glossaries tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.list_glossaries.return_value = GlossariesResponse(
                glossaries=[
                    Glossary(
                        glossary_id="test-1",
                        name="Test Glossary",
                        ready=True,
                        source_lang="EN",
                        target_lang="DE",
                        creation_time="2025-10-14T12:00:00",
                        entry_count=10,
                    )
                ]
            )

            result = await list_glossaries(ctx=mock_context)

            assert len(result.glossaries) == 1
            assert result.glossaries[0].glossary_id == "test-1"
            assert result.glossaries[0].entry_count == 10
            mock_client.list_glossaries.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_glossary(self, mock_context: MagicMock) -> None:
        """Test create_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.create_glossary.return_value = Glossary(
                glossary_id="new-glossary",
                name="Product Terms",
                ready=True,
                source_lang="EN",
                target_lang="DE",
                creation_time="2025-10-14T12:00:00",
                entry_count=3,
            )

            result = await create_glossary(
                name="Product Terms",
                source_lang="EN",
                target_lang="DE",
                entries={"app": "App", "cloud": "Cloud"},
                ctx=mock_context,
            )

            assert result.glossary_id == "new-glossary"
            assert result.entry_count == 3
            mock_client.create_glossary.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_glossary(self, mock_context: MagicMock) -> None:
        """Test get_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.get_glossary.return_value = Glossary(
                glossary_id="test-1",
                name="Test Glossary",
                ready=True,
                source_lang="EN",
                target_lang="DE",
                creation_time="2025-10-14T12:00:00",
                entry_count=10,
            )

            result = await get_glossary(glossary_id="test-1", ctx=mock_context)

            assert result.glossary_id == "test-1"
            mock_client.get_glossary.assert_called_once_with("test-1")

    @pytest.mark.asyncio
    async def test_delete_glossary(self, mock_context: MagicMock) -> None:
        """Test delete_glossary tool."""
        with patch("mcp_deepl.server.get_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            mock_client.delete_glossary.return_value = {
                "success": True,
                "glossary_id": "test-1",
            }

            result = await delete_glossary(glossary_id="test-1", ctx=mock_context)

            assert result["success"] is True
            assert result["glossary_id"] == "test-1"
            mock_client.delete_glossary.assert_called_once_with("test-1")
