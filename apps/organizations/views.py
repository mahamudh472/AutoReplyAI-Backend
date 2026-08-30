from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    GenericAPIView,
    RetrieveUpdateDestroyAPIView,
    ListCreateAPIView
)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from common.enums import OrganizationRoleChoice
from .models import Organization, OrganizationMember, OrganizationSubscription
from .serializers import (
    OrganizationSerializer,
    OrganizationListSerializer,
    OrganizationMemberSerializer,
    OrganizationLogoUploadSerializer,
    OrganizationSubscriptionSerializer
)
from .services import get_user_organization


class OrganizationListCreateView(ListCreateAPIView):
    """
    GET /api/v1/organizations/
      - List all organizations belonging to the authenticated user.

    POST /api/v1/organizations/
      - Create a new organization.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return OrganizationListSerializer
        return OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()

    def perform_create(self, serializer):
        org = serializer.save(owner=self.request.user)
        # Add creator as OWNER member
        OrganizationMember.objects.get_or_create(
            organization=org,
            user=self.request.user,
            defaults={"role": OrganizationRoleChoice.OWNER}
        )
        # Initialize default subscription plan
        OrganizationSubscription.objects.get_or_create(
            organization=org,
            defaults={
                "plan_name": "Starter Plan",
                "status": "active",
                "billing_cycle": "monthly",
                "max_messages": 10000,
                "max_team_members": 1,
                "max_connected_accounts": 1,
                "renews_at": timezone.now() + timedelta(days=30),
            }
        )


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """
    GET /api/v1/organizations/{id}/
      - Retrieve details for a specific organization.

    PATCH / PUT /api/v1/organizations/{id}/
      - Update organization details (name, slug, language, timezone, description).

    DELETE /api/v1/organizations/{id}/
      - Permanently delete the organization.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()

    def delete(self, request, *args, **kwargs):
        org = self.get_object()
        # Verify ownership / permissions if needed
        if org.owner != request.user:
            # Check if user is OWNER in OrganizationMember
            is_owner_member = org.members.filter(user=request.user, role=OrganizationRoleChoice.OWNER).exists()
            if not is_owner_member:
                return Response(
                    {"error": "Only the organization owner can delete this organization."},
                    status=status.HTTP_403_FORBIDDEN
                )

        if org.logo:
            org.logo.delete(save=False)
        org.delete()
        return Response(
            {"success": True, "message": "Organization has been permanently deleted."},
            status=status.HTTP_200_OK
        )


class OrganizationLogoView(GenericAPIView):
    """
    POST /api/v1/organizations/{id}/logo/
      - Upload / change organization logo (multipart/form-data).

    DELETE /api/v1/organizations/{id}/logo/
      - Remove organization logo.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()

    def post(self, request, pk=None) -> Response:
        org = get_object_or_404(self.get_queryset(), pk=pk)

        serializer = OrganizationLogoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Delete previous logo file if exists
        if org.logo:
            org.logo.delete(save=False)

        org.logo = serializer.validated_data["logo"]
        org.save(update_fields=["logo", "updated_at"])

        logo_url = request.build_absolute_uri(org.logo.url)
        return Response({
            "success": True,
            "logo_url": logo_url
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk=None) -> Response:
        org = get_object_or_404(self.get_queryset(), pk=pk)

        if org.logo:
            org.logo.delete(save=False)
            org.logo = None
            org.save(update_fields=["logo", "updated_at"])

        return Response({
            "success": True,
            "message": "Logo removed successfully",
            "logo_url": None
        }, status=status.HTTP_200_OK)


class OrganizationSubscriptionView(GenericAPIView):
    """
    GET /api/v1/organizations/{id}/subscription/
      - Get current subscription plan & usage summary for the organization.
    """
    serializer_class = OrganizationSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()

    def get(self, request, pk=None) -> Response:
        org = get_object_or_404(self.get_queryset(), pk=pk)

        # Get or lazily create default Starter subscription
        subscription, _ = OrganizationSubscription.objects.get_or_create(
            organization=org,
            defaults={
                "plan_name": "Starter Plan",
                "status": "active",
                "billing_cycle": "monthly",
                "max_messages": 10000,
                "max_team_members": 1,
                "max_connected_accounts": 1,
                "renews_at": timezone.now() + timedelta(days=30),
            }
        )

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationCurrentView(GenericAPIView):
    """
    Get the primary organization for the currently authenticated user.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request) -> Response:
        org = get_user_organization(request.user)
        if not org:
            return Response({"error": "No organization found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(org)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OrganizationMemberListView(ListCreateAPIView):
    """
    List members of an organization or invite/add a new member.
    """
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        org_id = self.kwargs.get("org_id")
        return OrganizationMember.objects.filter(
            organization_id=org_id,
            organization__members__user=self.request.user
        ).select_related("user", "organization")

    def perform_create(self, serializer):
        org_id = self.kwargs.get("org_id")
        org = get_object_or_404(
            Organization.objects.filter(
                members__user=self.request.user,
                members__role__in=[OrganizationRoleChoice.OWNER, OrganizationRoleChoice.ADMIN]
            ),
            id=org_id
        )
        serializer.save(organization=org)
