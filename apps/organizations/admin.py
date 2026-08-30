from django.contrib import admin
from .models import Organization, OrganizationMember, OrganizationSubscription
from unfold.admin import TabularInline, ModelAdmin


class OrganizationMemberInline(TabularInline):
    model = OrganizationMember
    extra = 0
    fields = ("user", "role", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Organization)
class OrganizationAdmin(ModelAdmin):
    list_display = ("name", "slug", "owner", "default_language", "timezone", "created_at")
    search_fields = ("name", "slug", "owner__email")
    inlines = [OrganizationMemberInline]


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(ModelAdmin):
    list_display = ("organization", "user", "role", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("organization__name", "user__email")


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(ModelAdmin):
    list_display = ("organization", "plan_name", "status", "billing_cycle", "max_messages", "renews_at")
    list_filter = ("status", "billing_cycle")
    search_fields = ("organization__name", "plan_name")
