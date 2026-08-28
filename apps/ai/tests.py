import io
import json
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.organizations.models import Organization, OrganizationMember
from apps.organizations.services import get_user_organization
from common.enums import OrganizationRoleChoice, KnowledgeDocumentStatus, KnowledgeSourceType
from .models import AISettings, KnowledgeDocument, DocumentChunk

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
        expected_first_org = Organization.objects.filter(members__user=self.user).first()
        self.assertEqual(response.data["organization_id"], str(expected_first_org.id))

    def test_unauthenticated_access_denied(self):
        """Unauthenticated requests are rejected."""
        self.client.force_authenticate(user=None)
        url = reverse("ai_settings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class KnowledgeBaseAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="kb_user@example.com",
            password="testpassword123",
            full_name="KB User"
        )
        self.client.force_authenticate(user=self.user)
        self.org = get_user_organization(self.user)

    def test_upload_text_file_success(self):
        """Test uploading a .txt file extracts content and creates a pending document."""
        url = reverse("knowledge_document_upload")
        file_content = b"Welcome to AutoReplyAI support. Our return policy is 30 days."
        test_file = SimpleUploadedFile("faq_policy.txt", file_content, content_type="text/plain")

        data = {
            "file": test_file,
            "title": "Return Policy FAQ",
            "description": "FAQ regarding refunds and returns",
            "tags": json.dumps(["faq", "refunds"]),
            "metadata": json.dumps({"category": "policies", "version": "1.0"})
        }

        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Return Policy FAQ")
        self.assertEqual(response.data["file_name"], "faq_policy.txt")
        self.assertEqual(response.data["file_type"], "txt")
        self.assertEqual(response.data["status"], KnowledgeDocumentStatus.PENDING)
        self.assertEqual(response.data["raw_content"], "Welcome to AutoReplyAI support. Our return policy is 30 days.")
        self.assertEqual(response.data["tags"], ["faq", "refunds"])
        self.assertEqual(response.data["metadata"], {"category": "policies", "version": "1.0"})
        self.assertEqual(response.data["word_count"], 10)
        self.assertEqual(response.data["character_count"], len(file_content))

        # Verify DB entry
        doc = KnowledgeDocument.objects.get(id=response.data["id"])
        self.assertEqual(doc.organization, self.org)
        self.assertEqual(doc.created_by, self.user)

    def test_create_document_raw_text(self):
        """Test creating a document with raw text input without a file."""
        url = reverse("knowledge_document_list_create")
        data = {
            "title": "Shipping Info",
            "raw_content": "We ship globally via FedEx and DHL.",
            "source_type": KnowledgeSourceType.TEXT,
            "tags": ["shipping", "logistics"]
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Shipping Info")
        self.assertEqual(response.data["source_type"], KnowledgeSourceType.TEXT)
        self.assertEqual(response.data["raw_content"], "We ship globally via FedEx and DHL.")
        self.assertEqual(response.data["status"], KnowledgeDocumentStatus.PENDING)

    def test_list_knowledge_documents_with_filters(self):
        """Test listing documents and applying status, tag, and search query filters."""
        # Create 2 documents
        doc1 = KnowledgeDocument.objects.create(
            organization=self.org,
            title="Refund Guidelines",
            raw_content="Refunds are processed in 5-7 business days.",
            status=KnowledgeDocumentStatus.PENDING,
            tags=["refunds", "billing"],
            is_active=True
        )
        doc2 = KnowledgeDocument.objects.create(
            organization=self.org,
            title="Technical Troubleshooting",
            raw_content="Reset your router to fix Wi-Fi issues.",
            status=KnowledgeDocumentStatus.INDEXED,
            tags=["tech", "network"],
            is_active=False
        )

        url = reverse("knowledge_document_list_create")

        # 1. List all
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # 2. Filter by status=pending
        response = self.client.get(f"{url}?status=pending")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(doc1.id))

        # 3. Filter by is_active=false
        response = self.client.get(f"{url}?is_active=false")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(doc2.id))

        # 4. Filter by tag=refunds
        response = self.client.get(f"{url}?tag=refunds")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(doc1.id))

        # 5. Search query
        response = self.client.get(f"{url}?search=router")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(doc2.id))

    def test_retrieve_and_update_document(self):
        """Test retrieving and updating document details."""
        doc = KnowledgeDocument.objects.create(
            organization=self.org,
            title="Original Title",
            raw_content="Sample content."
        )
        url = reverse("knowledge_document_detail", kwargs={"pk": doc.id})

        # GET detail
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Original Title")

        # PATCH update
        patch_data = {
            "title": "Updated Title",
            "is_active": False,
            "tags": ["updated_tag"]
        }
        patch_res = self.client.patch(url, patch_data, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["title"], "Updated Title")
        self.assertFalse(patch_res.data["is_active"])
        self.assertEqual(patch_res.data["tags"], ["updated_tag"])

    def test_delete_document(self):
        """Test deleting a document."""
        doc = KnowledgeDocument.objects.create(
            organization=self.org,
            title="To Delete",
            raw_content="Temporary content."
        )
        url = reverse("knowledge_document_detail", kwargs={"pk": doc.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(KnowledgeDocument.objects.filter(id=doc.id).exists())
