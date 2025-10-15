"""Wrapper around official DeepL Python client for async compatibility."""

import os
from typing import Any

import deepl

from .api_models import (
    DocumentDownloadResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    GlossariesResponse,
    Glossary,
    LanguageDetectionResponse,
    LanguagesResponse,
    Translation,
    TranslationResponse,
    UsageResponse,
)


class DeepLAPIError(Exception):
    """Custom exception for DeepL API errors."""

    def __init__(self, status: int, message: str, details: dict[str, Any] | None = None) -> None:
        self.status = status
        self.message = message
        self.details = details
        super().__init__(f"DeepL API Error {status}: {message}")


class DeepLClient:
    """Wrapper around official DeepL Translator for MCP server compatibility."""

    def __init__(
        self,
        api_token: str | None = None,
    ) -> None:
        """Initialize DeepL client.

        Args:
            api_token: DeepL API authentication key. If not provided, will use DEEPL_API_KEY env var.
        """
        self.api_token = api_token or os.environ.get("DEEPL_API_KEY")
        if not self.api_token:
            raise ValueError("DEEPL_API_KEY must be provided or set in environment")

        # Create the official DeepL translator
        self._translator = deepl.Translator(self.api_token)

    async def __aenter__(self) -> "DeepLClient":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the translator client and cleanup HTTP session."""
        # Close the underlying HTTP client to prevent hanging connections
        if hasattr(self._translator, "_client") and self._translator._client:
            self._translator._client.close()  # type: ignore[no-untyped-call]

    # Translation methods

    async def translate_text(
        self,
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
        try:
            # Convert split_sentences to the format expected by the official client
            # The DeepL SDK accepts: "0"/"off", "1"/"on", "nonewlines", or None
            split_sentences_param: str | None = None
            if split_sentences == "0":
                split_sentences_param = "0"
            elif split_sentences == "1":
                split_sentences_param = "1"
            elif split_sentences == "nonewlines":
                split_sentences_param = "nonewlines"

            # Call the official DeepL client
            result = self._translator.translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang,
                formality=formality,
                preserve_formatting=preserve_formatting,
                tag_handling=tag_handling,
                split_sentences=split_sentences_param,
            )

            # Convert result to our response model
            if isinstance(result, list):
                translations = [
                    Translation(
                        detected_source_language=r.detected_source_lang,
                        text=r.text,
                    )
                    for r in result
                ]
            else:
                translations = [
                    Translation(
                        detected_source_language=result.detected_source_lang,
                        text=result.text,
                    )
                ]

            return TranslationResponse(translations=translations)

        except deepl.DeepLException as e:
            # Map DeepL exceptions to our custom error
            status = 500
            if isinstance(e, deepl.AuthorizationException):
                status = 403
            elif isinstance(e, deepl.QuotaExceededException):
                status = 456
            elif isinstance(e, deepl.TooManyRequestsException):
                status = 429

            raise DeepLAPIError(status, str(e)) from e

    async def detect_language(self, text: str) -> LanguageDetectionResponse:
        """Detect the language of text.

        Args:
            text: Text to detect language for

        Returns:
            Detected language information
        """
        try:
            # Translate to detect language (DeepL doesn't have dedicated detection endpoint)
            result = self._translator.translate_text(text[:1000], target_lang="EN-US")

            # Handle both single result and list
            detected_lang = None
            if isinstance(result, list):
                if result:
                    detected_lang = result[0].detected_source_lang
            else:
                detected_lang = result.detected_source_lang

            return LanguageDetectionResponse(
                detected_language=detected_lang,
                text=text[:100] + "..." if len(text) > 100 else text,
            )
        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    # Language methods

    async def list_languages(self, language_type: str = "target") -> LanguagesResponse:
        """List all supported source and target languages.

        Args:
            language_type: Type of languages to list (source or target)

        Returns:
            List of supported languages
        """
        try:
            if language_type == "source":
                langs = self._translator.get_source_languages()
            else:
                langs = self._translator.get_target_languages()

            languages = [
                {
                    "language": lang.code,
                    "name": lang.name,
                    "supports_formality": getattr(lang, "supports_formality", None),
                }
                for lang in langs
            ]

            return LanguagesResponse(languages=languages)  # type: ignore[arg-type]

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    # Usage methods

    async def get_usage(self) -> UsageResponse:
        """Get API usage statistics.

        Returns:
            Usage statistics
        """
        try:
            usage = self._translator.get_usage()

            # Handle both character-based and document-based usage
            character_count: int = 0
            character_limit: int = 0

            if usage.character:
                character_count = usage.character.count or 0
                character_limit = usage.character.limit or 0

            return UsageResponse(
                character_count=character_count,
                character_limit=character_limit,
                document_count=usage.document.count if usage.document else None,
                document_limit=usage.document.limit if usage.document else None,
                team_document_count=usage.team_document.count if usage.team_document else None,
                team_document_limit=usage.team_document.limit if usage.team_document else None,
            )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    # Glossary methods

    async def list_glossaries(self) -> GlossariesResponse:
        """List custom glossaries.

        Returns:
            List of glossaries
        """
        try:
            glossaries = self._translator.list_glossaries()

            glossary_list = [
                Glossary(
                    glossary_id=g.glossary_id,
                    name=g.name,
                    ready=g.ready,
                    source_lang=g.source_lang,
                    target_lang=g.target_lang,
                    creation_time=g.creation_time.isoformat(),
                    entry_count=g.entry_count,
                )
                for g in glossaries
            ]

            return GlossariesResponse(glossaries=glossary_list)

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    async def create_glossary(
        self,
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
            entries_format: Format (tsv or csv) - maintained for API compatibility

        Returns:
            Created glossary information
        """
        try:
            # The official client takes a dict directly
            glossary = self._translator.create_glossary(
                name=name,
                source_lang=source_lang,
                target_lang=target_lang,
                entries=entries,
            )

            return Glossary(
                glossary_id=glossary.glossary_id,
                name=glossary.name,
                ready=glossary.ready,
                source_lang=glossary.source_lang,
                target_lang=glossary.target_lang,
                creation_time=glossary.creation_time.isoformat(),
                entry_count=glossary.entry_count,
            )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    async def get_glossary(self, glossary_id: str) -> Glossary:
        """Get glossary details.

        Args:
            glossary_id: Glossary ID

        Returns:
            Glossary information
        """
        try:
            glossary = self._translator.get_glossary(glossary_id)

            return Glossary(
                glossary_id=glossary.glossary_id,
                name=glossary.name,
                ready=glossary.ready,
                source_lang=glossary.source_lang,
                target_lang=glossary.target_lang,
                creation_time=glossary.creation_time.isoformat(),
                entry_count=glossary.entry_count,
            )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    async def delete_glossary(self, glossary_id: str) -> dict[str, Any]:
        """Delete a glossary.

        Args:
            glossary_id: Glossary ID

        Returns:
            Success confirmation
        """
        try:
            self._translator.delete_glossary(glossary_id)
            return {"success": True, "glossary_id": glossary_id}

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    async def translate_with_glossary(
        self,
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
        try:
            result = self._translator.translate_text(
                text,
                target_lang=target_lang,
                source_lang=source_lang,
                formality=formality,
                glossary=glossary_id,
            )

            # Convert result to our response model
            if isinstance(result, list):
                translations = [
                    Translation(
                        detected_source_language=r.detected_source_lang,
                        text=r.text,
                    )
                    for r in result
                ]
            else:
                translations = [
                    Translation(
                        detected_source_language=result.detected_source_lang,
                        text=result.text,
                    )
                ]

            return TranslationResponse(translations=translations)

        except deepl.DeepLException as e:
            status = 500
            if isinstance(e, deepl.AuthorizationException):
                status = 403
            elif isinstance(e, deepl.QuotaExceededException):
                status = 456
            raise DeepLAPIError(status, str(e)) from e

    # Document methods

    async def upload_document(
        self,
        document_path: str,
        target_lang: str,
        source_lang: str | None = None,
        formality: str | None = None,
        filename: str | None = None,
    ) -> DocumentUploadResponse:
        """Upload document for translation.

        Args:
            document_path: Path to document
            target_lang: Target language code
            source_lang: Source language code (optional)
            formality: Formality level
            filename: Original filename (for proper format detection)

        Returns:
            Document upload response with document_id and document_key
        """
        try:
            with open(document_path, "rb") as file:
                handle = self._translator.translate_document_upload(
                    file,
                    target_lang=target_lang,
                    source_lang=source_lang,
                    formality=formality,
                    filename=filename,
                )

            return DocumentUploadResponse(
                document_id=handle.document_id,
                document_key=handle.document_key,
            )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e
        except FileNotFoundError as e:
            raise DeepLAPIError(404, f"Document not found: {document_path}") from e

    async def get_document_status(
        self, document_id: str, document_key: str
    ) -> DocumentStatusResponse:
        """Check document translation status.

        Args:
            document_id: Document ID from upload
            document_key: Document key from upload

        Returns:
            Document status information
        """
        try:
            # Create a DocumentHandle from the ID and key
            handle = deepl.DocumentHandle(document_id, document_key)
            status = self._translator.translate_document_get_status(handle)

            # Map status to our enum
            status_str = "queued"
            if status.done:
                status_str = "done"
            elif status.error_message:
                status_str = "error"
            elif status.seconds_remaining is not None:
                status_str = "translating"

            return DocumentStatusResponse(
                document_id=document_id,
                status=status_str,  # type: ignore[arg-type]
                seconds_remaining=status.seconds_remaining,
                billed_characters=status.billed_characters,
                error_message=str(status.error_message) if status.error_message else None,
            )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e

    async def download_translated_document(
        self, document_id: str, document_key: str, output_path: str | None = None
    ) -> DocumentDownloadResponse:
        """Download completed document translation.

        Args:
            document_id: Document ID
            document_key: Document key
            output_path: Optional path to save the document

        Returns:
            Document download information
        """
        try:
            # Create a DocumentHandle from the ID and key
            handle = deepl.DocumentHandle(document_id, document_key)

            if output_path:
                # Download to file
                with open(output_path, "wb") as file:
                    self._translator.translate_document_download(handle, file)

                import os

                size = os.path.getsize(output_path)

                return DocumentDownloadResponse(
                    success=True,
                    document_id=document_id,
                    content_type="application/octet-stream",
                    size=size,
                    note=f"Document saved to {output_path}",
                )
            else:
                # Download to memory (note: this may not be ideal for large files)
                import io

                buffer = io.BytesIO()
                self._translator.translate_document_download(handle, buffer)
                size = buffer.tell()

                return DocumentDownloadResponse(
                    success=True,
                    document_id=document_id,
                    content_type="application/octet-stream",
                    size=size,
                    note="Document downloaded to memory buffer",
                )

        except deepl.DeepLException as e:
            raise DeepLAPIError(500, str(e)) from e
