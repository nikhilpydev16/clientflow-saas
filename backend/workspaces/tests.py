from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Workspace, WorkspaceMembership


class WorkspaceRBACTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        def create_user(role):
            return User.objects.create_user(
                **{
                    User.USERNAME_FIELD: f"{role}@example.com",
                    "password": "TestPassword123!"
                }
            )

        cls.owner = create_user("owner")
        cls.admin = create_user("admin")
        cls.member = create_user("member")
        cls.non_member = create_user("nonmember")

        cls.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
            description="Original description",
            created_by=cls.owner,
        )

        for user, role in [
            (cls.owner, WorkspaceMembership.Role.OWNER),
            (cls.admin, WorkspaceMembership.Role.ADMIN),
            (cls.member, WorkspaceMembership.Role.MEMBER),
        ]:
            WorkspaceMembership.objects.create(
                workspace=cls.workspace,
                user=user,
                role=role,
                is_active=True,
            )

    def setUp(self):
        self.api = APIClient()
        self.url = f"/api/workspaces/{self.workspace.pk}/"

    def patch_as(self, user):
        self.api.force_authenticate(user=user)
        return self.api.patch(
            self.url,
            {"description": "Updated description"},
            format="json",
        )

    def test_owner_can_update_workspace(self):
        response = self.patch_as(self.owner)
        self.assertEqual(response.status_code, 200)

    def test_admin_can_update_workspace(self):
        response = self.patch_as(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_member_cannot_update_workspace(self):
        response = self.patch_as(self.member)
        self.assertEqual(response.status_code, 403)

    def test_non_member_cannot_update_workspace(self):
        response = self.patch_as(self.non_member)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cannot_update(self):
        response = self.api.patch(
            self.url,
            {"description": "Unauthorized update"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_admin_cannot_delete_workspace(self):
        self.api.force_authenticate(user=self.admin)
        response = self.api.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_delete_workspace(self):
        self.api.force_authenticate(user=self.member)
        response = self.api.delete(self.url)
        self.assertEqual(response.status_code, 403)