import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
