from django.db import models
from django.conf import settings
import uuid
from typing import Any, Dict
from common.enums import PlatformChoice

class Integration(models.Model):
    """
    Saves connections to various platforms (Facebook Pages, Instagram, WhatsApp Business)
    and their authentication tokens and unique identifiers under an Organization.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="integrations",
        help_text="The organization this integration belongs to"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="integrations",
        help_text="The user who created/connected this integration"
    )
    platform = models.CharField(
        max_length=50,
        choices=PlatformChoice.choices,
        help_text="The platform being integrated (Facebook Page, Instagram, WhatsApp Business)"
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom name or label for this connection (e.g. Page Name or Business Name)"
    )
    access_token = models.TextField(
        help_text="The API access token or system user token used to authenticate on behalf of the user"
    )
    platform_identifier = models.CharField(
        max_length=255,
        help_text="The external identifier on the platform (Facebook Page ID, Instagram Account ID, or Phone Number ID)"
    )
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional platform-specific metadata (e.g. WABA ID, Catalog ID, token expiry)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates if the integration is active and should be used"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "integrations"
        app_label = "integrations"
        verbose_name = "Integration"
        verbose_name_plural = "Integrations"
        unique_together = ("organization", "platform", "platform_identifier")

    def get_platform_display(self) -> str:
        """
        Returns a human-readable label for the platform.
        """
        return PlatformChoice(self.platform).label

    def __str__(self) -> str:
        platform_label = self.get_platform_display()
        display_name = self.name or self.platform_identifier
        return f"{self.organization.name} - {platform_label} ({display_name})"



class MessageLog(models.Model):
    """
    Tracks messages sent from the application on behalf of the user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name="message_logs"
    )
    recipient_id = models.CharField(
        max_length=255,
        help_text="Recipient identifier (phone number for WhatsApp, Page-Scoped ID for FB/Instagram)"
    )
    message_content = models.TextField(
        help_text="The payload/text content of the message sent"
    )
    platform_message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The unique message ID returned by the platform's API"
    )
    status = models.CharField(
        max_length=50,
        default="sent",
        choices=[
            ("sent", "Sent"),
            ("delivered", "Delivered"),
            ("read", "Read"),
            ("failed", "Failed")
        ]
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Details of the error if the sending failed"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "integration_message_logs"
        app_label = "integrations"
        verbose_name = "Message Log"
        verbose_name_plural = "Message Logs"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.integration.platform} to {self.recipient_id} ({self.status}) - {self.created_at}"


class MetaUserToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meta_user_token"
    )
    access_token = models.TextField(
        help_text="The long-lived user access token for Facebook Graph API"
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="The expiration time of the user access token"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meta_user_tokens"
        verbose_name = "Meta User Token"
        verbose_name_plural = "Meta User Tokens"

    def __str__(self) -> str:
        return f"{self.user.email} - Meta Token"

