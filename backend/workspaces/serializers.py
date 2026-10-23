
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Workspace, WorkspaceMembership


class WorkspaceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Workspace

        fields = [
            "id",
            "name",
            "slug",
            "description",
            "created_by",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_by",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Workspace name must contain at least 3 characters."
            )

        return value

    def validate_slug(self, value):
        if value != value.lower():
            raise serializers.ValidationError(
                "Workspace slug must be lowercase."
            )

        return value



class WorkspaceMemberCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=get_user_model().objects.all(),
        write_only=True,
    )

    role = serializers.ChoiceField(
        choices=[
            WorkspaceMembership.Role.ADMIN,
            WorkspaceMembership.Role.MEMBER,
        ],
        default=WorkspaceMembership.Role.MEMBER,
    )

    class Meta:
        model = WorkspaceMembership
        fields = ["user_id", "role"]

    def validate(self, attrs):
        workspace = self.context.get("workspace")

        if workspace is None:
            raise serializers.ValidationError(
                "Workspace context is required."
            )

        if WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=attrs["user"],
        ).exists():
            raise serializers.ValidationError({
                "user_id": "User is already a workspace member."
            })

        return attrs


class WorkspaceMemberListSerializer(serializers.ModelSerializer):
    user_id = serializers.ReadOnlyField()
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = WorkspaceMembership

        fields = [
            "id",
            "user_id",
            "email",
            "role",
            "is_active",
            "joined_at",
        ]

        read_only_fields = fields
