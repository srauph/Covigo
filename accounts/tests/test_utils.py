from django.contrib.auth.models import User
from django.test import TestCase
from unittest import mock

import accounts.utils
from accounts.models import Flag, Staff
from accounts.utils import get_flag, get_superuser_staff_model, reset_password_email_generator, send_email_to_user


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
        """
        Test that when no superuser exists, the function returns None
        @return:
        """

        # Act & Assert
        self.assertIsNone(get_superuser_staff_model())

    @mock.patch.object(accounts.utils.Staff.objects, 'create')
    def test_superuser__has_no_staff_object__creates_staff_object(self, mock_create_staff_model):
        """
        Test that for a superuser without a staff object, the function o create one for it is called.
        @return:
        """

        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        get_superuser_staff_model()

        # Assert
        mock_create_staff_model.assert_called_once_with(user=self.superuser)

    def test_superuser__has_no_staff_object__returns_staff_object(self):
        """
        Test that for a superuser without a staff object, one is created and assigned to it, and returned
        @return:
        """
        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)

        # Act
        result = get_superuser_staff_model()

        # Assert
        self.assertIsInstance(result, Staff)
        self.assertEqual(result, self.superuser.staff)

    def test_superuser__has_staff_object__returns_staff_object(self):
        """
        Test that the staff object of a superuser that already has one gets returned and that a new one isn't created
        @return:
        """

        # Arrange
        self.superuser = User.objects.create(username="admin", is_superuser=True)
        staff_obj = Staff.objects.create(user=self.superuser)
        self.superuser.refresh_from_db()

        # Act & Assert
        self.assertEqual(staff_obj, get_superuser_staff_model())
        self.assertEqual(staff_obj, self.superuser.staff)
        with mock.patch.object(accounts.utils.Staff.objects, 'create') as mock_staff_model:
            mock_staff_model.assert_not_called()


class ResetEmailPasswordGeneratorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user")
        self.subject = "Test Subject"
        self.template = "Test Template"

    # NOTE: TO ANYONE WHO USES THIS AS INSPIRATION FOR DOING MULTIPLE MOCKS:
    # The decorators wrap the function and are thus loaded in "reverse order"!
    # The decorator in the bottom will populate the first param, second from bottom
    # is the second param, etc. until the first decorator populates the last param.
    @mock.patch('accounts.utils.send_email_to_user')
    @mock.patch('accounts.utils.render_to_string', return_value="email")
    def test_renders_email(self, mock_render_function, _):
        """
        Check that the render to string function is being called
        @param mock_render_function: accounts.utils.render_to_string
        @param _:
        @return:
        """

        # Act
        reset_password_email_generator(self.user, self.subject, self.template)

        # Assert
        mock_render_function.assert_called_once()

    @mock.patch('accounts.utils.render_to_string', return_value="email")
    @mock.patch('accounts.utils.send_email_to_user')
    def test_sends_email(self, mock_send_email_function, _):
        """
        Check that the send email function is being called
        @param mock_send_email_function:
        @param _:
        @return:
        """

        # Act
        reset_password_email_generator(self.user, self.subject, self.template)

        # Assert
        mock_send_email_function.assert_called_once_with(self.user, self.subject, "email")


class SendEmailToUserTests(TestCase):
    @mock.patch('accounts.utils.smtplib.SMTP')
    @mock.patch('accounts.utils.smtplib')
    def test_send_email(self, mock_smtp, mock_smtp_object):
        """
        Check that the smtplib functions are being called
        @param mock_smtp:
        @param mock_smtp_object:
        @return:
        """
        # Arrange
        user = User.objects.create(email="test@email.com")
        mock_instance = mock_smtp_object.return_value
        sender_email = 'shahdextra@gmail.com'
        sender_pass = 'roses12345!%'
        email_contents = f"Subject: test subject\ntest message"

        # Act
        send_email_to_user(user, "test subject", "test message")

        # Assert
        mock_smtp.SMTP.assert_called_once_with('smtp.gmail.com', 587)
        mock_instance.starttls.assert_called_once()
        mock_instance.login.assert_called_once_with(sender_email, sender_pass)
        mock_instance.sendmail.assert_called_once_with(sender_email, user.email, email_contents)
        mock_instance.quit.assert_called_once()
