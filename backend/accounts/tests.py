from django.contrib.auth import authenticate, get_user_model
from django.test import TestCase


User = get_user_model()


class CustomUserTests(TestCase):

    def test_create_regular_user(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="StrongPass123!"
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="StrongPass123!"
        )

        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_email_required(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="StrongPass123!"
            )

    def test_email_authentication(self):
        user = User.objects.create_user(
            email="login@example.com",
            password="StrongPass123!"
        )

        authenticated_user = authenticate(
            email="login@example.com",
            password="StrongPass123!"
        )

        self.assertEqual(authenticated_user, user)