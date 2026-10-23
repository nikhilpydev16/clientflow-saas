
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Workspace, WorkspaceMembership
from .serializers import (
    WorkspaceSerializer,
    WorkspaceMemberCreateSerializer,
    WorkspaceMemberListSerializer,
)


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

    # ----------------------------------------
    # UPDATE WORKSPACE
    # ----------------------------------------
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

    # ----------------------------------------
    # DELETE WORKSPACE
    # ----------------------------------------
    def perform_destroy(self, instance):
        membership = self.get_current_membership(instance)

        if membership.role != WorkspaceMembership.Role.OWNER:
            raise PermissionDenied(
                "Only workspace owners can delete workspaces."
            )

        instance.delete()

    # ----------------------------------------
    # GET MEMBERS / ADD MEMBER
    # ----------------------------------------
    @action(
        detail=True,
        methods=["get", "post"],
        url_path="members",
    )
    @transaction.atomic
    def members(self, request, pk=None):
        workspace = self.get_object()

        # GET - List active workspace members
        if request.method == "GET":
            memberships = (
                WorkspaceMembership.objects.filter(
                    workspace=workspace,
                    is_active=True,
                )
                .select_related("user")
                .order_by("id")
            )

            serializer = WorkspaceMemberListSerializer(
                memberships,
                many=True,
            )

            return Response(serializer.data)

        # POST - Add workspace member
        current_membership = self.get_current_membership(
            workspace
        )

        allowed_roles = [
            WorkspaceMembership.Role.OWNER,
            WorkspaceMembership.Role.ADMIN,
        ]

        if current_membership.role not in allowed_roles:
            raise PermissionDenied(
                "Only owners and admins can add members."
            )

        serializer = WorkspaceMemberCreateSerializer(
            data=request.data,
            context={"workspace": workspace},
        )
        serializer.is_valid(raise_exception=True)

        membership = serializer.save(
            workspace=workspace
        )

        return Response(
            {
                "id": membership.id,
                "user_id": membership.user_id,
                "role": membership.role,
                "is_active": membership.is_active,
                "joined_at": membership.joined_at,
            },
            status=status.HTTP_201_CREATED,
        )

    # ----------------------------------------
    # CHANGE MEMBER ROLE
    # ----------------------------------------
    @action(
        detail=True,
        methods=["patch"],
        url_path=r"members/(?P<user_id>\d+)/role",
    )
    @transaction.atomic
    def change_member_role(
        self, request, pk=None, user_id=None
    ):
        workspace = self.get_object()

        # Get current user's membership
        current_membership = self.get_current_membership(
            workspace
        )

        # Only owner can change roles
        if (
            current_membership.role
            != WorkspaceMembership.Role.OWNER
        ):
            raise PermissionDenied(
                "Only workspace owners can change member roles."
            )

        # Find target member
        membership = get_object_or_404(
            WorkspaceMembership,
            workspace=workspace,
            user_id=user_id,
            is_active=True,
        )

        # Prevent changing owner role
        if membership.role == WorkspaceMembership.Role.OWNER:
            raise PermissionDenied(
                "Workspace owner role cannot be changed."
            )

        new_role = request.data.get("role")

        allowed_roles = [
            WorkspaceMembership.Role.ADMIN,
            WorkspaceMembership.Role.MEMBER,
        ]

        if new_role not in allowed_roles:
            raise ValidationError({
                "role": "Role must be admin or member."
            })

        # Save updated role
        membership.role = new_role
        membership.save(
            update_fields=["role"]
        )

        return Response(
            {
                "message": "Member role updated successfully.",
                "user_id": membership.user_id,
                "role": membership.role,
            },
            status=status.HTTP_200_OK,
        )



    # ----------------------------------------
    # REMOVE WORKSPACE MEMBER
    # ----------------------------------------
    @action(
        detail=True,
        methods=["delete"],
        url_path=r"members/(?P<user_id>\d+)",
    )
    @transaction.atomic
    def remove_member(self, request, pk=None, user_id=None):
        workspace = self.get_object()

        # Check current user's membership
        current_membership = self.get_current_membership(
            workspace
        )

        # Only owner can remove members
        if current_membership.role != WorkspaceMembership.Role.OWNER:
            raise PermissionDenied(
                "Only workspace owners can remove members."
            )

        # Find target member
        membership = get_object_or_404(
            WorkspaceMembership,
            workspace=workspace,
            user_id=user_id,
            is_active=True,
        )

        # Prevent owner removal
        if membership.role == WorkspaceMembership.Role.OWNER:
            raise PermissionDenied(
                "Workspace owner cannot be removed."
            )

        # Soft remove member
        membership.is_active = False
        membership.save(update_fields=["is_active"])

        return Response(
            {
                "message": "Member removed successfully.",
                "user_id": membership.user_id,
                "is_active": membership.is_active,
            },
            status=status.HTTP_200_OK,
        )
