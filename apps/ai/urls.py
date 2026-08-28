from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.AISettingsView.as_view(), name="ai_settings"),
    path("knowledge-base/", views.KnowledgeDocumentListCreateView.as_view(), name="knowledge_document_list_create"),
    path("knowledge-base/upload/", views.KnowledgeDocumentListCreateView.as_view(), name="knowledge_document_upload"),
    path("knowledge-base/<uuid:pk>/", views.KnowledgeDocumentDetailView.as_view(), name="knowledge_document_detail"),
]
