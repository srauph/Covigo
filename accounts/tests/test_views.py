from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse

from unittest import mock

from accounts.utils import get_flag
from accounts.views import flaguser, unflaguser
from accounts.models import Flag


class ForgotPasswordTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, email='bob@gmail.com', username='bob1')
        user_1.save()

        self.request = RequestFactory().get('/')

        self.client = Client()
        self.response = self.client.get('accounts:forgot_password')

    def test_non_unique_email(self):
        """
        Test to check if user enters an email that have more than one user connected to it
        @return:
        """

        # Arrange
        # Simulate that somehow two users exist with the same email
        # (this can only occur if a serious bug in the program exists)
        user_2 = User.objects.create(id=2, email='bob@gmail.com', username='bob2')
        user_2.save()

        # Simulate the user entering their email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'bob@gmail.com'}

        # Act
        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message = list(response.context['form'].errors.values())[0][0]

        # Assert
        self.assertEqual('More than one user with the given email address could be found. Please contact the system '
                         'administrators to fix this issue.', form_error_message)

    def test_non_existing_user_email(self):
        """
        Test to check if user enters an email that isn't linked to any existing user
        @return:
        """

        # Arrange
        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'bruh@gmail.com'}

        # Act
        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message = list(response.context['form'].errors.values())[0][0]

        # Assert
        self.assertEqual('No user with the given email address could be found.', form_error_message)

    def test_empty_email(self):
        """
        Test to check if user does not enter any data in the form
        @return:
        """

        # Arrange
        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': ''}

        # Act
        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message_1 = list(response.context['form'].errors.values())[0][0]
        form_error_message_2 = list(response.context['form'].errors.values())[1][0]

        # Assert
        self.assertEqual('This field is required.', form_error_message_1)
        self.assertEqual('Please enter a valid email address or phone number.', form_error_message_2)

    @mock.patch('accounts.views.reset_password_email_generator')
    def test_forgot_password_calls_reset_password_email_generator(self, mock_reset_password_email_generator):
        """
        Test to check that forgot_password() calls reset_password_email_generator()
        @param mock_reset_password_email_generator:
        @return:
        """
        # Arrange
        # Create a new user that doesn't have duplicate emails in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')
        subject = "Password Reset Requested"
        template = "accounts/authentication/reset_password_email.txt"

        # Simulate the user entering a valid in the forgot password form
        mocked_pass_reset_form_data = {'email': 'qwerty@gmail.com'}

        # Act
        self.request.POST = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        # Assert
        mock_reset_password_email_generator.assert_called_once_with(new_user, subject, template)

    def test_forgot_password_redirects_to_done(self):
        # Arrange
        # Create a new user that doesn't have duplicate emails in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')
        subject = "Password Reset Requested"
        template = "accounts/authentication/reset_password_email.txt"

        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'qwerty@gmail.com'}

        # Act
        response = self.request.POST = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        # Assert
        self.assertRedirects(response, '/accounts/forgot_password/done/')


class FlagAssigningTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = User.objects.create(id=1, is_staff=1, username="Andrew")
        self.never_flagged_patient = User.objects.create(id=2, username="Jake")
        self.previously_flagged_patient = User.objects.create(id=3, username="John")

    def test_previously_flagged_user(self):
        """
        Test to check that a previously unflagged user can be flagged again
        @return:
        """

        # Arrange
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient)

        # Act
        response = flaguser(self.request, self.previously_flagged_patient.id)

        # Assert
        self.assertions(response, True, self.previously_flagged_patient)

    def test_never_flagged_user(self):
        """
        Test to ensure that a never-before flagged user can be flagged
        @return:
        """

        # Arrange & Act
        response = flaguser(self.request, self.never_flagged_patient.id)

        # Assert
        self.assertions(response, True, self.never_flagged_patient)

    def test_unflag_user(self):
        """
        Test to ensure that a flagged user can be unflagged
        @return:
        """

        # Arrange
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient, is_active=True)

        # Act
        response = unflaguser(self.request, self.previously_flagged_patient.id)

        # Assert
        self.assertions(response, False, self.previously_flagged_patient)

    def test_unflag_never_flagged_user(self):
        """
        Test to ensure that a never-before flagged user can be unflagged
        @return:
        """

        # Arrange & Act
        response = unflaguser(self.request, self.never_flagged_patient.id)

        # Assert
        self.assertIsNone(get_flag(self.request.user, self.never_flagged_patient))
        self.assertEqual(response.status_code, 302)

    def assertions(self, response, expected, patient):
        """
        Gets the flag of `patient`, and asserts that the flag's is_active property is `expected`
        and that the `response` status code is 302.
        @param response:
        @param expected:
        @param patient:
        @return:
        """
        flag = get_flag(self.request.user, patient)
        self.assertEqual(flag.is_active, expected)
        self.assertEqual(response.status_code, 302)
