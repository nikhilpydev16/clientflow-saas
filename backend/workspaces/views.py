
from django.db import transaction
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from .models import Workspace, WorkspaceMembership
from .serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Workspace.objects.all()

    def get_queryset(self):
        return Workspace.objects.filter(
            memberships__user=self.request.user,
            memberships__is_active=True,
            is_active=True,
        ).distinct()

    @transaction.atomic
    def perform_create(self, serializer):
        workspace = serializer.save(
            created_by=self.request.user
        )

        WorkspaceMembership.objects.create(
            workspace=workspace,
            user=self.request.user,
            role=WorkspaceMembership.Role.OWNER,
        )

    def get_current_membership(self, workspace):
        membership = WorkspaceMembership.objects.filter(
            workspace=workspace,
            user=self.request.user,
            is_active=True,
        ).first()

        if membership is None:
            raise PermissionDenied(
                "You are not an active workspace member."
            )

        return membership

    def perform_update(self, serializer):
        workspace = serializer.instance
        membership = self.get_current_membership(workspace)

        allowed_roles = [
            WorkspaceMembership.Role.OWNER,
            WorkspaceMembership.Role.ADMIN,
        ]

        if membership.role not in allowed_roles:
            raise PermissionDenied(
                "Only owners and admins can update workspaces."
            )

        serializer.save()

    def perform_destroy(self, instance):
        membership = self.get_current_membership(instance)

        if membership.role != WorkspaceMembership.Role.OWNER:
            raise PermissionDenied(
                "Only workspace owners can delete workspaces."
            )

        instance.delete()
