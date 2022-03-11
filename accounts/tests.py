from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse

from accounts.utils import get_flag
from accounts.views import flaguser, unflaguser
from accounts.models import Flag


class ForgotPasswordTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, email='bob@gmail.com', username='bob1')
        user_1.save()

        self.client = Client()
        self.response = self.client.get('accounts:forgot_password')

    # Test to check if user enters an email that have more than one user connected to it
    def test_non_unique_email(self):
        # Simulate that somehow two users exist with the same email
        user_2 = User.objects.create(id=2, email='bob@gmail.com', username='bob2')
        user_2.save()

        # Simulate the user entering their email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'bob@gmail.com'}

        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message = list(response.context['form'].errors.values())[0][0]

        self.assertEqual('More than one user with the given email address could be found. Please contact the system '
                         'administrators to fix this issue.', form_error_message)

    # Test to check if user enters an email that isn't linked to any existing user
    def test_non_existing_user_email(self):
        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'bruh@gmail.com'}

        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message = list(response.context['form'].errors.values())[0][0]

        self.assertEqual('No user with the given email address could be found.', form_error_message)

    # Test to check if user does not enter any data in the form
    def test_empty_email(self):
        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': ''}

        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message_1 = list(response.context['form'].errors.values())[0][0]
        form_error_message_2 = list(response.context['form'].errors.values())[1][0]

        self.assertEqual('This field is required.', form_error_message_1)
        self.assertEqual('Please enter a valid email address or phone number.', form_error_message_2)

    def test_forgot_password_success(self):
        # Create a new user that doesn't have duplicate emails in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')

        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'qwerty@gmail.com'}

        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)


class FlagAssigningTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = User.objects.create(id=1, is_staff=1, username="Andrew")
        self.never_flagged_patient = User.objects.create(id=2, username="Jake")
        self.previously_flagged_patient = User.objects.create(id=3, username="John")

    def test_previously_flagged_user(self):
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient)
        response = flaguser(self.request, self.previously_flagged_patient.id)
        self.assertions(response, True, self.previously_flagged_patient)

    def test_never_flagged_user(self):
        response = flaguser(self.request, self.never_flagged_patient.id)
        self.assertions(response, True, self.never_flagged_patient)

    def test_unflag_user(self):
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient, is_active=True)
        response = unflaguser(self.request, self.previously_flagged_patient.id)
        self.assertions(response, False, self.previously_flagged_patient)

    def test_unflag_never_flagged_user(self):
        response = unflaguser(self.request, self.never_flagged_patient.id)
        self.assertIsNone(get_flag(self.request.user, self.never_flagged_patient))
        self.assertEqual(response.status_code, 302)

    def assertions(self, response, expected, patient):
        flag = get_flag(self.request.user, patient)
        self.assertEqual(flag.is_active, expected)
        self.assertEqual(response.status_code, 302)
