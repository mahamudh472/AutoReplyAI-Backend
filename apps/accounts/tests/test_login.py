from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AccountsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )
        self.inactive_user = User.objects.create_user(
            email="inactive@example.com",
            password="testpassword123",
            full_name="Inactive User",
            is_active=False
        )

    def test_login_active_user_success(self):
        """Test that an active user can successfully log in and get JWT tokens."""
        url = reverse("login")
        data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_inactive_user_failure(self):
        """Test that login fails for an inactive user and triggers an OTP send."""
        url = reverse("login")
        data = {
            "email": "inactive@example.com",
            "password": "testpassword123"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"][0], "Account is not active. An OTP has been sent to your email for verification.")
        self.assertEqual(response.data["code"][0], "EMAIL_NOT_VERIFIED")

    def test_logout_missing_refresh_token(self):
        """Test that logout fails with 400 Bad Request if no refresh token is provided."""
        self.client.force_authenticate(user=self.user)
        url = reverse("logout")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Refresh token is required")

    def test_logout_invalid_refresh_token(self):
        """Test that logout fails with 400 Bad Request if an invalid refresh token is provided."""
        self.client.force_authenticate(user=self.user)
        url = reverse("logout")
        response = self.client.post(url, {"refresh_token": "invalidtoken"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_logout_success(self):
        """Test that logout succeeds when a valid refresh token is provided."""
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        url = reverse("logout")
        response = self.client.post(url, {"refresh_token": str(refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data["message"], "Successfully logged out")

    def test_get_profile(self):
        """Test that an authenticated user can get their profile details."""
        self.client.force_authenticate(user=self.user)
        url = reverse("profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["full_name"], "Test User")
        self.assertIn("id", response.data)
        # Ensure ID is a string (UUID format) and not an integer
        self.assertIsInstance(response.data["id"], str)
        self.assertNotEqual(response.data["id"], "")
