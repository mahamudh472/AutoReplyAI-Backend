from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    ListAPIView,
    GenericAPIView
)
from django.shortcuts import get_object_or_404
from .models import Integration, MessageLog, MetaUserToken
from .serializers import IntegrationSerializer, MessageLogSerializer
from .services.message_service import MetaMessageService
from typing import Any, Dict

import urllib.parse
from django.conf import settings
from django.core import signing
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from .services.meta_auth_service import MetaAuthService, MetaAuthError


class IntegrationListCreateView(ListCreateAPIView):
    """
    List integrations or create a new integration connection.
    """
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return integrations belonging to the authenticated user
        return Integration.objects.filter(user=self.request.user)


class IntegrationDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an integration connection.
    """
    serializer_class = IntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Prevent accessing other users' integrations
        return Integration.objects.filter(user=self.request.user)


class MessageLogListView(ListAPIView):
    """
    List history/logs of messages sent through user integrations.
    """
    serializer_class = MessageLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter logs for integrations belonging to the current user
        return MessageLog.objects.filter(integration__user=self.request.user)


class IntegrationSendMessageView(GenericAPIView):
    """
    Send a message through a specific integration on behalf of the user.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Integration.objects.filter(user=self.request.user)

    def post(self, request, pk=None) -> Response:
        integration = get_object_or_404(self.get_queryset(), pk=pk)

        recipient_id = request.data.get("recipient_id")
        message_content = request.data.get("message_content")

        if not recipient_id or not message_content:
            return Response(
                {"error": "Both 'recipient_id' and 'message_content' are required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call service layer to dispatch message to Meta platform
        success, info, payload = MetaMessageService.send_message(
            integration=integration,
            recipient_id=recipient_id,
            message_content=message_content
        )

        if success:
            return Response({
                "message": "Message sent successfully.",
                "platform_message_id": info,
                "response": payload
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error": "Failed to send message.",
                "detail": info
            }, status=status.HTTP_400_BAD_REQUEST)


class MetaConnectView(APIView):
    """
    Endpoint that generates the Meta OAuth URL.
    GET /api/v1/integrations/meta/connect/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        client_id = getattr(settings, "META_CLIENT_ID", "")
        redirect_uri = getattr(settings, "META_REDIRECT_URI", "")

        if not client_id or not redirect_uri:
            return Response(
                {"error": "Meta App is not configured properly on the backend. Missing META_CLIENT_ID or META_REDIRECT_URI."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Generate signed state containing the user's ID
        state = signing.dumps({"user_id": str(request.user.id)})

        # Prepare scopes
        scopes = [
            "pages_show_list",
            "pages_messaging",
            "pages_read_engagement",
            "pages_manage_metadata"
        ]

        # Construct oauth url
        oauth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(scopes),
            "response_type": "code"
        }
        oauth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urllib.parse.urlencode(oauth_params)}"

        return Response({"authorization_url": oauth_url}, status=status.HTTP_200_OK)


class MetaCallbackView(APIView):
    """
    Meta OAuth Callback Endpoint.
    GET /api/v1/integrations/meta/callback/
    """
    permission_classes = [AllowAny]

    def get(self, request) -> HttpResponseRedirect:
        code = request.GET.get("code")
        state = request.GET.get("state")
        error_reason = request.GET.get("error_description") or request.GET.get("error")

        frontend_redirect_url = getattr(settings, "META_FRONTEND_REDIRECT_URL", "")
        if not frontend_redirect_url:
            frontend_redirect_url = "/"

        if error_reason:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error={urllib.parse.quote(error_reason)}")

        if not code or not state:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error=missing_code_or_state")

        # 1. Unsign and verify state
        try:
            state_data = signing.loads(state, max_age=3600)  # expires in 1 hour
            user_id = state_data.get("user_id")
        except signing.SignatureExpired:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error=state_expired")
        except signing.BadSignature:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error=invalid_state")

        # Find the user matching the ID
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error=user_not_found")

        # 2. Exchange authorization code for token (and upgrade to long-lived)
        try:
            token_data = MetaAuthService.get_user_access_token(code)
        except MetaAuthError as e:
            return HttpResponseRedirect(f"{frontend_redirect_url}?error={urllib.parse.quote(str(e))}")

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in")

        # Calculate expires_at
        expires_at = None
        if expires_in:
            expires_at = timezone.now() + timezone.timedelta(seconds=int(expires_in))

        # 3. Save/update to database
        MetaUserToken.objects.update_or_create(
            user=user,
            defaults={
                "access_token": access_token,
                "expires_at": expires_at
            }
        )

        return HttpResponseRedirect(f"{frontend_redirect_url}?success=true")


class MetaPagesListView(APIView):
    """
    Fetch the list of Facebook Pages that the authenticated user has access to.
    GET /api/v1/integrations/meta/pages/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        try:
            user_token = MetaUserToken.objects.get(user=request.user)
        except MetaUserToken.DoesNotExist:
            return Response(
                {"error": "No connected Meta account found. Please connect your Facebook account first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if expired
        if user_token.expires_at and user_token.expires_at < timezone.now():
            return Response(
                {"error": "Your Meta connection has expired. Please reconnect your Facebook account."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pages = MetaAuthService.get_user_pages(user_token.access_token)
        except MetaAuthError as e:
            return Response(
                {"error": f"Failed to retrieve pages: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Return page info: id, name, category, tasks (excluding sensitive page access token)
        filtered_pages = []
        for page in pages:
            filtered_pages.append({
                "id": page.get("id"),
                "name": page.get("name"),
                "category": page.get("category"),
                "tasks": page.get("tasks")
            })

        return Response(filtered_pages, status=status.HTTP_200_OK)


class MetaSelectPageView(APIView):
    """
    Selects a page and saves/updates it in the Integration database.
    POST /api/v1/integrations/meta/select-page/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request) -> Response:
        page_id = request.data.get("page_id")
        if not page_id:
            return Response(
                {"error": "page_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_token = MetaUserToken.objects.get(user=request.user)
        except MetaUserToken.DoesNotExist:
            return Response(
                {"error": "No connected Meta account found. Please connect your Facebook account first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrieve pages to extract the access token for this specific page
        try:
            pages = MetaAuthService.get_user_pages(user_token.access_token)
        except MetaAuthError as e:
            return Response(
                {"error": f"Failed to retrieve pages: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Find the selected page in the list
        selected_page = None
        for page in pages:
            if str(page.get("id")) == str(page_id):
                selected_page = page
                break

        if not selected_page:
            return Response(
                {"error": "Selected page not found or access not granted by user."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Retrieve details
        page_name = selected_page.get("name")
        page_access_token = selected_page.get("access_token")
        category = selected_page.get("category")
        tasks = selected_page.get("tasks")

        # Save/update the Integration in db
        from common.enums import PlatformChoice
        integration, created = Integration.objects.update_or_create(
            user=request.user,
            platform=PlatformChoice.FACEBOOK_PAGE,
            platform_identifier=str(page_id),
            defaults={
                "name": page_name,
                "access_token": page_access_token,
                "is_active": True,
                "additional_data": {
                    "category": category,
                    "tasks": tasks
                }
            }
        )

        serializer = IntegrationSerializer(integration)
        return Response(serializer.data, status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED)

