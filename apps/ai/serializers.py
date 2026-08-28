import json
from rest_framework import serializers
from common.enums import KnowledgeSourceType, KnowledgeDocumentStatus
from .models import AISettings, KnowledgeDocument, DocumentChunk


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


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = (
            "id",
            "chunk_index",
            "content",
            "token_count",
            "metadata",
            "created_at"
        )
        read_only_fields = fields


class KnowledgeDocumentSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    created_by_email = serializers.EmailField(source="created_by.email", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeDocument
        fields = (
            "id",
            "organization_id",
            "organization_name",
            "title",
            "description",
            "file",
            "file_url",
            "file_name",
            "file_type",
            "file_size",
            "source_type",
            "raw_content",
            "status",
            "error_message",
            "character_count",
            "word_count",
            "chunk_count",
            "tags",
            "metadata",
            "is_active",
            "created_by_email",
            "created_at",
            "updated_at",
            "indexed_at"
        )
        read_only_fields = (
            "id",
            "organization_id",
            "organization_name",
            "file_url",
            "file_name",
            "file_type",
            "file_size",
            "status",
            "error_message",
            "character_count",
            "word_count",
            "chunk_count",
            "created_by_email",
            "created_at",
            "updated_at",
            "indexed_at"
        )

    def get_file_url(self, obj) -> str:
        if obj.file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class KnowledgeDocumentUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading text-related files or submitting raw text to the Knowledge Base.
    """
    file = serializers.FileField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    raw_content = serializers.CharField(required=False, allow_blank=True)
    source_type = serializers.ChoiceField(
        choices=KnowledgeSourceType.choices,
        required=False,
        default=KnowledgeSourceType.FILE
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list
    )
    metadata = serializers.DictField(
        required=False,
        default=dict
    )
    is_active = serializers.BooleanField(required=False, default=True)

    def to_internal_value(self, data):
        # Support multipart form-data where tags or metadata might be passed as JSON strings
        mutable_data = data.dict() if hasattr(data, "dict") else data.copy()
        if "tags" in mutable_data and isinstance(mutable_data["tags"], str):
            try:
                mutable_data["tags"] = json.loads(mutable_data["tags"])
            except Exception:
                # Comma-separated fallback
                mutable_data["tags"] = [t.strip() for t in mutable_data["tags"].split(",") if t.strip()]

        if "metadata" in mutable_data and isinstance(mutable_data["metadata"], str):
            try:
                mutable_data["metadata"] = json.loads(mutable_data["metadata"])
            except Exception:
                mutable_data["metadata"] = {}

        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        file = attrs.get("file")
        raw_content = attrs.get("raw_content")

        if not file and not raw_content:
            raise serializers.ValidationError("Either an uploaded file or 'raw_content' text must be provided.")

        return attrs
