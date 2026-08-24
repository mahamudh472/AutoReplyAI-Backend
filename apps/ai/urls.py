from django.urls import path
from . import views

urlpatterns = [
    path("settings/", views.AISettingsView.as_view(), name="ai_settings"),
]
