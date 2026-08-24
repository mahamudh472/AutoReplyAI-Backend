from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import GenericAPIView
from apps.organizations.models import Organization
from apps.organizations.services import get_user_organization
from .models import AISettings
from .serializers import AISettingsSerializer


class AISettingsView(GenericAPIView):
    """
    Retrieve or update AI settings for the user's organization.
    Queries the first organization associated with the authenticated user.

    GET /api/v1/ai/settings/
      - Returns the current AI configuration for the user's organization.
    
    PATCH /api/v1/ai/settings/
      - Partially updates the AI configuration.

    PUT /api/v1/ai/settings/
      - Updates the AI configuration.
    """
    serializer_class = AISettingsSerializer
    permission_classes = [IsAuthenticated]

    def _get_organization(self):
        # Query the user's organization(s) and take the first one from the query
        org = Organization.objects.filter(members__user=self.request.user).first()
        if not org:
            org = get_user_organization(self.request.user)
        return org

    def _get_or_create_settings(self, org):
        ai_settings, _ = AISettings.objects.get_or_create(organization=org)
        return ai_settings

    def get(self, request) -> Response:
        org = self._get_organization()
        if not org:
            return Response(
                {"error": "No organization found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND
            )

        ai_settings = self._get_or_create_settings(org)
        serializer = self.get_serializer(ai_settings)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request) -> Response:
        org = self._get_organization()
        if not org:
            return Response(
                {"error": "No organization found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND
            )

        ai_settings = self._get_or_create_settings(org)
        serializer = self.get_serializer(ai_settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request) -> Response:
        return self.patch(request)
