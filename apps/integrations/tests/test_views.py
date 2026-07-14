from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from ..models import Integration, MessageLog
from common.enums import PlatformChoice
import io

User = get_user_model()

class IntegrationAPITests(APITestCase):
    def setUp(self):
        # Create users
        self.user = User.objects.create_user(
            email="user1@example.com",
            password="testpassword123",
            full_name="User One"
        )
        self.other_user = User.objects.create_user(
            email="user2@example.com",
            password="testpassword123",
            full_name="User Two"
        )
        # Authenticate main user
        self.client.force_authenticate(user=self.user)

        # Create base integration for tests
        self.integration = Integration.objects.create(
            user=self.user,
            platform=PlatformChoice.FACEBOOK_PAGE,
            name="My FB Page",
            access_token="fake-page-token-123",
            platform_identifier="1234567890"
        )

    def test_list_integrations(self):
        """Test retrieving all integrations belonging to user."""
        # Create an integration for the other user to verify isolation
        Integration.objects.create(
            user=self.other_user,
            platform=PlatformChoice.WHATSAPP_BUSINESS,
            name="Other WA",
            access_token="other-token",
            platform_identifier="987654321"
        )

        url = reverse("integration_list_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return 1 integration belonging to self.user
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "My FB Page")

    def test_create_integration(self):
        """Test creating a new integration."""
        url = reverse("integration_list_create")
        data = {
            "platform": PlatformChoice.WHATSAPP_BUSINESS,
            "name": "My WhatsApp Biz",
            "access_token": "wa-token-xyz",
            "platform_identifier": "555-0199",
            "additional_data": {"waba_id": "waba_999"}
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Integration.objects.filter(user=self.user).count(), 2)

        # Verify access token is write_only and NOT returned in payload
        self.assertNotIn("access_token", response.data)

    def test_retrieve_integration_detail(self):
        """Test getting details of a single integration."""
        url = reverse("integration_detail", kwargs={"pk": self.integration.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "My FB Page")

    def test_unauthorized_access(self):
        """Test that other users cannot access details of this integration."""
        self.client.force_authenticate(user=self.other_user)
        url = reverse("integration_detail", kwargs={"pk": self.integration.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("urllib.request.urlopen")
    def test_send_message_success(self, mock_urlopen):
        """Test sending message successfully via mock."""
        # Setup mock response from Meta Graph API
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message_id": "mid.14567890"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url = reverse("integration_send_message", kwargs={"pk": self.integration.pk})
        data = {
            "recipient_id": "recipient_fb_id",
            "message_content": "Hello World!"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["platform_message_id"], "mid.14567890")

        # Verify log creation
        self.assertEqual(MessageLog.objects.filter(status="sent").count(), 1)

    @patch("urllib.request.urlopen")
    def test_send_message_failure(self, mock_urlopen):
        """Test sending message failure handling."""
        # Setup mock exception for Meta Graph API
        error_file = io.BytesIO(b'{"error":{"message":"Invalid OAuth access token."}}')
        mock_urlopen.side_effect = HTTPError(
            url="https://graph.facebook.com/v19.0/1234567890/messages",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=error_file
        )

        url = reverse("integration_send_message", kwargs={"pk": self.integration.pk})
        data = {
            "recipient_id": "recipient_fb_id",
            "message_content": "Hello World!"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid OAuth access token.", response.data["detail"])

        # Verify log failure logged
        log = MessageLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, "failed")
        self.assertEqual(log.error_message, "Invalid OAuth access token.")
