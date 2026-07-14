from django.urls import path
from . import views

urlpatterns = [
    path("", views.IntegrationListCreateView.as_view(), name="integration_list_create"),
    path("<uuid:pk>/", views.IntegrationDetailView.as_view(), name="integration_detail"),
    path("<uuid:pk>/send-message/", views.IntegrationSendMessageView.as_view(), name="integration_send_message"),
    path("logs/", views.MessageLogListView.as_view(), name="message_log_list"),
]
