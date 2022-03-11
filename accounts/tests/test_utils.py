from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from accounts.models import Flag
from accounts.utils import get_flag


class GetFlagTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")

    def test_user_without_flag(self):
        # Act & Assert
        self.assertIsNone(get_flag(self.user))

    def test_user_with_flag(self):
        # Arrange
        flag = Flag.objects.create(user=self.user)

        # Act & Assert
        self.assertEqual(flag, get_flag(self.user))
