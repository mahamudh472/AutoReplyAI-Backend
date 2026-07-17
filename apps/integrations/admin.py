from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Integration, MessageLog, MetaUserToken

@admin.register(Integration)
class IntegrationAdmin(ModelAdmin):
    list_display = ("user", "platform", "name", "platform_identifier", "is_active", "created_at")
    list_filter = ("platform", "is_active", "created_at")
    search_fields = ("user__email", "name", "platform_identifier")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {
            "fields": ("user", "platform", "name", "is_active")
        }),
        ("Authentication & Identifier", {
            "fields": ("access_token", "platform_identifier")
        }),
        ("Extra Configuration", {
            "fields": ("additional_data", "created_at", "updated_at")
        }),
    )

@admin.register(MessageLog)
class MessageLogAdmin(ModelAdmin):
    list_display = ("integration", "recipient_id", "status", "platform_message_id", "created_at")
    list_filter = ("status", "created_at", "integration__platform")
    search_fields = ("recipient_id", "platform_message_id", "message_content", "integration__user__email")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {
            "fields": ("integration", "recipient_id", "status")
        }),
        ("Payload & IDs", {
            "fields": ("message_content", "platform_message_id")
        }),
        ("Error Details", {
            "fields": ("error_message", "created_at")
        }),
    )

@admin.register(MetaUserToken)
class MetaUserTokenAdmin(ModelAdmin):
    pass
