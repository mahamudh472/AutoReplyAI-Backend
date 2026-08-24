import uuid
from django.db import models
from django.conf import settings
from common.enums import OrganizationRoleChoice


class Organization(models.Model):
    """
    Represents a tenant or team under which all integrations and resources are scoped.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Organization / Company name", default="Default organization")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_organizations",
        help_text="The primary owner of the organization"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.email})"


class OrganizationMember(models.Model):
    """
    Represents the membership of a user in an organization with a specific role.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The organization this membership belongs to"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        help_text="The user belonging to the organization"
    )
    role = models.CharField(
        max_length=20,
        choices=OrganizationRoleChoice.choices,
        default=OrganizationRoleChoice.MEMBER,
        help_text="Role within the organization (Owner, Admin, Member)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_members"
        verbose_name = "Organization Member"
        verbose_name_plural = "Organization Members"
        unique_together = ("organization", "user")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.organization.name} ({self.get_role_display()})"
