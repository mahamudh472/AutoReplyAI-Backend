from rest_framework import serializers
from .models import AISettings


class AISettingsSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = AISettings
        fields = (
            "id",
            "organization_id",
            "organization_name",
            "is_enabled",
            "provider",
            "model_name",
            "api_key",
            "system_prompt",
            "tone",
            "temperature",
            "max_tokens",
            "fallback_message",
            "auto_reply_delay_seconds",
            "business_name",
            "business_description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "organization_id", "organization_name", "created_at", "updated_at")
