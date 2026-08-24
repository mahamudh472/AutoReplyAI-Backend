from django.contrib import admin
from .models import AISettings


@admin.register(AISettings)
class AISettingsAdmin(admin.ModelAdmin):
    list_display = ("organization", "provider", "model_name", "tone", "temperature", "is_enabled", "updated_at")
    list_filter = ("provider", "tone", "is_enabled", "created_at")
    search_fields = ("organization__name", "business_name", "system_prompt")
