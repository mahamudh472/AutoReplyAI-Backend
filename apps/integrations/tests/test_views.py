from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core import signing
from django.utils import timezone
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError
from ..models import Integration, MessageLog, MetaUserToken
from apps.organizations.services import get_user_organization
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
            organization=get_user_organization(self.user),
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
            organization=get_user_organization(self.other_user),
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

    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.unsubscribe_page_from_app")
    def test_delete_integration_unsubscribes(self, mock_unsubscribe):
        url = reverse("integration_detail", kwargs={"pk": self.integration.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_unsubscribe.assert_called_once_with("1234567890", "fake-page-token-123")

    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.subscribe_page_to_app")
    def test_create_facebook_page_integration_subscribes(self, mock_subscribe):
        url = reverse("integration_list_create")
        data = {
            "platform": PlatformChoice.FACEBOOK_PAGE,
            "name": "New FB Page",
            "access_token": "new-fb-token",
            "platform_identifier": "99887766",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_subscribe.assert_called_once_with("99887766", "new-fb-token")

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


class MetaConnectAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user1@example.com",
            password="testpassword123",
            full_name="User One"
        )
        self.client.force_authenticate(user=self.user)

    @override_settings(META_CLIENT_ID="test-client-id", META_REDIRECT_URI="http://test-redirect-uri")
    def test_meta_connect_url_generation(self):
        url = reverse("meta_connect")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("authorization_url", response.data)
        auth_url = response.data["authorization_url"]
        self.assertIn("client_id=test-client-id", auth_url)
        self.assertIn("redirect_uri=http%3A%2F%2Ftest-redirect-uri", auth_url)
        self.assertIn("state=", auth_url)

    @override_settings(META_FRONTEND_REDIRECT_URL="http://test-frontend")
    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.get_user_access_token")
    def test_meta_callback_success(self, mock_get_token):
        mock_get_token.return_value = {
            "access_token": "long-lived-user-token",
            "expires_in": 5183999
        }
        
        # Generate valid state
        state = signing.dumps({"user_id": str(self.user.id)})
        url = f"{reverse('meta_callback')}?code=auth-code-123&state={state}"
        
        response = self.client.get(url)
        # Should redirect to frontend
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response.url.startswith("http://test-frontend?success=true"))
        
        # Verify db entry
        token_entry = MetaUserToken.objects.get(user=self.user)
        self.assertEqual(token_entry.access_token, "long-lived-user-token")
        self.assertIsNotNone(token_entry.expires_at)

    @override_settings(META_FRONTEND_REDIRECT_URL="http://test-frontend")
    def test_meta_callback_invalid_state(self):
        url = f"{reverse('meta_callback')}?code=auth-code-123&state=invalidstate"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response.url.startswith("http://test-frontend?error=invalid_state"))

    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.get_user_pages")
    def test_meta_pages_list(self, mock_get_pages):
        mock_get_pages.return_value = [
            {"id": "page-1", "name": "FB Page 1", "category": "Tech", "access_token": "page-tok-1", "tasks": ["MANAGE"]},
            {"id": "page-2", "name": "FB Page 2", "category": "Art", "access_token": "page-tok-2", "tasks": ["MESSAGING"]}
        ]
        
        # Set token in db
        MetaUserToken.objects.create(
            user=self.user,
            access_token="valid-token",
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )
        
        url = reverse("meta_pages")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["id"], "page-1")
        self.assertEqual(response.data[0]["name"], "FB Page 1")
        # Ensure access token is NOT exposed
        self.assertNotIn("access_token", response.data[0])

    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.subscribe_page_to_app")
    @patch("apps.integrations.services.meta_auth_service.MetaAuthService.get_user_pages")
    def test_meta_select_page(self, mock_get_pages, mock_subscribe):
        mock_get_pages.return_value = [
            {"id": "page-1", "name": "FB Page 1", "category": "Tech", "access_token": "page-tok-1", "tasks": ["MANAGE"]}
        ]
        
        MetaUserToken.objects.create(
            user=self.user,
            access_token="valid-token",
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )
        
        url = reverse("meta_select_page")
        response = self.client.post(url, {"page_id": "page-1"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["platform_identifier"], "page-1")
        self.assertEqual(response.data["name"], "FB Page 1")
        
        # Verify saved in integration db
        integration = Integration.objects.get(user=self.user, platform=PlatformChoice.FACEBOOK_PAGE)
        self.assertEqual(integration.access_token, "page-tok-1")
        self.assertEqual(integration.platform_identifier, "page-1")
        self.assertEqual(integration.additional_data, {"category": "Tech", "tasks": ["MANAGE"]})
        mock_subscribe.assert_called_once_with("page-1", "page-tok-1")



class MetaWebhookAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="testpassword123",
            full_name="Webhook User"
        )
        org = get_user_organization(self.user)
        self.fb_integration = Integration.objects.create(
            organization=org,
            user=self.user,
            platform=PlatformChoice.FACEBOOK_PAGE,
            name="FB Page Test",
            access_token="fb-page-access-token",
            platform_identifier="page_12345"
        )
        self.ig_integration = Integration.objects.create(
            organization=org,
            user=self.user,
            platform=PlatformChoice.INSTAGRAM,
            name="IG Test",
            access_token="ig-access-token",
            platform_identifier="ig_12345"
        )
        self.wa_integration = Integration.objects.create(
            organization=org,
            user=self.user,
            platform=PlatformChoice.WHATSAPP_BUSINESS,
            name="WA Test",
            access_token="wa-access-token",
            platform_identifier="phone_12345"
        )

    @override_settings(META_WEBHOOK_VERIFY_TOKEN="my-secret-verify-token")
    def test_webhook_verification_success(self):
        url = reverse("meta_webhook")
        response = self.client.get(url, {
            "hub.mode": "subscribe",
            "hub.verify_token": "my-secret-verify-token",
            "hub.challenge": "1158201444"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content.decode("utf-8"), "1158201444")

    @override_settings(META_WEBHOOK_VERIFY_TOKEN="my-secret-verify-token")
    def test_webhook_verification_invalid_token(self):
        url = reverse("meta_webhook")
        response = self.client.get(url, {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong-token",
            "hub.challenge": "1158201444"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(META_WEBHOOK_VERIFY_TOKEN="my-secret-verify-token")
    def test_webhook_verification_invalid_mode(self):
        url = reverse("meta_webhook")
        response = self.client.get(url, {
            "hub.mode": "invalid_mode",
            "hub.verify_token": "my-secret-verify-token",
            "hub.challenge": "1158201444"
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.integrations.services.message_service.MetaMessageService.send_message")
    def test_webhook_post_facebook_page_message(self, mock_send_message):
        mock_send_message.return_value = (True, "mid.reply_123", {"message_id": "mid.reply_123"})
        url = reverse("meta_webhook")
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": "page_12345",
                    "time": 1458692752478,
                    "messaging": [
                        {
                            "sender": {"id": "user_psid_1"},
                            "recipient": {"id": "page_12345"},
                            "timestamp": 1458692752478,
                            "message": {
                                "mid": "mid.incoming_1",
                                "text": "Hi there!"
                            }
                        }
                    ]
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "EVENT_RECEIVED")
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(kwargs.get("integration") or args[0], self.fb_integration)
        self.assertEqual(kwargs.get("recipient_id") or args[1], "user_psid_1")

    @patch("apps.integrations.services.message_service.MetaMessageService.send_message")
    def test_webhook_post_instagram_message(self, mock_send_message):
        mock_send_message.return_value = (True, "mid.ig_reply_123", {"message_id": "mid.ig_reply_123"})
        url = reverse("meta_webhook")
        payload = {
            "object": "instagram",
            "entry": [
                {
                    "id": "ig_12345",
                    "time": 1458692752478,
                    "messaging": [
                        {
                            "sender": {"id": "ig_user_1"},
                            "recipient": {"id": "ig_12345"},
                            "timestamp": 1458692752478,
                            "message": {
                                "mid": "mid.ig_incoming_1",
                                "text": "Hello Instagram!"
                            }
                        }
                    ]
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "EVENT_RECEIVED")
        mock_send_message.assert_called_once()

    @patch("apps.integrations.services.message_service.MetaMessageService.send_message")
    def test_webhook_post_whatsapp_message(self, mock_send_message):
        mock_send_message.return_value = (True, "wamid.reply_123", {"messages": [{"id": "wamid.reply_123"}]})
        url = reverse("meta_webhook")
        payload = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "waba_12345",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "metadata": {
                                    "phone_number_id": "phone_12345",
                                    "display_phone_number": "15550254321"
                                },
                                "messages": [
                                    {
                                        "from": "16315551234",
                                        "id": "wamid.in_123",
                                        "type": "text",
                                        "text": {"body": "Hello WhatsApp!"}
                                    }
                                ]
                            },
                            "field": "messages"
                        }
                    ]
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "EVENT_RECEIVED")
        mock_send_message.assert_called_once()
        args, kwargs = mock_send_message.call_args
        self.assertEqual(kwargs.get("integration") or args[0], self.wa_integration)
        self.assertEqual(kwargs.get("recipient_id") or args[1], "16315551234")

    @patch("apps.integrations.services.message_service.MetaMessageService.send_message")
    def test_webhook_post_echo_ignored(self, mock_send_message):
        url = reverse("meta_webhook")
        payload = {
            "object": "page",
            "entry": [
                {
                    "id": "page_12345",
                    "messaging": [
                        {
                            "sender": {"id": "page_12345"},
                            "recipient": {"id": "user_psid_1"},
                            "message": {
                                "mid": "mid.outgoing_echo_1",
                                "text": "Our bot message",
                                "is_echo": True
                            }
                        }
                    ]
                }
            ]
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_message.assert_not_called()


