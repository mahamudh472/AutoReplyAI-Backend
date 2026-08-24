from rest_framework import serializers
from .models import Organization, OrganizationMember
from apps.accounts.serializers import UserSerializer


class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = OrganizationMember
        fields = (
            "id",
            "organization",
            "user",
            "user_email",
            "user_full_name",
            "role",
            "created_at",
            "updated_at"
        )
        read_only_fields = ("id", "created_at", "updated_at")


class OrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    members_count = serializers.IntegerField(source="members.count", read_only=True)

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "owner",
            "owner_email",
            "members_count",
            "created_at",
            "updated_at"
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")
