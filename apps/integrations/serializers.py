from rest_framework import serializers
from .models import Integration, MessageLog
from typing import Dict, Any
from apps.organizations.services import get_user_organization

class IntegrationSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Integration
        fields = (
            "id",
            "organization_id",
            "organization_name",
            "platform",
            "name",
            "access_token",
            "platform_identifier",
            "additional_data",
            "is_active",
            "created_at",
            "updated_at"
        )
        read_only_fields = ("id", "organization_id", "organization_name", "created_at", "updated_at")
        extra_kwargs = {
            "access_token": {"write_only": True}  # Security principle: do not return tokens in responses
        }

    def validate_platform_identifier(self, value: str) -> str:
        if not value.strip():
            raise serializers.ValidationError("Platform identifier cannot be empty.")
        return value

    def create(self, validated_data: Dict[str, Any]) -> Integration:
        user = self.context["request"].user
        validated_data["user"] = user
        if "organization" not in validated_data:
            validated_data["organization"] = get_user_organization(user)
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
