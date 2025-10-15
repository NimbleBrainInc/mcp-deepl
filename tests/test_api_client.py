"""Unit tests for the DeepL API client."""

from unittest.mock import MagicMock, patch

import deepl
import pytest

from mcp_deepl.api_client import DeepLAPIError, DeepLClient
from mcp_deepl.api_models import TranslationResponse, UsageResponse


class TestDeepLClient:
    """Test the DeepL API client."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self) -> None:
        """Test client can be used as async context manager."""
        async with DeepLClient(api_token="test-token") as client:
            assert client._translator is not None

        # Client doesn't need cleanup but maintains API compatibility
        assert client._translator is not None

    @pytest.mark.asyncio
    async def test_client_requires_token(self) -> None:
        """Test client raises error when token is not provided."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="DEEPL_API_KEY"):
                DeepLClient()

    @pytest.mark.asyncio
    async def test_translate_text_success(self) -> None:
        """Test successful text translation."""
        client = DeepLClient(api_token="test-token")

        # Mock the translator's translate_text method
        mock_result = MagicMock()
        mock_result.text = "Hallo Welt"
        mock_result.detected_source_lang = "EN"

        with patch.object(client._translator, "translate_text", return_value=mock_result):
            result = await client.translate_text(text="Hello world", target_lang="DE")

            assert isinstance(result, TranslationResponse)
            assert result.translations[0].text == "Hallo Welt"
            assert result.translations[0].detected_source_language == "EN"

    @pytest.mark.asyncio
    async def test_translate_text_list(self) -> None:
        """Test translating a list of texts."""
        client = DeepLClient(api_token="test-token")

        # Mock the translator returning a list
        mock_results = [
            MagicMock(text="Hallo", detected_source_lang="EN"),
            MagicMock(text="Welt", detected_source_lang="EN"),
        ]

        with patch.object(client._translator, "translate_text", return_value=mock_results):
            result = await client.translate_text(text=["Hello", "World"], target_lang="DE")

            assert isinstance(result, TranslationResponse)
            assert len(result.translations) == 2
            assert result.translations[0].text == "Hallo"
            assert result.translations[1].text == "Welt"

    @pytest.mark.asyncio
    async def test_get_usage_success(self) -> None:
        """Test successful usage retrieval."""
        client = DeepLClient(api_token="test-token")

        # Mock usage response
        mock_usage = MagicMock()
        mock_usage.character = MagicMock(count=123456, limit=500000)
        mock_usage.document = None
        mock_usage.team_document = None

        with patch.object(client._translator, "get_usage", return_value=mock_usage):
            result = await client.get_usage()

            assert isinstance(result, UsageResponse)
            assert result.character_count == 123456
            assert result.character_limit == 500000

    @pytest.mark.asyncio
    async def test_api_authorization_error(self) -> None:
        """Test API authorization error handling."""
        client = DeepLClient(api_token="invalid-token")

        with patch.object(
            client._translator,
            "translate_text",
            side_effect=deepl.AuthorizationException("Invalid authentication"),
        ):
            with pytest.raises(DeepLAPIError) as exc_info:
                await client.translate_text(text="test", target_lang="DE")

            assert exc_info.value.status == 403
            assert "Invalid authentication" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_quota_exceeded_error(self) -> None:
        """Test quota exceeded error handling."""
        client = DeepLClient(api_token="test-token")

        with patch.object(
            client._translator,
            "translate_text",
            side_effect=deepl.QuotaExceededException("Quota exceeded"),
        ):
            with pytest.raises(DeepLAPIError) as exc_info:
                await client.translate_text(text="test", target_lang="DE")

            assert exc_info.value.status == 456

    @pytest.mark.asyncio
    async def test_too_many_requests_error(self) -> None:
        """Test too many requests error handling."""
        client = DeepLClient(api_token="test-token")

        with patch.object(
            client._translator,
            "translate_text",
            side_effect=deepl.TooManyRequestsException("Too many requests"),
        ):
            with pytest.raises(DeepLAPIError) as exc_info:
                await client.translate_text(text="test", target_lang="DE")

            assert exc_info.value.status == 429

    @pytest.mark.asyncio
    async def test_list_languages(self) -> None:
        """Test listing languages."""
        client = DeepLClient(api_token="test-token")

        # Create properly configured mocks with spec
        mock_de = MagicMock()
        mock_de.code = "DE"
        mock_de.name = "German"
        mock_de.supports_formality = True

        mock_fr = MagicMock()
        mock_fr.code = "FR"
        mock_fr.name = "French"
        mock_fr.supports_formality = True

        mock_langs = [mock_de, mock_fr]

        with patch.object(client._translator, "get_target_languages", return_value=mock_langs):
            result = await client.list_languages("target")

            assert len(result.languages) == 2
            assert result.languages[0].language == "DE"
            assert result.languages[0].supports_formality is True

    @pytest.mark.asyncio
    async def test_list_source_languages(self) -> None:
        """Test listing source languages."""
        client = DeepLClient(api_token="test-token")

        # Create properly configured mocks
        mock_en = MagicMock()
        mock_en.code = "EN"
        mock_en.name = "English"
        # Source languages don't have supports_formality attribute
        delattr(mock_en, "supports_formality") if hasattr(mock_en, "supports_formality") else None

        mock_de = MagicMock()
        mock_de.code = "DE"
        mock_de.name = "German"

        mock_langs = [mock_en, mock_de]

        with patch.object(client._translator, "get_source_languages", return_value=mock_langs):
            result = await client.list_languages("source")

            assert len(result.languages) == 2
            assert result.languages[0].language == "EN"

    @pytest.mark.asyncio
    async def test_create_glossary(self) -> None:
        """Test creating a glossary."""
        client = DeepLClient(api_token="test-token")

        from datetime import datetime

        mock_glossary = MagicMock()
        mock_glossary.glossary_id = "test-123"
        mock_glossary.name = "Test Glossary"
        mock_glossary.ready = True
        mock_glossary.source_lang = "EN"
        mock_glossary.target_lang = "DE"
        mock_glossary.creation_time = datetime(2025, 10, 14, 12, 0, 0)
        mock_glossary.entry_count = 2

        with patch.object(client._translator, "create_glossary", return_value=mock_glossary):
            result = await client.create_glossary(
                name="Test Glossary",
                source_lang="EN",
                target_lang="DE",
                entries={"app": "App", "cloud": "Cloud"},
            )

            assert result.glossary_id == "test-123"
            assert result.entry_count == 2
            assert result.ready is True

    @pytest.mark.asyncio
    async def test_list_glossaries(self) -> None:
        """Test listing glossaries."""
        client = DeepLClient(api_token="test-token")

        from datetime import datetime

        mock_glossary = MagicMock()
        mock_glossary.glossary_id = "test-123"
        mock_glossary.name = "Test"
        mock_glossary.ready = True
        mock_glossary.source_lang = "EN"
        mock_glossary.target_lang = "DE"
        mock_glossary.creation_time = datetime(2025, 10, 14, 12, 0, 0)
        mock_glossary.entry_count = 5

        with patch.object(client._translator, "list_glossaries", return_value=[mock_glossary]):
            result = await client.list_glossaries()

            assert len(result.glossaries) == 1
            assert result.glossaries[0].glossary_id == "test-123"

    @pytest.mark.asyncio
    async def test_detect_language(self) -> None:
        """Test language detection."""
        client = DeepLClient(api_token="test-token")

        mock_result = MagicMock()
        mock_result.text = "Bonjour"
        mock_result.detected_source_lang = "FR"

        with patch.object(client._translator, "translate_text", return_value=mock_result):
            result = await client.detect_language("Bonjour le monde")

            assert result.detected_language == "FR"
            assert "Bonjour le monde" in result.text

    @pytest.mark.asyncio
    async def test_translate_with_glossary(self) -> None:
        """Test translation with glossary."""
        client = DeepLClient(api_token="test-token")

        mock_result = MagicMock()
        mock_result.text = "Smartphone App"
        mock_result.detected_source_lang = "EN"

        with patch.object(client._translator, "translate_text", return_value=mock_result):
            result = await client.translate_with_glossary(
                text="smartphone app",
                target_lang="DE",
                glossary_id="test-glossary",
            )

            assert result.translations[0].text == "Smartphone App"
            # Verify glossary parameter was passed
            client._translator.translate_text.assert_called_once()
            call_kwargs = client._translator.translate_text.call_args[1]
            assert call_kwargs["glossary"] == "test-glossary"

    @pytest.mark.asyncio
    async def test_session_cleanup(self) -> None:
        """Test session cleanup (API compatibility)."""
        client = DeepLClient(api_token="test-token")

        # The new client doesn't require session management,
        # but close() should still work without error
        await client.close()
        assert True  # If we get here, close() didn't raise an error
