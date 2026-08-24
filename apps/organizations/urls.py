from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrganizationListCreateView.as_view(), name="organization_list_create"),
    path("current/", views.OrganizationCurrentView.as_view(), name="organization_current"),
    path("<uuid:pk>/", views.OrganizationDetailView.as_view(), name="organization_detail"),
    path("<uuid:org_id>/members/", views.OrganizationMemberListView.as_view(), name="organization_member_list"),
]
