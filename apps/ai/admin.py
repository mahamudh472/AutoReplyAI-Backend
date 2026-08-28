from django.contrib import admin
from .models import AISettings, KnowledgeDocument, DocumentChunk


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "provider", "model_name", "tone", "temperature", "is_enabled", "updated_at")
    list_filter = ("provider", "tone", "is_enabled", "created_at")
    search_fields = ("organization__name", "business_name", "system_prompt")


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ("chunk_index", "content", "token_count", "created_at")
    readonly_fields = ("created_at",)


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "source_type", "file_type", "status", "character_count", "word_count", "is_active", "created_at")
    list_filter = ("status", "source_type", "is_active", "created_at")
    search_fields = ("title", "description", "file_name", "raw_content", "organization__name")
    readonly_fields = ("created_at", "updated_at", "character_count", "word_count", "chunk_count")
    inlines = [DocumentChunkInline]


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "token_count", "created_at")
    search_fields = ("document__title", "content")
    readonly_fields = ("created_at",)
