from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from common.enums import OrganizationRoleChoice
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.services import create_default_organization_for_user, get_user_organization

User = get_user_model()


class OrganizationModelAndSignalTests(APITestCase):
    def test_active_user_auto_creates_organization_and_owner_member(self):
        """Creating an active user should automatically create an Organization and OWNER OrganizationMember."""
        user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            full_name="Alice Owner"
        )
        # Check Organization
        org = Organization.objects.filter(owner=user).first()
        self.assertIsNotNone(org)
        self.assertEqual(org.name, "Alice Owner's Organization")
        self.assertEqual(org.owner, user)

        # Check OrganizationMember with OWNER role
        member = OrganizationMember.objects.filter(organization=org, user=user).first()
        self.assertIsNotNone(member)
        self.assertEqual(member.role, OrganizationRoleChoice.OWNER)

    def test_inactive_user_activation_creates_organization(self):
        """An inactive user does not create an organization until activated."""
        user = User.objects.create_user(
            email="inactive_bob@example.com",
            password="password123",
            full_name="Bob User",
            is_active=False
        )
        self.assertFalse(Organization.objects.filter(owner=user).exists())

        # Activate user
        user.is_active = True
        user.save()

        org = Organization.objects.filter(owner=user).first()
        self.assertIsNotNone(org)
        self.assertEqual(org.name, "Bob User's Organization")
        member = OrganizationMember.objects.filter(organization=org, user=user).first()
        self.assertIsNotNone(member)
        self.assertEqual(member.role, OrganizationRoleChoice.OWNER)

    def test_create_default_organization_idempotent(self):
        """Calling create_default_organization_for_user multiple times returns the same org and does not duplicate."""
        user = User.objects.create_user(
            email="idempotent@example.com",
            password="password123",
            full_name="Charlie"
        )
        org1, member1 = create_default_organization_for_user(user)
        org2, member2 = create_default_organization_for_user(user)
        self.assertEqual(org1.id, org2.id)
        self.assertEqual(member1.id, member2.id)
        self.assertEqual(Organization.objects.filter(owner=user).count(), 1)
        self.assertEqual(OrganizationMember.objects.filter(user=user).count(), 1)


class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner_api@example.com",
            password="password123",
            full_name="Owner Api"
        )
        self.member_user = User.objects.create_user(
            email="member_api@example.com",
            password="password123",
            full_name="Member Api"
        )
        self.client.force_authenticate(user=self.owner)
        self.org = get_user_organization(self.owner)

    def test_get_current_organization(self):
        url = reverse("organization_current")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.org.id))
        self.assertEqual(response.data["name"], self.org.name)
        self.assertEqual(response.data["owner_email"], self.owner.email)

    def test_list_user_organizations(self):
        url = reverse("organization_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.org.id))

    def test_list_and_add_organization_members(self):
        # Add member_user to org
        OrganizationMember.objects.create(
            organization=self.org,
            user=self.member_user,
            role=OrganizationRoleChoice.MEMBER
        )
        url = reverse("organization_member_list", kwargs={"org_id": self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Owner + Member
