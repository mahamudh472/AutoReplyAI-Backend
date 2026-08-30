import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from common.enums import OrganizationRoleChoice


class Organization(models.Model):
    """
    Represents a tenant or team under which all integrations and resources are scoped.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Organization / Company name", default="Default organization")
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, db_index=True, help_text="Unique slug for URLs / identifiers")
    logo = models.ImageField(upload_to="organization_logos/%Y/%m/", blank=True, null=True, help_text="Organization logo image")
    default_language = models.CharField(max_length=50, default="English", blank=True, help_text="Default communication language")
    timezone = models.CharField(max_length=50, default="GMT+06:00", blank=True, help_text="Organization timezone")
    description = models.TextField(max_length=500, blank=True, null=True, help_text="Brief summary/description of the organization")
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

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "org"
            slug = base_slug
            counter = 1
            # Ensure unique slug
            while Organization.objects.filter(slug=slug).exclude(id=self.id).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

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


class OrganizationSubscription(models.Model):
    """
    Tracks subscription tier, usage quotas, and renewal details for an organization.
    """
    STATUS_CHOICES = [
        ("active", "Active"),
        ("trialing", "Trialing"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
    ]

    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="subscription",
        help_text="Organization tied to this subscription plan"
    )
    plan_name = models.CharField(max_length=100, default="Starter Plan", help_text="Subscription plan tier name")
    status = models.CharField(max_length=50, default="active", choices=STATUS_CHOICES)
    billing_cycle = models.CharField(max_length=50, default="monthly", choices=BILLING_CHOICES)
    max_messages = models.IntegerField(default=10000, help_text="Maximum allowed messages per cycle")
    max_team_members = models.IntegerField(default=1, help_text="Maximum team members allowed")
    max_connected_accounts = models.IntegerField(default=1, help_text="Maximum connected integration channels")
    renews_at = models.DateTimeField(blank=True, null=True, help_text="Date when current billing cycle renews")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organization_subscriptions"
        verbose_name = "Organization Subscription"
        verbose_name_plural = "Organization Subscriptions"

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.plan_name} ({self.status})"
