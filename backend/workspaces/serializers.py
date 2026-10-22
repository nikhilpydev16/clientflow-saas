
from rest_framework import serializers
from .models import Workspace


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
