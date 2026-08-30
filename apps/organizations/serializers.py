from rest_framework import serializers
from .models import Organization, OrganizationMember, OrganizationSubscription


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


class OrganizationListSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "logo_url",
            "role",
        )
        read_only_fields = fields

    def get_logo_url(self, obj) -> str:
        if obj.logo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_role(self, obj) -> str:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if obj.owner_id == request.user.id:
                return "owner"
            membership = obj.members.filter(user=request.user).first()
            if membership:
                return membership.role.lower()
        return "member"


class OrganizationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    members_count = serializers.IntegerField(source="members.count", read_only=True)
    logo_url = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "logo_url",
            "default_language",
            "timezone",
            "description",
            "owner",
            "owner_email",
            "members_count",
            "created_at",
            "updated_at",
            "role",
        )
        read_only_fields = ("id", "owner", "owner_email", "members_count", "logo_url", "created_at", "updated_at", "role")

    def get_logo_url(self, obj) -> str:
        if obj.logo:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None

    def get_role(self, obj) -> str:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if obj.owner_id == request.user.id:
                return "owner"
            membership = obj.members.filter(user=request.user).first()
            if membership:
                return membership.role.lower()
        return "member"

    def validate_slug(self, value):
        if value:
            # Check unique slug excluding current instance if updating
            qs = Organization.objects.filter(slug=value)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError("Organization with this slug already exists.")
        return value

    def validate_description(self, value):
        if value and len(value) > 500:
            raise serializers.ValidationError("Ensure this field has no more than 500 characters.")
        return value


class OrganizationLogoUploadSerializer(serializers.Serializer):
    logo = serializers.FileField(required=True)

    def validate_logo(self, value):
        valid_extensions = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError("Unsupported file format. Please upload PNG, JPG, SVG, or WEBP.")
        # 2MB max file size
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Logo file size cannot exceed 2MB.")
        return value


class OrganizationSubscriptionSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationSubscription
        fields = (
            "plan_name",
            "status",
            "billing_cycle",
            "features",
            "renews_at"
        )
        read_only_fields = fields

    def get_features(self, obj):
        org = obj.organization
        # Calculate real-time usages
        used_team_members = org.members.count()
        used_connected_accounts = org.integrations.count() if hasattr(org, "integrations") else 0
        
        # Count message logs under this organization
        from apps.integrations.models import MessageLog
        used_messages = MessageLog.objects.filter(integration__organization=org).count()

        return {
            "max_messages": obj.max_messages,
            "used_messages": used_messages,
            "max_team_members": obj.max_team_members,
            "used_team_members": used_team_members,
            "max_connected_accounts": obj.max_connected_accounts,
            "used_connected_accounts": used_connected_accounts,
        }
