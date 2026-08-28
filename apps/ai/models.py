import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from common.enums import KnowledgeDocumentStatus, KnowledgeSourceType


class AISettings(models.Model):
    """
    Configuration and prompt parameters for AI automated replies scoped per Organization.
    """
    TONE_CHOICES = [
        ("professional", "Professional"),
        ("friendly", "Friendly"),
        ("casual", "Casual"),
        ("formal", "Formal"),
        ("enthusiastic", "Enthusiastic"),
    ]

    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("gemini", "Google Gemini"),
        ("anthropic", "Anthropic Claude"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="ai_settings",
        help_text="The organization this AI configuration belongs to"
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Enable or disable AI auto-reply for this organization"
    )
    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default="openai",
        help_text="AI model provider (OpenAI, Google Gemini, Anthropic)"
    )
    model_name = models.CharField(
        max_length=100,
        default="gpt-4o-mini",
        blank=True,
        help_text="The specific model ID to use (e.g. gpt-4o-mini, gemini-1.5-flash, claude-3-haiku)"
    )
    api_key = models.TextField(
        blank=True,
        null=True,
        help_text="Custom API key if organization uses its own model credentials"
    )
    system_prompt = models.TextField(
        blank=True,
        default="You are a helpful, polite, and professional customer support assistant for our business. Reply concisely, clearly, and accurately to customer inquiries.",
        help_text="System prompt defining the persona, guidelines, and constraints for the AI agent"
    )
    tone = models.CharField(
        max_length=50,
        choices=TONE_CHOICES,
        default="professional",
        help_text="General tone of voice for generated replies"
    )
    temperature = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(2.0)],
        help_text="Controls reply creativity / randomness (0.0 = deterministic, 2.0 = highly creative)"
    )
    max_tokens = models.IntegerField(
        default=500,
        validators=[MinValueValidator(50), MaxValueValidator(4096)],
        help_text="Maximum token limit for generated responses"
    )
    fallback_message = models.TextField(
        blank=True,
        default="Thank you for contacting us! A member of our team will review your message and get back to you shortly.",
        help_text="Fallback message returned if AI response fails or confidence is low"
    )
    auto_reply_delay_seconds = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(300)],
        help_text="Optional simulated delay before dispatching reply (in seconds)"
    )
    business_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Business or brand name for context in prompts"
    )
    business_description = models.TextField(
        blank=True,
        null=True,
        help_text="Summary of products, services, operating hours, and business details"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_settings"
        verbose_name = "AI Setting"
        verbose_name_plural = "AI Settings"

    def __str__(self) -> str:
        return f"{self.organization.name} - AI Settings ({'Active' if self.is_enabled else 'Disabled'})"


class KnowledgeDocument(models.Model):
    """
    Represents a knowledge base source document (e.g. text file, markdown, FAQ, or guide)
    uploaded for an organization to enrich AI auto-replies via RAG.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="knowledge_documents",
        help_text="The organization this knowledge document belongs to"
    )
    title = models.CharField(max_length=255, help_text="Title or name of the document")
    description = models.TextField(blank=True, null=True, help_text="Optional summary or description of the document")
    file = models.FileField(
        upload_to="knowledge_base/%Y/%m/",
        blank=True,
        null=True,
        help_text="Uploaded document file (e.g. .txt, .md, .pdf, .csv, .json, .docx)"
    )
    file_name = models.CharField(max_length=255, blank=True, null=True, help_text="Original uploaded filename")
    file_type = models.CharField(max_length=50, blank=True, null=True, help_text="Extension or MIME type (e.g. txt, md, pdf, csv, json)")
    file_size = models.BigIntegerField(blank=True, null=True, help_text="File size in bytes")
    source_type = models.CharField(
        max_length=50,
        choices=KnowledgeSourceType.choices,
        default=KnowledgeSourceType.FILE,
        help_text="Source type: file, raw text, FAQ, or URL"
    )
    raw_content = models.TextField(blank=True, null=True, help_text="Extracted plain text content ready for indexing")
    status = models.CharField(
        max_length=50,
        choices=KnowledgeDocumentStatus.choices,
        default=KnowledgeDocumentStatus.PENDING,
        db_index=True,
        help_text="Current indexing lifecycle status (pending, processing, indexed, failed)"
    )
    error_message = models.TextField(blank=True, null=True, help_text="Error message if text extraction or indexing failed")
    character_count = models.IntegerField(default=0, help_text="Character count of extracted content")
    word_count = models.IntegerField(default=0, help_text="Word count of extracted content")
    chunk_count = models.IntegerField(default=0, help_text="Number of vector chunks generated from this document")
    tags = models.JSONField(default=list, blank=True, help_text="List of string tags for categorization and filtering")
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom key-value metadata attributes for filtering")
    is_active = models.BooleanField(
        default=True,
        help_text="Controls whether this document is actively queried by the AI assistant"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents",
        help_text="User who uploaded or created this document"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    indexed_at = models.DateTimeField(blank=True, null=True, help_text="Timestamp when vector indexing completed")

    class Meta:
        db_table = "knowledge_documents"
        verbose_name = "Knowledge Document"
        verbose_name_plural = "Knowledge Documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.title} ({self.status})"


class DocumentChunk(models.Model):
    """
    Individual text segments/chunks extracted from a KnowledgeDocument for vector indexing and semantic search.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        KnowledgeDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
        help_text="The parent document this chunk belongs to"
    )
    chunk_index = models.IntegerField(default=0, help_text="Sequence index of the chunk within the document")
    content = models.TextField(help_text="The text snippet content of this chunk")
    token_count = models.IntegerField(default=0, help_text="Approximate token count for the chunk content")
    embedding = models.JSONField(blank=True, null=True, help_text="Vector embedding numbers (float array)")
    metadata = models.JSONField(default=dict, blank=True, help_text="Chunk-level metadata for context filtering")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "knowledge_document_chunks"
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"
        ordering = ["document", "chunk_index"]

    def __str__(self) -> str:
        return f"{self.document.title} - Chunk #{self.chunk_index}"

