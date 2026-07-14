from rest_framework import serializers
from .models import Integration, MessageLog
from typing import Dict, Any

class IntegrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Integration
        fields = (
            "id",
            "platform",
            "name",
            "access_token",
            "platform_identifier",
            "additional_data",
            "is_active",
            "created_at",
            "updated_at"
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "access_token": {"write_only": True}  # Security principle: do not return tokens in responses
        }

    def validate_platform_identifier(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Platform identifier cannot be empty.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Integration:
        # User is injected from the view during save()
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class MessageLogSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(source="integration.platform", read_only=True)
    integration_name = serializers.CharField(source="integration.name", read_only=True)

    class Meta:
        model = MessageLog
        fields = (
            "id",
            "integration",
            "platform",
            "integration_name",
            "recipient_id",
            "message_content",
            "platform_message_id",
            "status",
            "error_message",
            "created_at"
        )
        read_only_fields = fields
