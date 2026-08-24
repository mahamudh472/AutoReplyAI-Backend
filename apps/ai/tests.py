from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.services import get_user_organization
from common.enums import OrganizationRoleChoice
from .models import AISettings

User = get_user_model()


class AISettingsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ai_user@example.com",
            password="testpassword123",
            full_name="AI Test User"
        )
        self.client.force_authenticate(user=self.user)
        self.org = get_user_organization(self.user)

    def test_get_ai_settings_creates_default(self):
        """GET /api/v1/ai/settings/ creates and returns default AISettings for the user's organization."""
        url = reverse("ai_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["organization_id"], str(self.org.id))
        self.assertEqual(response.data["organization_name"], self.org.name)
        self.assertEqual(response.data["provider"], "openai")
        self.assertEqual(response.data["model_name"], "gpt-4o-mini")
        self.assertTrue(response.data["is_enabled"])
        self.assertEqual(response.data["tone"], "professional")
        self.assertEqual(response.data["temperature"], 0.7)
        self.assertEqual(response.data["max_tokens"], 500)

        # Verify DB entry exists
        self.assertTrue(AISettings.objects.filter(organization=self.org).exists())

    def test_update_ai_settings_patch(self):
        """PATCH /api/v1/ai/settings/ updates specified fields for the organization's settings."""
        url = reverse("ai_settings")
        update_data = {
            "provider": "gemini",
            "model_name": "gemini-1.5-flash",
            "tone": "friendly",
            "temperature": 0.3,
            "max_tokens": 1000,
            "business_name": "Acme Widgets",
            "system_prompt": "Custom tailored prompt for widgets support.",
            "is_enabled": False
        }
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["provider"], "gemini")
        self.assertEqual(response.data["model_name"], "gemini-1.5-flash")
        self.assertEqual(response.data["tone"], "friendly")
        self.assertEqual(response.data["temperature"], 0.3)
        self.assertEqual(response.data["max_tokens"], 1000)
        self.assertEqual(response.data["business_name"], "Acme Widgets")
        self.assertEqual(response.data["system_prompt"], "Custom tailored prompt for widgets support.")
        self.assertFalse(response.data["is_enabled"])

        # Verify persisted in DB
        db_settings = AISettings.objects.get(organization=self.org)
        self.assertEqual(db_settings.provider, "gemini")
        self.assertEqual(db_settings.tone, "friendly")
        self.assertFalse(db_settings.is_enabled)

    def test_queries_first_organization_for_user(self):
        """If user belongs to multiple organizations, queries the first organization from the queryset."""
        second_org = Organization.objects.create(
            name="Second Org",
            owner=self.user
        )
        OrganizationMember.objects.create(
            organization=second_org,
            user=self.user,
            role=OrganizationRoleChoice.OWNER
        )

        url = reverse("ai_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should match the first organization in Organization.objects.filter(members__user=user)
        expected_first_org = Organization.objects.filter(members__user=self.user).first()
        self.assertEqual(response.data["organization_id"], str(expected_first_org.id))

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        url = reverse("ai_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
