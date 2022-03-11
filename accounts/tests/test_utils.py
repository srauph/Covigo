from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from unittest import mock

import accounts.utils
from accounts.models import Flag, Staff
from accounts.utils import get_flag, get_superuser_staff_model


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


class GetSuperuserStaffModelTests(TestCase):

    def test_superuser_does_not_exist(self):
        # Act & Assert
        self.assertIsNone(get_superuser_staff_model())

    @mock.patch.object(accounts.utils.Staff.objects, 'create')
    def test_superuser__has_no_staff_object__creates_staff_object(self, mock_staff_model):
        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        get_superuser_staff_model()

        # Assert
        mock_staff_model.assert_called_once_with(user=self.superuser)

    def test_superuser__has_no_staff_object__returns_staff_object(self):
        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        result = get_superuser_staff_model()

        # Assert
        self.assertIsInstance(result, Staff)

    def test_superuser__has_staff_object__returns_staff_object(self):
        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)
        staff_obj = Staff.objects.create(user=self.superuser)
        self.superuser.refresh_from_db()

        with mock.patch.object(accounts.utils.Staff.objects, 'create') as mock_staff_model:
            # Act & Assert
            self.assertEqual(staff_obj, get_superuser_staff_model())
            mock_staff_model.assert_not_called()
