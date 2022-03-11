from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory

from accounts.models import Flag
from accounts.utils import get_flag


class GetFlagTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create(username="patient_user")
        self.staff_user = User.objects.create(username="staff_user")

    def test_user_without_flag(self):
        """
        Test that trying to get a flag that doesn't exist returns None
        @return:
        """
        # Act & Assert
        self.assertIsNone(get_flag(self.staff_user, self.patient_user))

    def test_user_with_flag(self):
        """
        Test that getting a flag that exists returns the flag
        @return:
        """
        # Arrange
        flag = Flag.objects.create(patient=self.patient_user, staff=self.staff_user)

        # Act & Assert
        self.assertEqual(flag, get_flag(self.staff_user,self.patient_user))
