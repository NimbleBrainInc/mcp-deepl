"""
Core tools integration tests.

Tests basic DeepL API functionality with real API calls.
"""

import pytest

from mcp_deepl.api_client import DeepLClient


class TestTranslation:
    """Test text translation functionality."""

    @pytest.mark.asyncio
    async def test_simple_translation(self, client: DeepLClient):
        """Test basic English to German translation."""
        result = await client.translate_text(text="Hello world", target_lang="DE")

        assert len(result.translations) == 1
        assert result.translations[0].text
        assert result.translations[0].detected_source_language == "EN"
        print(f"Translated: {result.translations[0].text}")

    @pytest.mark.asyncio
    async def test_batch_translation(self, client: DeepLClient):
        """Test translating multiple texts at once."""
        result = await client.translate_text(
            text=["Hello", "Goodbye", "Thank you"],
            target_lang="FR",
        )

        assert len(result.translations) == 3
        for t in result.translations:
            assert t.text
            assert t.detected_source_language  # language detected for each item
        print(f"Batch: {[t.text for t in result.translations]}")

    @pytest.mark.asyncio
    async def test_translation_with_formality(self, client: DeepLClient):
        """Test translation with formality parameter."""
        result_formal = await client.translate_text(
            text="How are you?",
            target_lang="DE",
            formality="more",
        )
        result_informal = await client.translate_text(
            text="How are you?",
            target_lang="DE",
            formality="less",
        )

        assert result_formal.translations[0].text
        assert result_informal.translations[0].text
        print(f"Formal: {result_formal.translations[0].text}")
        print(f"Informal: {result_informal.translations[0].text}")

    @pytest.mark.asyncio
    async def test_translation_with_source_lang(self, client: DeepLClient):
        """Test translation with explicit source language."""
        result = await client.translate_text(
            text="Bonjour le monde",
            target_lang="EN-US",
            source_lang="FR",
        )

        assert len(result.translations) == 1
        assert result.translations[0].text
        print(f"FR->EN: {result.translations[0].text}")


class TestLanguageDetection:
    """Test language detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_french(self, client: DeepLClient):
        """Test detecting French text."""
        result = await client.detect_language("Bonjour le monde")

        assert result.detected_language == "FR"

    @pytest.mark.asyncio
    async def test_detect_german(self, client: DeepLClient):
        """Test detecting German text."""
        result = await client.detect_language("Guten Morgen, wie geht es Ihnen?")

        assert result.detected_language == "DE"


class TestLanguages:
    """Test language listing functionality."""

    @pytest.mark.asyncio
    async def test_list_target_languages(self, client: DeepLClient):
        """Test listing target languages."""
        result = await client.list_languages("target")

        assert len(result.languages) > 20
        codes = {lang.language for lang in result.languages}
        assert "DE" in codes
        assert "FR" in codes
        assert "ES" in codes
        print(f"Target languages: {len(result.languages)}")

    @pytest.mark.asyncio
    async def test_list_source_languages(self, client: DeepLClient):
        """Test listing source languages."""
        result = await client.list_languages("source")

        assert len(result.languages) > 10
        codes = {lang.language for lang in result.languages}
        assert "EN" in codes
        assert "DE" in codes
        print(f"Source languages: {len(result.languages)}")


class TestUsage:
    """Test usage endpoint."""

    @pytest.mark.asyncio
    async def test_get_usage(self, client: DeepLClient):
        """Test getting API usage statistics."""
        result = await client.get_usage()

        assert result.character_count >= 0
        assert result.character_limit > 0
        print(f"Usage: {result.character_count}/{result.character_limit}")


class TestGlossaryCRUD:
    """Test full glossary lifecycle."""

    @pytest.mark.asyncio
    async def test_glossary_lifecycle(self, client: DeepLClient):
        """Test create, get, list, and delete a glossary."""
        glossary = None
        try:
            # Create
            glossary = await client.create_glossary(
                name="test-integration-glossary",
                source_lang="EN",
                target_lang="DE",
                entries={"app": "App", "cloud": "Cloud", "server": "Server"},
            )
            assert glossary.glossary_id
            assert glossary.name == "test-integration-glossary"
            assert glossary.entry_count == 3
            assert glossary.ready is True
            print(f"Created glossary: {glossary.glossary_id}")

            # Get
            fetched = await client.get_glossary(glossary.glossary_id)
            assert fetched.glossary_id == glossary.glossary_id
            assert fetched.name == glossary.name

            # List
            all_glossaries = await client.list_glossaries()
            ids = {g.glossary_id for g in all_glossaries.glossaries}
            assert glossary.glossary_id in ids

            # Translate with glossary
            result = await client.translate_with_glossary(
                text="The app runs on the cloud server",
                target_lang="DE",
                glossary_id=glossary.glossary_id,
                source_lang="EN",
            )
            assert result.translations[0].text
            print(f"With glossary: {result.translations[0].text}")

        finally:
            # Delete (always clean up)
            if glossary:
                result = await client.delete_glossary(glossary.glossary_id)
                assert result["success"] is True
                print(f"Deleted glossary: {glossary.glossary_id}")
