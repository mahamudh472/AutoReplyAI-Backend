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
from django.db.models import Q
from apps.organizations.models import Organization
from apps.organizations.services import get_user_organization
from .models import AISettings, KnowledgeDocument, DocumentChunk
from .serializers import (
    AISettingsSerializer,
    KnowledgeDocumentSerializer,
    KnowledgeDocumentUploadSerializer,
    DocumentChunkSerializer
)
from .services import DocumentProcessingService


def _get_user_primary_organization(user):
    """
    Helper function to query the first organization for the authenticated user.
    """
    org = Organization.objects.filter(members__user=user).first()
    if not org:
        org = get_user_organization(user)
    return org


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
        return _get_user_primary_organization(self.request.user)

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


class KnowledgeDocumentListCreateView(GenericAPIView):
    """
    List and upload/create Knowledge Base documents for the user's organization.

    GET /api/v1/ai/knowledge-base/
      - Lists knowledge documents with optional filters:
        - `status`: filter by status (pending, processing, indexed, failed)
        - `source_type`: filter by source type (file, text, faq, url)
        - `is_active`: filter by active state (true/false)
        - `tag`: filter documents having a matching tag
        - `search`: search within title, description, or content

    POST /api/v1/ai/knowledge-base/
      - Upload text related files or submit raw text to be indexed later.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return KnowledgeDocumentUploadSerializer
        return KnowledgeDocumentSerializer

    def get_queryset(self):
        org = _get_user_primary_organization(self.request.user)
        if not org:
            return KnowledgeDocument.objects.none()

        qs = KnowledgeDocument.objects.filter(organization=org)

        # Filters
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        source_type_filter = self.request.query_params.get("source_type")
        if source_type_filter:
            qs = qs.filter(source_type=source_type_filter)

        is_active_filter = self.request.query_params.get("is_active")
        if is_active_filter is not None:
            if is_active_filter.lower() in ["true", "1"]:
                qs = qs.filter(is_active=True)
            elif is_active_filter.lower() in ["false", "0"]:
                qs = qs.filter(is_active=False)

        tag_filter = self.request.query_params.get("tag")
        if tag_filter:
            qs = qs.filter(tags__icontains=tag_filter)

        search_query = self.request.query_params.get("search")
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(file_name__icontains=search_query) |
                Q(raw_content__icontains=search_query)
            )

        return qs

    def get(self, request) -> Response:
        queryset = self.get_queryset()
        serializer = KnowledgeDocumentSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request) -> Response:
        org = _get_user_primary_organization(request.user)
        if not org:
            return Response(
                {"error": "No organization found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = KnowledgeDocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        document = DocumentProcessingService.create_document_from_upload(
            organization=org,
            user=request.user,
            file=validated_data.get("file"),
            title=validated_data.get("title"),
            description=validated_data.get("description"),
            raw_content=validated_data.get("raw_content"),
            tags=validated_data.get("tags"),
            metadata=validated_data.get("metadata"),
            source_type=validated_data.get("source_type"),
            is_active=validated_data.get("is_active", True)
        )

        response_serializer = KnowledgeDocumentSerializer(document, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class KnowledgeDocumentDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific Knowledge Base document.

    GET /api/v1/ai/knowledge-base/<uuid:pk>/
    PATCH /api/v1/ai/knowledge-base/<uuid:pk>/
    PUT /api/v1/ai/knowledge-base/<uuid:pk>/
    DELETE /api/v1/ai/knowledge-base/<uuid:pk>/
    """
    serializer_class = KnowledgeDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        org = _get_user_primary_organization(self.request.user)
        if not org:
            return KnowledgeDocument.objects.none()
        return KnowledgeDocument.objects.filter(organization=org)

    def perform_destroy(self, instance):
        # Delete underlying uploaded file if it exists
        if instance.file:
            instance.file.delete(save=False)
        instance.delete()
