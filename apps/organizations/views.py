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
from common.enums import OrganizationRoleChoice
from .models import Organization, OrganizationMember
from .serializers import OrganizationSerializer, OrganizationMemberSerializer
from .services import get_user_organization


class OrganizationListCreateView(ListCreateAPIView):
    """
    List organizations the authenticated user is a member of or create a new organization.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

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


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an organization (only if member/owner).
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()


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
            Organization.objects.filter(members__user=self.request.user, members__role__in=[OrganizationRoleChoice.OWNER, OrganizationRoleChoice.ADMIN]),
            id=org_id
        )
        serializer.save(organization=org)
