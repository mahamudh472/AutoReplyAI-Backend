from typing import Tuple, Optional
from django.contrib.auth import get_user_model
from common.enums import OrganizationRoleChoice
from .models import Organization, OrganizationMember

User = get_user_model()


def create_default_organization_for_user(user: User) -> Tuple[Organization, OrganizationMember]:
    """
    Creates a default organization for the user if they do not already own one,
    and adds an OrganizationMember entry with the OWNER role.
    """
    existing_membership = OrganizationMember.objects.filter(
        user=user,
        role=OrganizationRoleChoice.OWNER
    ).select_related("organization").first()

    if existing_membership:
        return existing_membership.organization, existing_membership

    # Check if user already owns an organization without membership
    existing_org = Organization.objects.filter(owner=user).first()
    if existing_org:
        member, _ = OrganizationMember.objects.get_or_create(
            organization=existing_org,
            user=user,
            defaults={"role": OrganizationRoleChoice.OWNER}
        )
        return existing_org, member

    # Generate organization name from user's full name or email
    display_name = user.full_name or user.email.split("@")[0]
    org_name = f"{display_name}'s Organization"

    organization = Organization.objects.create(
        name=org_name,
        owner=user
    )
    member = OrganizationMember.objects.create(
        organization=organization,
        user=user,
        role=OrganizationRoleChoice.OWNER
    )
    return organization, member


def get_user_organization(user: User) -> Optional[Organization]:
    """
    Returns the primary organization for the user.
    If the user has memberships, returns the organization where they are OWNER or the first available.
    If none exists and the user is active, creates a default organization.
    """
    # 1. Try to find membership with OWNER role
    owner_membership = OrganizationMember.objects.filter(
        user=user,
        role=OrganizationRoleChoice.OWNER
    ).select_related("organization").first()

    if owner_membership:
        return owner_membership.organization

    # 2. Try any membership
    any_membership = OrganizationMember.objects.filter(
        user=user
    ).select_related("organization").first()

    if any_membership:
        return any_membership.organization

    # 3. If active, auto-create
    if user.is_active:
        org, _ = create_default_organization_for_user(user)
        return org

    return None
