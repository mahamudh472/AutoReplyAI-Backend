from django.urls import path
from . import views

urlpatterns = [
    path("", views.IntegrationListCreateView.as_view(), name="integration_list_create"),
    path("<uuid:pk>/", views.IntegrationDetailView.as_view(), name="integration_detail"),
    path("<uuid:pk>/send-message/", views.IntegrationSendMessageView.as_view(), name="integration_send_message"),
    path("logs/", views.MessageLogListView.as_view(), name="message_log_list"),
    path("meta/connect/", views.MetaConnectView.as_view(), name="meta_connect"),
    path("meta/callback/", views.MetaCallbackView.as_view(), name="meta_callback"),
    path("meta/pages/", views.MetaPagesListView.as_view(), name="meta_pages"),
    path("meta/select-page/", views.MetaSelectPageView.as_view(), name="meta_select_page"),
    path("meta/webhook/", views.MetaWebhookView.as_view(), name="meta_webhook"),
    path("webhook/", views.MetaWebhookView.as_view(), name="webhook"),
]
