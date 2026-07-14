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
from .models import Integration, MessageLog
from .serializers import IntegrationSerializer, MessageLogSerializer
from .services.message_service import MetaMessageService
from typing import Any, Dict

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
