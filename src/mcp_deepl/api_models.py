"""Pydantic models for DeepL API responses."""

from enum import Enum

from pydantic import BaseModel, Field


class FormalityLevel(str, Enum):
    """Enum for formality levels."""

    DEFAULT = "default"
    MORE = "more"
    LESS = "less"
    PREFER_MORE = "prefer_more"
    PREFER_LESS = "prefer_less"


class TagHandling(str, Enum):
    """Enum for tag handling modes."""

    XML = "xml"
    HTML = "html"


class SplitSentences(str, Enum):
    """Enum for sentence splitting modes."""

    NONE = "0"
    DEFAULT = "1"
    NO_NEWLINES = "nonewlines"


class LanguageType(str, Enum):
    """Enum for language types."""

    SOURCE = "source"
    TARGET = "target"


class DocumentStatus(str, Enum):
    """Enum for document translation status."""

    QUEUED = "queued"
    TRANSLATING = "translating"
    DONE = "done"
    ERROR = "error"


class Translation(BaseModel):
    """Model for a single translation result."""

    detected_source_language: str | None = Field(None, description="Detected source language code")
    text: str = Field(..., description="Translated text")


class TranslationResponse(BaseModel):
    """Response model for translate endpoint."""

    translations: list[Translation] = Field(..., description="List of translations")


class Language(BaseModel):
    """Model for a supported language."""

    language: str = Field(..., description="Language code")
    name: str = Field(..., description="Language name")
    supports_formality: bool | None = Field(None, description="Whether formality is supported")


class LanguagesResponse(BaseModel):
    """Response model for languages endpoint."""

    languages: list[Language] = Field(..., description="List of supported languages")


class UsageResponse(BaseModel):
    """Response model for usage endpoint."""

    character_count: int = Field(..., description="Characters used")
    character_limit: int = Field(..., description="Character limit")
    document_count: int | None = Field(None, description="Documents translated")
    document_limit: int | None = Field(None, description="Document limit")
    team_document_count: int | None = Field(None, description="Team documents used")
    team_document_limit: int | None = Field(None, description="Team document limit")


class Glossary(BaseModel):
    """Model for a glossary."""

    glossary_id: str = Field(..., description="Unique glossary identifier")
    name: str = Field(..., description="Glossary name")
    ready: bool = Field(..., description="Whether glossary is ready to use")
    source_lang: str = Field(..., description="Source language code")
    target_lang: str = Field(..., description="Target language code")
    creation_time: str = Field(..., description="Creation timestamp")
    entry_count: int = Field(..., description="Number of entries")


class GlossariesResponse(BaseModel):
    """Response model for glossaries list endpoint."""

    glossaries: list[Glossary] = Field(..., description="List of glossaries")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    document_id: str = Field(..., description="Document identifier")
    document_key: str = Field(..., description="Document key for status/download")


class DocumentStatusResponse(BaseModel):
    """Response model for document status."""

    document_id: str = Field(..., description="Document identifier")
    status: DocumentStatus = Field(..., description="Translation status")
    seconds_remaining: int | None = Field(None, description="Estimated seconds remaining")
    billed_characters: int | None = Field(None, description="Characters billed")
    error_message: str | None = Field(None, description="Error message if status=error")


class DocumentDownloadResponse(BaseModel):
    """Response model for document download."""

    success: bool = Field(..., description="Whether download was successful")
    document_id: str = Field(..., description="Document identifier")
    content_type: str | None = Field(None, description="Content type of document")
    size: int = Field(..., description="Size in bytes")
    note: str = Field(..., description="Additional notes")


class LanguageDetectionResponse(BaseModel):
    """Response model for language detection."""

    detected_language: str | None = Field(None, description="Detected language code")
    text: str = Field(..., description="Text that was analyzed")


class ErrorResponse(BaseModel):
    """Error response model."""

    status: int | None = None
    error: dict[str, str] | None = None
    message: str | None = None
