from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from common.enums import OrganizationRoleChoice
from apps.organizations.models import Organization, OrganizationMember, OrganizationSubscription
from apps.organizations.services import create_default_organization_for_user, get_user_organization

User = get_user_model()


class OrganizationModelAndSignalTests(APITestCase):
    def test_active_user_auto_creates_organization_and_owner_member(self):
        """Creating an active user should automatically create an Organization, OWNER member, and Starter subscription."""
        user = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            full_name="Alice Owner"
        )
        # Check Organization
        org = Organization.objects.filter(owner=user).first()
        self.assertIsNotNone(org)
        self.assertEqual(org.name, "Alice Owner's Organization")
        self.assertTrue(org.slug.startswith("alice-owners-organization"))
        self.assertEqual(org.owner, user)

        # Check OrganizationMember with OWNER role
        member = OrganizationMember.objects.filter(organization=org, user=user).first()
        self.assertIsNotNone(member)
        self.assertEqual(member.role, OrganizationRoleChoice.OWNER)

        # Check Subscription
        self.assertTrue(OrganizationSubscription.objects.filter(organization=org).exists())

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
        """GET /api/v1/organizations/ returns list with id, name, slug, logo_url, and role."""
        url = reverse("organization_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.org.id))
        self.assertEqual(response.data[0]["name"], self.org.name)
        self.assertEqual(response.data[0]["slug"], self.org.slug)
        self.assertEqual(response.data[0]["role"], "owner")

    def test_get_organization_detail(self):
        """GET /api/v1/organizations/{id}/ returns detailed info including role, language, timezone."""
        url = reverse("organization_detail", kwargs={"pk": self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.org.id))
        self.assertEqual(response.data["name"], self.org.name)
        self.assertEqual(response.data["default_language"], "English")
        self.assertEqual(response.data["timezone"], "GMT+06:00")
        self.assertEqual(response.data["role"], "owner")

    def test_update_organization_settings_patch(self):
        """PATCH /api/v1/organizations/{id}/ updates name, slug, language, timezone, description."""
        url = reverse("organization_detail", kwargs={"pk": self.org.id})
        data = {
            "name": "ABC Store",
            "slug": "abc-store",
            "default_language": "Spanish",
            "timezone": "GMT+01:00",
            "description": "We sell high-quality products and provide excellent customer support."
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "ABC Store")
        self.assertEqual(response.data["slug"], "abc-store")
        self.assertEqual(response.data["default_language"], "Spanish")
        self.assertEqual(response.data["timezone"], "GMT+01:00")
        self.assertEqual(response.data["description"], "We sell high-quality products and provide excellent customer support.")

        # Verify in DB
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, "ABC Store")
        self.assertEqual(self.org.slug, "abc-store")

    def test_upload_and_remove_organization_logo(self):
        """POST and DELETE /api/v1/organizations/{id}/logo/"""
        url = reverse("organization_logo", kwargs={"pk": self.org.id})

        # 1. Upload logo (1x1 transparent PNG)
        png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        logo_file = SimpleUploadedFile("logo.png", png_bytes, content_type="image/png")

        post_res = self.client.post(url, {"logo": logo_file}, format="multipart")
        self.assertEqual(post_res.status_code, status.HTTP_200_OK)
        self.assertTrue(post_res.data["success"])
        self.assertIsNotNone(post_res.data["logo_url"])
        self.assertIn("logo", post_res.data["logo_url"])

        # 2. Remove logo
        del_res = self.client.delete(url)
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        self.assertTrue(del_res.data["success"])
        self.assertEqual(del_res.data["message"], "Logo removed successfully")
        self.assertIsNone(del_res.data["logo_url"])

    def test_get_organization_subscription(self):
        """GET /api/v1/organizations/{id}/subscription/ returns plan name, status, features with usage quotas."""
        url = reverse("organization_subscription", kwargs={"pk": self.org.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["plan_name"], "Starter Plan")
        self.assertEqual(response.data["status"], "active")
        self.assertEqual(response.data["billing_cycle"], "monthly")
        self.assertIn("features", response.data)
        self.assertEqual(response.data["features"]["max_messages"], 10000)
        self.assertEqual(response.data["features"]["used_messages"], 0)
        self.assertEqual(response.data["features"]["max_team_members"], 1)
        self.assertEqual(response.data["features"]["used_team_members"], 1)

    def test_delete_organization(self):
        """DELETE /api/v1/organizations/{id}/ permanently deletes the organization."""
        url = reverse("organization_detail", kwargs={"pk": self.org.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["message"], "Organization has been permanently deleted.")
        self.assertFalse(Organization.objects.filter(id=self.org.id).exists())

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
