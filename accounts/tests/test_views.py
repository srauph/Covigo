from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase, TransactionTestCase, RequestFactory, Client
from django.urls import reverse
from unittest import mock
from django.db import connection

from Covigo.messages import Messages
from accounts.utils import get_flag, dictfetchall
from accounts.views import flag_user, unflag_user, profile_from_code, convert_permission_name_to_id
from accounts.models import Flag, Patient, Staff


class EditCaseTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create(is_superuser=True, username='PhillyB1', is_staff=True, first_name="Phil",
                                              last_name="Baldhead")
        self.doctor = Staff.objects.create(user=self.staff_user)
        self.staff_user.set_password('BaldMan123')
        self.staff_user.save()

        self.patient_user = User.objects.create(is_superuser=True, username='JohnnyD2', is_staff=False,
                                                first_name="John", last_name="Doe")
        self.patient = Patient.objects.create(user=self.patient_user, is_confirmed=True, is_negative=False,
                                              is_quarantining=True, assigned_staff=self.doctor)
        self.patient_user.set_password('JohnGuy123')
        self.patient_user.save()

        self.edited_mocked_case_data1 = {'is_confirmed': False, 'is_negative': False, 'is_quarantining': True}
        self.edited_mocked_case_data2 = {'is_confirmed': True, 'is_negative': False, 'is_quarantining': True}

        self.client = Client()
        self.client.login(username='PhillyB1', password='BaldMan123')
        self.response = self.client.get(
            reverse('accounts:edit_case',
                    kwargs={'user_id': self.patient.user_id}
                    )
        )

    def test_staff_can_edit_case_info_successfully(self):
        """
        test to check if a staff user can change/edit a patient's case info/data successfully
        @return: void
        """

        self.assertEqual(self.response.status_code, 200)

        # Act/simulate a staff user changing/editing a patient's case info/data in the edit case form with mocked form data
        self.response = self.client.post(
            reverse('accounts:edit_case',
                    kwargs={'user_id': self.patient.user_id}
                    ),
            self.edited_mocked_case_data1
        )

        # this refreshes the patient datatable in the database for the changes to take effect
        self.patient.refresh_from_db()

        # Assert/verify that the patient's case info/data was changed/edited successfully
        self.assertEqual(self.edited_mocked_case_data1['is_confirmed'], self.patient.is_confirmed)
        self.assertEqual(self.edited_mocked_case_data1['is_negative'], self.patient.is_negative)
        self.assertEqual(self.edited_mocked_case_data1['is_quarantining'], self.patient.is_quarantining)

    def test_edit_case_info_error(self):
        """
        test to check if a staff user can't submit an unchanged/unedited case info/data of a patient successfully
        @return: void
        """

        self.assertEqual(self.response.status_code, 200)

        # Act/simulate a staff user changing/editing a patient's case info/data in
        # the edit case form with identical/unchanged/unedited mocked form data
        self.response = self.client.post(
            reverse('accounts:edit_case',
                    kwargs={'user_id': self.patient.user_id}
                    ),
            self.edited_mocked_case_data2
        )

        # Assert/verify that the patient's case info/data was not changed/edited successfully with
        # identical/unchanged/unedited mocked form data and that an error message was thrown in the response context
        self.assertEqual(
            'This patient\'s case data was not edited successfully: No edits made on this patient\'s case data. If you wish to make no changes, please click the "Cancel" button to go back to this patient\'s profile page.',
            str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.edited_mocked_case_data2['is_confirmed'],
                         bool(self.response.context['case_form']['is_confirmed'].value()))
        self.assertEqual(self.edited_mocked_case_data2['is_negative'],
                         not bool(self.response.context['case_form']['is_negative'].value()))
        self.assertEqual(self.edited_mocked_case_data2['is_quarantining'],
                         bool(self.response.context['case_form']['is_quarantining'].value()))


class ChangePasswordTests(TestCase):
    def setUp(self):
        user = User.objects.create(email='bob@gmail.com', username='bob1', first_name='John', last_name='Smith')
        user.set_password('boogieman69420')
        user.save()

        self.request = RequestFactory().get('/')

        self.client = Client()
        self.client.login(username='bob1', password='boogieman69420')
        self.response = self.client.get('accounts:change_password')

    def test_empty_change_password_forms(self):
        """
        this test allows us to test directly for form fields when dealing with empty forms
        @return: void
        """

        # Simulate the user entering nothing in the change password form
        mocked_changed_password_form_data = {'old_password': '', 'new_password1': '', 'new_password2': ''}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('This field is required.', list(response.context['form'].errors.values())[0][0])
        self.assertEqual('This field is required.', list(response.context['form'].errors.values())[1][0])
        self.assertEqual('This field is required.', list(response.context['form'].errors.values())[2][0])

    def test_user_can_change_password_successfully_and_is_redirected_to_done(self):
        """
        test to check if a user can change their account password successfully
        @return: void
        """

        # Simulate the user entering a new valid/successful password in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': 'boogieman42069',
                                             'new_password2': 'boogieman42069'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertRedirects(response, '/accounts/change_password/done/')

    def test_change_password_errors(self):
        """
        test to check for the various form errors that can occur when a user is changing their password
        @return: void
        """

        # Simulate the user entering an invalid/unsuccessful password in the change password form
        mocked_changed_password_form_data = {'old_password': '1', 'new_password1': '1', 'new_password2': '1'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('Your old password was entered incorrectly. Please enter it again.',
                         list(response.context['form'].errors.values())[0][0])
        self.assertEqual('This password is too short. It must contain at least 8 characters.',
                         list(response.context['form'].errors.values())[1][0])
        self.assertEqual('This password is too common.', list(response.context['form'].errors.values())[1][1])
        self.assertEqual('This password is entirely numeric.', list(response.context['form'].errors.values())[1][2])

        # Simulate the user entering two unmatched new password fields in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': '1',
                                             'new_password2': '2'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('The two password fields didn\'t match.', list(response.context['form'].errors.values())[0][0])

        # Simulate the user entering a password that is identical to their account/profile username in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': 'bob1',
                                             'new_password2': 'bob1'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('The password is too similar to the username.',
                         list(response.context['form'].errors.values())[0][0])

        # Simulate the user entering a password that is identical to their account/profile email in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': 'bob@gmail.com',
                                             'new_password2': 'bob@gmail.com'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('The password is too similar to the email address.',
                         list(response.context['form'].errors.values())[0][0])

        # Simulate the user entering a password that is identical to their first name in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': 'John',
                                             'new_password2': 'John'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('The password is too similar to the first name.',
                         list(response.context['form'].errors.values())[0][0])

        # Simulate the user entering a password that is identical to their last name in the change password form
        mocked_changed_password_form_data = {'old_password': 'boogieman69420', 'new_password1': 'Smith',
                                             'new_password2': 'Smith'}

        # Act
        response = self.client.post(reverse('accounts:change_password'), mocked_changed_password_form_data)

        # Assert
        self.assertEqual('The password is too similar to the last name.',
                         list(response.context['form'].errors.values())[0][0])


class ForgotPasswordTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, email='bob@gmail.com', username='bob1')
        user_1.save()

        self.request = RequestFactory().get('/')

        self.client = Client()
        self.response = self.client.get('accounts:forgot_password')

    def test_non_unique_email(self):
        """
        Test to check if user enters an email that has more than one user connected/registered to it
        @return: void
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

        form_error_message = str(list(response.context['messages'])[0])

        # Assert
        self.assertEqual('More than one user with the given email address could be found. Please contact the system '
                         'administrators to fix this issue.', form_error_message)

    @mock.patch("accounts.views.send_system_message_to_user")
    def test_non_existing_user_email(self, m_system_message_sender):
        """
        Test to check if user enters an email that isn't linked to any existing user
        @return: void
        """

        # Arrange
        # Create a new user that doesn't have duplicate email in the db
        new_user = User.objects.create(id=3, username='qwerty')
        subject = "Covigo - Password Reset Requested"
        template = "reset_password"

        # Simulate the user entering a valid email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'bruh@lol.com'}

        # Act
        self.request.POST = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        # Assert
        m_system_message_sender.assert_not_called()

    def test_empty_email(self):
        """
        Test to check if user does not enter any data in the form
        @return: void
        """

        # Arrange
        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': ''}

        # Act
        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message_1 = list(response.context['form'].errors.values())[0][0]

        # Assert
        self.assertEqual('This field is required.', form_error_message_1)

    def test_invalid_email(self):
        """
        test to check if a user enters an invalid email address in the forgot password form
        @return: void
        """

        # Arrange
        # Simulate the user entering an invalid email address in the forgot password form
        mocked_pass_reset_form_data = {'email': 'r'}

        # Act
        response = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        form_error_message_1 = list(response.context['form'].errors.values())[0][0]

        # Assert
        self.assertEqual('Enter a valid email address.', form_error_message_1)

    @mock.patch('accounts.views.default_token_generator.make_token', return_value="token")
    @mock.patch('accounts.views.send_system_message_to_user')
    def test_forgot_password_calls_system_message_sender(self, m_system_message_sender, m_token_generator):
        """
        Test to check that forgot_password() calls reset_password_email_generator()
        @param m_system_message_sender:
        @return: void
        """

        # Arrange
        # Create a new user that doesn't have duplicate email in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')
        template = Messages.RESET_PASSWORD.value
        c = {
            'token': "token",
        }

        # Simulate the user entering a valid in the forgot password form
        mocked_pass_reset_form_data = {'email': 'qwerty@gmail.com'}

        # Act
        self.request.POST = self.client.post(reverse('accounts:forgot_password'), mocked_pass_reset_form_data)

        # Assert
        m_system_message_sender.assert_called_once_with(new_user, template=template, c=c)

    @mock.patch("accounts.views.send_system_message_to_user")
    def test_forgot_password_redirects_to_done(self, m_system_message_sender):
        """
        Test to check that completing the forgot password form redirects to the forgot password done page
        @return:
        """

        # Arrange
        # Create a new user that doesn't have duplicate email in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')

        # Simulate the user entering a non-existing email in the forgot password form
        mocked_pass_reset_form_data = {'email': 'qwerty@gmail.com'}

        # Act
        response = self.request.POST = self.client.post(reverse('accounts:forgot_password'),
                                                        mocked_pass_reset_form_data)

        # Assert
        self.assertRedirects(response, '/accounts/forgot_password/done/')


class FlagAssigningTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = User.objects.create(id=1, is_staff=1, is_superuser=True, username="Andrew")
        self.never_flagged_patient = User.objects.create(id=2, username="Jake")
        self.previously_flagged_patient = User.objects.create(id=3, username="John")

    def test_previously_flagged_user(self):
        """
        Test to check that a previously unflagged user can be flagged again
        @return: void
        """

        # Arrange
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient)

        # Act
        response = flag_user(self.request, self.previously_flagged_patient.id)

        # Assert
        self.assertions(response, True, self.previously_flagged_patient)

    def test_never_flagged_user(self):
        """
        Test to ensure that a never-before flagged user can be flagged
        @return: void
        """

        # Arrange & Act
        response = flag_user(self.request, self.never_flagged_patient.id)

        # Assert
        self.assertions(response, True, self.never_flagged_patient)

    def test_unflag_user(self):
        """
        Test to ensure that a flagged user can be unflagged
        @return: void
        """

        # Arrange
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient, is_active=True)

        # Act
        response = unflag_user(self.request, self.previously_flagged_patient.id)

        # Assert
        self.assertions(response, False, self.previously_flagged_patient)

    def test_unflag_never_flagged_user(self):
        """
        Test to ensure that a never-before flagged user can be unflagged
        @return: void
        """

        # Arrange & Act
        response = unflag_user(self.request, self.never_flagged_patient.id)

        # Assert
        self.assertIsNone(get_flag(self.request.user, self.never_flagged_patient))
        self.assertEqual(response.status_code, 302)

    def assertions(self, response, expected, patient):
        """
        Gets the flag of `patient`, and asserts that the flag's is_active property is `expected`
        and that the `response` status code is 302.
        @param response: Http response object
        @param expected: Expected flag status
        @param patient: Patient whose flag we're getting
        @return: void
        """

        flag = get_flag(self.request.user, patient)
        self.assertEqual(flag.is_active, expected)
        self.assertEqual(response.status_code, 302)


class ListOrViewAccountTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, is_superuser=True, username="bob", is_staff=False)
        user_1.set_password('secret')
        user_1.save()

        doctor_1 = User.objects.create(id=2, username="doctor", is_staff=True)

        staff_1 = Staff.objects.create(user=doctor_1)

        patient_1 = Patient.objects.create(code=1, user=user_1, assigned_staff=staff_1)
        user_1.patient = patient_1
        user_1.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

    def test_list_users_not_logged_in(self):
        """
        Test that checks if not logged-in users cannot view the list of users
        @return: void
        """

        # Arrange
        # New client that is not logged in
        other_client = Client()

        # Act
        response = other_client.get(reverse('accounts:list_users'))

        # Assert
        self.assertTemplateNotUsed(response, 'accounts/list_users.html')

    def test_list_users_logged_in(self):
        """
        Test that checks if logged-in users can view the list of users
        @return: void
        """

        # Act
        response = self.client.get(reverse('accounts:list_users'))

        # Assert
        self.assertTemplateUsed(response, 'accounts/list_users.html')

    def test_profile_not_logged_in(self):
        """
        Test that checks if not logged-in users cannot view user profiles
        @return: void
        """

        # Arrange
        # New client that is not logged in
        other_client = Client()

        # Act
        response = other_client.get('/accounts/profile/1/')

        # Assert
        self.assertTemplateNotUsed(response, 'accounts/profile/profile.html')

    @mock.patch('accounts.views.get_or_generate_patient_profile_qr')
    def test_profile_logged_in(self, m_get_or_generate_patient_profile_qr_function):
        """
        Test that checks if logged-in users can view user profiles
        @return: void
        """

        # Act
        response = self.client.get('/accounts/profile/1/')

        # Assert
        self.assertTemplateUsed(response, 'accounts/profile/profile.html')
        m_get_or_generate_patient_profile_qr_function.assert_called_once()

    @mock.patch('accounts.views.get_or_generate_patient_profile_qr')
    def test_profile_from_code(self, m_get_or_generate_patient_profile_qr_function):
        """
        Test that checks if not logged-in users can view user profiles qr codes using the profile codes
        @return: void
        """

        # Arrange
        # New client that is not logged in
        other_client = Client()

        # Act
        response = other_client.get('/accounts/profile/1/')
        request = response.wsgi_request
        profile_from_code(request, 1)

        # Assert
        m_get_or_generate_patient_profile_qr_function.assert_called_once()


class AccountsTestCase(TransactionTestCase):
    # this makes sure that the database ids reset to 1 for every test (especially important for
    # the test "test_user_can_edit_existing_user_account" when dealing with fetching user ids from the database)
    reset_sequences = True

    def setUp(self):
        """
        initialization of data to be run before every test. Note that not all data initialized here is used
        necessarily in all tests and the decision to include "all" of them here was more for readability choice
        than anything else (for example, "edited_mocked_form_data2" to "edited_mocked_form_data10" are only ever
        used in one test: "test_user_can_edit_existing_user_account")
        :return: void
        """

        self.user = User.objects.create(is_superuser=True, username='admin')
        self.staff = Staff.objects.create(user=self.user)
        self.user.set_password('admin')
        self.user.save()

        self.client = create_test_client(test_user=self.user, test_password='admin')

        self.mocked_group1 = Group.objects.create(name='')
        self.mocked_group2 = Group.objects.create(name='Doctor')
        self.mocked_group3 = Group.objects.create(name='Officer')

        c = connection.cursor()
        c.execute('SELECT * FROM Covigo.postal_codes WHERE POSTAL_CODE = %s', ['J7G 2M2'])
        r = dictfetchall(c)

        self.mocked_form_data1 = {'email': '', 'phone_number': '', 'is_staff': True, 'groups': self.mocked_group1.id}
        self.mocked_form_data2 = {'email': 'my_brother@gmail.com', 'phone_number': '', 'is_staff': True,
                                  'groups': self.mocked_group2.id}
        self.mocked_form_data3 = {'email': '', 'phone_number': '5145639236', 'is_staff': True,
                                  'groups': self.mocked_group3.id}
        self.mocked_form_data4 = {'email': 'my_sister@gmail.com', 'phone_number': '5149067845', 'is_staff': True,
                                  'groups': self.mocked_group3.id}
        self.mocked_form_data5 = {'email': 'm', 'phone_number': '5149067845', 'is_staff': True,
                                  'groups': self.mocked_group3.id}
        self.mocked_form_data6 = {'email': 'my_sister@gmail.com', 'phone_number': '51:l;><906', 'is_staff': True,
                                  'groups': self.mocked_group3.id}
        self.mocked_form_data7 = {'email': 'my_other@gmail.com', 'phone_number': '5143728471', 'is_staff': True,
                                  'groups': [self.mocked_group2.id, self.mocked_group3.id]}
        self.edited_mocked_form_data2 = {'username': 'my_brother@gmail.com', 'email': 'my_mother@gmail.com',
                                         'phone_number': '', 'is_staff': True, 'groups': self.mocked_group2.id,
                                         'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data3 = {'username': '5145639236', 'email': 'my_otter@gmail.com',
                                         'phone_number': '5145639236', 'is_staff': True,
                                         'groups': self.mocked_group2.id, 'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data4 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                         'phone_number': '5140398275', 'is_staff': True,
                                         'groups': self.mocked_group3.id, 'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data5 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                         'phone_number': '5149067845', 'is_staff': True,
                                         'groups': self.mocked_group2.id, 'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data6 = {'username': '', 'email': 'my_sister@gmail.com', 'phone_number': '5140398275',
                                         'is_staff': True, 'groups': self.mocked_group3.id,
                                         'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data7 = {'username': 'my_sister;', 'email': 'my_sister@gmail.com',
                                         'phone_number': '5140398275', 'is_staff': True,
                                         'groups': self.mocked_group3.id, 'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data8 = {'username': 'my_sister@gmail.com', 'email': 'y', 'phone_number': '5149067845',
                                         'is_staff': True, 'groups': self.mocked_group3.id,
                                         'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data9 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                         'phone_number': 'h', 'is_staff': True, 'groups': self.mocked_group3.id,
                                         'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data10 = {'username': 'my_sister@gmail.com', 'email': '', 'phone_number': '',
                                          'is_staff': True, 'groups': self.mocked_group3.id,
                                          'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data11 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                          'phone_number': '5149067845', 'is_staff': True,
                                          'groups': self.mocked_group3.id, 'postal_code': ''}
        self.edited_mocked_form_data12 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                          'phone_number': '5149067845', 'is_staff': True,
                                          'groups': self.mocked_group3.id, 'postal_code': '000000'}
        self.edited_mocked_form_data13 = {'username': 'my_sister@gmail.com', 'email': 'my_sister@gmail.com',
                                          'phone_number': '5149067845', 'is_staff': True,
                                          'groups': self.mocked_group3.id, 'postal_code': 'J7G 2M3'}
        self.edited_mocked_form_data14 = {'username': 'my_sister@gmail.com', 'email': 'my_father@gmail.com',
                                          'phone_number': '5149067845', 'is_staff': True,
                                          'groups': [self.mocked_group2.id, self.mocked_group3.id],
                                          'postal_code': r[0]['POSTAL_CODE']}
        self.edited_mocked_form_data15 = {'username': 'my_brother@gmail.com', 'email': 'my_mother@gmail.com',
                                          'phone_number': '5145639236', 'is_staff': True,
                                          'groups': self.mocked_group3.id, 'postal_code': r[0]['POSTAL_CODE']}

        self.response = self.client.get(reverse('accounts:create_user'))

    def test_empty_create_new_user_account_forms(self):
        """
        this test allows us to test directly for form fields when dealing with empty forms
        :return: void
        """

        # this insures that the specific GET request has succeeded (OK) through
        # the reverse URL naming attribute for the "create_user.html" page
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(User.objects.all().count() == 1)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data1)

        # we expect no accounts to be added to the database here since nothing has been inputted
        # in the form fields so there's no "real" post data submission
        self.assertTrue(User.objects.all().count() == 1)
        self.assertEqual('Please enter an email address or a phone number.',
                         str(list(self.response.context['messages'])[0]))

    def test_user_can_create_new_user_account(self):
        """
        this test allows us to test for if an account that is submitted through a form
        (with the "Create" or "Create and Return" buttons) ends up actually being indeed added to the database or not
        :return: void
        """

        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(User.objects.all().count() == 1)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data2)

        # we expect one more account to be added to the database here, since proper
        # form data has been inputted in the form fields
        self.assertTrue(User.objects.all().count() == 2)
        self.assertEqual(self.mocked_form_data2['email'], User.objects.get(id=2).email)
        self.assertEqual(self.mocked_form_data2['phone_number'], User.objects.get(id=2).profile.phone_number)
        self.assertEqual(self.mocked_form_data2['groups'], User.objects.get(id=2).groups.get().id)
        self.assertEqual(self.mocked_form_data2['is_staff'], User.objects.get(id=2).is_staff)

        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data3)

        self.assertTrue(User.objects.all().count() == 3)
        self.assertEqual(self.mocked_form_data3['email'], User.objects.get(id=3).email)
        self.assertEqual(self.mocked_form_data3['phone_number'], User.objects.get(id=3).profile.phone_number)
        self.assertEqual(self.mocked_form_data3['groups'], User.objects.get(id=3).groups.get().id)
        self.assertEqual(self.mocked_form_data3['is_staff'], User.objects.get(id=3).is_staff)

        # Here, I am checking if it is possible to create an account with the same
        # groups/role as another account (should be possible as it is intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data4)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual(self.mocked_form_data4['email'], User.objects.get(id=4).email)
        self.assertEqual(self.mocked_form_data4['phone_number'], User.objects.get(id=4).profile.phone_number)
        self.assertEqual(self.mocked_form_data4['groups'], User.objects.get(id=4).groups.get().id)
        self.assertEqual(self.mocked_form_data4['is_staff'], User.objects.get(id=4).is_staff)
        self.assertEqual(User.objects.get(id=3).groups.get().id, User.objects.get(id=4).groups.get().id)

        # here, I am testing for the valid email address form error body by making sure that it works:
        # If I use a non-valid email address inside mocked form data and try to call a POST request on it,
        # I should expect the error body to be shown on the view, alerting me of my mistake,
        # and prevent me from creating an account in the database, thus my database user count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data5)
        self.assertTrue(User.objects.all().count() == 4)

        self.assertEqual('Enter a valid email address.', list(self.response.context['user_form'].errors['email'])[0])

        # here, I am testing for the duplicate email (in another already existing account) and invalid phone number
        # form error messages by making sure that they work: If I try to submit mocked form data that contains a duplicate email
        # and an invalid phone number and try to call a POST request on it, I should expect the error messages to be shown on the view,
        # alerting me of my mistakes, and prevent me from creating an account in the database, thus my database user count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data6)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual('Email already in use by another user.',
                         list(self.response.context['user_form'].errors['email'])[0])
        self.assertEqual('Please enter a valid phone number.',
                         list(self.response.context['profile_form'].errors['phone_number'])[0])

        # here, I am testing for the multiple groups/roles form error message by making sure that it works:
        # If I try to post mocked form data that contains more than one groups/role by calling a POST request on it,
        # I should expect the error message to be shown on the view, alerting me of my mistake,
        # and prevent me from creating an account in the database, thus my database user count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data7)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual('Cannot select more than one group.',
                         list(self.response.context['user_form']['groups'].errors)[0])

    def test_user_can_edit_existing_user_account(self):
        """
        this test allows us to test for if an account that is edited and submitted through a form
        ends up actually being indeed properly edited in the list of users and in the database or not
        :return: void
        """

        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(User.objects.all().count() == 1)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data2)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data3)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data4)
        self.assertTrue(User.objects.all().count() == 4)

        # for lack of details, this following statement would translate to the "edit_user.html" page
        # opening up with a specific user/account from the user/account list already
        # loaded on its form on the view and ready to be edited
        self.response = self.client.get(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=2).id}
                    )
        )
        self.assertEqual(self.response.status_code, 200)
        self.assertEqual(self.response.context['user_form']['email'].value(), User.objects.get(id=2).email)
        self.assertEqual(self.response.context['profile_form']['phone_number'].value(),
                         User.objects.get(id=2).profile.phone_number)
        self.assertEqual(list(self.response.context['user_form']['groups'].value())[0],
                         User.objects.get(id=2).groups.get().id)

        # for lack of details, this following statement would translate to an administrator making a change/edit
        # to the form data of an existing user/account taken from the user/account list and "posting" that
        # new user/account back to the view of the "list_users.html" page
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=2).id}
                    ),
            self.edited_mocked_form_data2
        )
        self.response = self.client.get(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=3).id}
                    )
        )
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=3).id}
                    ),
            self.edited_mocked_form_data3
        )
        self.response = self.client.get(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    )
        )
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data4
        )

        # Here, I am checking if it is possible to edit an already existing account with the same
        # groups/role as another already existing account (should be possible as it is intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data5
        )
        self.assertEqual(User.objects.get(id=2).groups.get().id, User.objects.get(id=4).groups.get().id)

        # here, I am testing for the empty edited username field (in another already existing account)
        # form error message by making sure that it works: If I try to submit edited mocked form data
        # with no username by calling a POST request on it, I should expect the error message to be shown
        # on the view as the form should return the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data6
        )
        self.assertEqual('This field is required.', list(self.response.context['user_form'].errors.values())[0][0])

        # here, I am testing for the invalid edited username field form error message by making sure that it works:
        # If I try to submit edited mocked form data with an invalid username by calling a POST request on it,
        # I should expect the error message to be shown on the view as the form should return the error message
        # and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data7
        )
        self.assertEqual(
            "Username can only contain letters, numbers, periods '.', underscores '_', hyphens '-', or the at symbol '@'.",
            list(self.response.context['user_form'].errors.values())[0][0])

        # here, I am testing for the valid email address form error message by making sure that it works:
        # If I try to submit edited mocked form data with a non-valid email address by calling a POST request on it,
        # I should expect the error message to be shown on the view as the form should return
        # the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data8
        )
        self.assertEqual('Enter a valid email address.', list(self.response.context['user_form'].errors['email'])[0])

        # here, I am testing for the valid phone number form error message by making sure that it works:
        # If I try to submit edited mocked form data with a non-valid phone number by calling a POST request on it,
        # I should expect the error message to be shown on the view as the form should return
        # the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data9
        )
        self.assertEqual('Please enter a valid phone number.',
                         list(self.response.context['profile_form'].errors['phone_number'])[0])

        # here, I am testing for the empty edited email and phone number fields form error message by making sure that it works:
        # If I try to submit edited mocked form data with no email and phone number by calling a POST request on it,
        # I should expect the error message to be shown on the view as the form should return
        # the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data10
        )
        self.assertEqual('Please enter an email address or a phone number.',
                         str(list(self.response.context['messages'])[0]))

        # here, I am testing for the postal code form error messages by making sure that they work:
        # If I try to submit edited mocked form data with a non-valid, non-existent or empty postal code by calling a POST request on it,
        # I should expect the error messages to be shown on the view as the form should return
        # the error messages and alert me of my mistakes (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data11
        )
        self.assertEqual('Please provide your postal code.',
                         list(self.response.context['profile_form'].errors['postal_code'])[0])

        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data12
        )
        self.assertEqual('Please enter a valid postal code.',
                         list(self.response.context['profile_form'].errors['postal_code'])[0])

        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data13
        )
        self.assertEqual('The postal code entered may not exist; check its spelling and try again.',
                         list(self.response.context['profile_form'].errors['postal_code'])[0])

        # here, I am testing for the multiple groups/roles form error message by making sure that it works:
        # If I try to post edited mocked form data that contains more than one groups/role by calling a POST request on it,
        # I should expect the error message to be shown on the view as the form should return
        # the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data14
        )
        self.assertEqual('Cannot select more than one group.',
                         list(self.response.context['user_form']['groups'].errors)[0])

        # here, I am testing for the duplicate username, email and phone number fields (in another already existing account)
        # form error messages by making sure that they work: If I try to post edited mocked form data that contains
        # an identical username, email and phone number to any other already existing user/account in the
        # database/system by calling a POST request on it, I should expect the error messages to be shown on
        # the view as the form should return the error messages and alert me of my mistakes (intended behaviour)
        self.response = self.client.post(
            reverse('accounts:edit_user',
                    kwargs={'user_id': User.objects.get(id=4).id}
                    ),
            self.edited_mocked_form_data15
        )
        self.assertEqual('A user with that username already exists.',
                         list(self.response.context['user_form'].errors['username'])[0])
        self.assertEqual('Email already in use by another user.',
                         list(self.response.context['user_form'].errors['email'])[0])

        # this just makes sure that the database still contains
        # the same number of users/accounts in it as it did earlier, thus
        # showing that the contents of existing users/accounts
        # were changed, rather than the changes showing up
        # as new users/accounts in the database entirely
        self.assertTrue(User.objects.all().count() == 4)
        self.response = self.client.get(reverse('accounts:list_users'))
        self.assertEqual(self.response.status_code, 200)

        # the following assertions below check that the list of users/accounts page actually shows
        # the three posted users/accounts with changes in its context
        self.assertEqual(set(self.response.context['users']), set(User.objects.all()))
        self.assertEqual(
            list(self.response.context['users'].values("username")),
            list(User.objects.values("username"))
        )
        self.assertEqual(
            list(self.response.context['users'].values("email")),
            list(User.objects.values("email"))
        )
        self.assertEqual(self.response.context['users'][1].profile.phone_number,
                         User.objects.get(id=2).profile.phone_number)
        self.assertEqual(self.response.context['users'][2].profile.phone_number,
                         User.objects.get(id=3).profile.phone_number)
        self.assertEqual(self.response.context['users'][3].profile.phone_number,
                         User.objects.get(id=4).profile.phone_number)
        self.assertEqual(
            list(self.response.context['users'].values("groups")),
            list(User.objects.values("groups"))
        )


class ListGroupTests(TestCase):
    def test_list_groups_not_logged_in(self):
        """
        Test that checks if not logged in, users cannot view the list of groups
        @return: void
        """

        # Arrange
        # New client that is not logged in
        anonymous_client = Client()

        # Act
        response = anonymous_client.get(reverse('accounts:list_users'))

        # Assert
        self.assertTemplateNotUsed(response, 'accounts/list_users.html')

    def test_list_groups_successfully(self):
        """
        Test that checks that a logged-in user can view the list of groups
        @return: void
        """

        # Arrange
        create_test_permissions(4)
        client = create_test_client()

        new_group_name = 'test groups lol'
        second_new_group_name = 'second test groups lol'

        group1 = Group.objects.create(name=new_group_name)
        group1.permissions.set([1, 2])
        group1.save()

        group2 = Group.objects.create(name=second_new_group_name)
        group2.permissions.set([2, 3])
        group2.save()

        # Act
        response = client.get(reverse('accounts:list_groups'))

        # Assert
        self.assertEqual(set(Group.objects.all()), set(response.context['groups']))


class CreateGroupTests(TestCase):
    def setUp(self):
        create_test_permissions(3)
        self.client = create_test_client()

    def test_create_group_successfully(self):
        """
        Test that creating a group with a given set of permissions works
        @return: void
        """

        # Arrange
        new_group_name = 'test group lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']
        expected_permissions_set = set(Permission.objects.filter(codename__in=new_group_perms))

        # Act
        create_group_helper(self.client, new_group_name, new_group_perms)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_create_group_with_no_perms_successfully(self):
        """
        Test that creating a group with an empty set of permissions works
        @return: void
        """

        # Arrange
        new_group_name = 'test groups lol'
        new_group_perms = []
        expected_permissions_set = set()

        # Act
        create_group_helper(self.client, new_group_name, new_group_perms)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_create_group_with_existing_perms_successfully(self):
        """
        Test that creating a group with permissions identical to another group works
        @return: void
        """

        # Arrange
        new_group_name = 'test groups lol'
        second_new_group_name = 'second test groups lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']

        # Act
        create_group_helper(self.client, new_group_name, new_group_perms)
        create_group_helper(self.client, second_new_group_name, new_group_perms)

        # Assert
        self.assertEqual(2, Group.objects.count())
        self.assertEqual(second_new_group_name, Group.objects.last().name)
        self.assertEqual(set(Group.objects.first().permissions.all()), set(Group.objects.last().permissions.all()))

    def test_create_group_with_no_name_raises_error(self):
        """
        Test that creating a group with a blank name fails and sends errors.blank_name as True
        @return: void
        """

        # Arrange
        new_group_name = ''
        new_group_perms = ['test_perm_1', 'test_perm_2']

        # Act
        response = create_group_helper(self.client, new_group_name, new_group_perms)

        # Assert
        self.assertTrue(list(response.context['messages'])[0])
        self.assertFalse(set(Group.objects.all()))

    def test_create_group_with_existing_name_raises_error(self):
        """
        Test that creating a group with an existing name fails and sends errors.duplicate_name as True
        @return: void
        """

        # Arrange
        new_group_name = 'test groups lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']

        # Act
        create_group_helper(self.client, new_group_name, new_group_perms)
        response = create_group_helper(self.client, new_group_name, new_group_perms)

        # Assert
        self.assertTrue(list(response.context['messages'])[1])
        self.assertEqual(1, Group.objects.count())


class EditGroupTests(TestCase):
    def setUp(self):
        create_test_permissions(3)
        self.client = create_test_client()

        new_group_name = 'test groups lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']

        create_group_helper(self.client, new_group_name, new_group_perms)

    def test_edit_group_successfully(self):
        """
        Test that editing a group with a given set of permissions works
        @return: void
        """

        # Arrange
        group_to_edit = Group.objects.first()
        new_group_name = 'new groups name lol'
        new_group_perms = ['test_perm_2', 'test_perm_3']

        expected_permissions_set = set(Permission.objects.filter(codename__in=new_group_perms))

        # Act
        edit_group_helper(self.client, new_group_name, new_group_perms, group_to_edit.id)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_edit_group_to_no_perms_successfully(self):
        """
        Test that editing a group to have an empty set of permissions works
        @return: void
        """

        # Arrange
        group_to_edit = Group.objects.first()
        new_group_name = 'new groups name lol'
        new_group_perms = []
        expected_permissions_set = set()

        # Act
        edit_group_helper(self.client, new_group_name, new_group_perms, group_to_edit.id)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_edit_group_to_existing_perms_successfully(self):
        """
        Test that editing a group to have permissions identical to another group works
        @return: void
        """

        # Arrange
        new_group_name = 'test groups lol'
        second_new_group_name = 'second test groups lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']
        second_new_group_perms = ['test_perm_2', 'test_perm_3']

        create_group_helper(self.client, new_group_name, new_group_perms)
        create_group_helper(self.client, second_new_group_name, second_new_group_perms)

        group_to_edit = Group.objects.last()

        # Act
        edit_group_helper(self.client, second_new_group_name, new_group_perms, group_to_edit.id)

        # Assert
        self.assertEqual(set(Group.objects.first().permissions.all()), set(Group.objects.last().permissions.all()))

    def test_edit_group_to_no_name_raises_error(self):
        """
        Test that editing a group to have a blank name fails and sends errors.blank_name as True
        @return: void
        """

        # Arrange
        group_to_edit = Group.objects.first()
        old_group_name = group_to_edit.name
        old_group_perms = set(group_to_edit.permissions.all())

        new_group_name = ''
        new_group_perms = ['test_perm_2', 'test_perm_3']

        # Act
        response = edit_group_helper(self.client, new_group_name, new_group_perms, group_to_edit.id)

        # Assert
        self.assertTrue(list(response.context['messages'])[1])
        self.assertEqual(old_group_name, Group.objects.first().name)
        self.assertEqual(old_group_perms, set(Group.objects.first().permissions.all()))

    def test_edit_group_to_existing_name_raises_error(self):
        """
        Test that editing a group to have an existing name fails and sends errors.duplicate_name as True
        @return: void
        """

        # Arrange
        old_second_group_name = 'new groups name lol'
        second_group_perms = ['test_perm_2', 'test_perm_3']

        create_group_helper(self.client, old_second_group_name, second_group_perms)
        old_second_group_perms = set(Group.objects.last().permissions.all())

        new_second_group_name = 'test groups lol'
        new_second_group_perms = ['test_perm_2', 'test_perm_3']

        group_to_edit = Group.objects.last()

        # Act
        response = edit_group_helper(self.client, new_second_group_name, new_second_group_perms, group_to_edit.id)

        # Assert
        self.assertTrue(list(response.context['messages'])[2])
        self.assertEqual(old_second_group_name, Group.objects.last().name)
        self.assertEqual(old_second_group_perms, set(Group.objects.last().permissions.all()))


class ConvertPermissionNameTests(TestCase):
    def setUp(self):
        create_test_permissions(6)
        self.factory = RequestFactory()

    def test_pass_list_of_perms(self):
        """
        Test that the convert_permission_name_to_id() function returns the IDS of the passed list of perms
        @return: void
        """

        cases = [
            {'test_section': 0, 'msg': 'No permissions'},
            {'test_section': Permission.objects.count() // 2, 'msg': 'Half of the permissions'},
            {'test_section': Permission.objects.count(), 'msg': 'All of the permissions'},
        ]

        for case in cases:
            with self.subTest(case.get('msg')):
                # Arrange
                perms_list = []
                id_list = []
                for i in Permission.objects.values('codename', 'id')[:case.get('test_section')]:
                    perms_list.append(i['codename'])
                    id_list.append(i['id'])

                fake_form_data = {'perms': perms_list}
                m_request = self.factory.post('', fake_form_data)

                # Act & Assert
                self.assertEqual(id_list, convert_permission_name_to_id(m_request))


def create_test_client(test_user=None, test_password=None):
    """
    Helper function to create a test client
    @return: The test client
    """

    if test_user is None:
        test_user = User.objects.create(is_superuser=True, username="bob")
        test_user.set_password('secret')
        test_user.save()
        test_password = 'secret'

    client = Client()
    client.login(username=test_user.username, password=test_password)

    return client


def create_test_permissions(num_of_permissions):
    """
    Helper function to create test permissions
    @return: void
    """

    Permission.objects.all().delete()
    for i in range(1, num_of_permissions + 1):
        Permission.objects.create(codename=f'test_perm_{i}', content_type_id=1)


def create_group_helper(client, new_group_name, new_group_perms):
    """
    Helper function to create a group to be used inside another test.
    @param client: The test client
    @param new_group_name: The new name to give to the created group
    @param new_group_perms: The new perms to give to the created group
    @return: The test client's response
    """

    # here, the key "name" is the name of the group and not the name of the permission
    fake_form_data = {
        'name': new_group_name,
        'perms': new_group_perms
    }

    return client.post(reverse('accounts:create_group'), fake_form_data)


def edit_group_helper(client, new_group_name, new_group_perms, group_id):
    """
    Helper function to edit a group used inside another test.
    @param client: The test client
    @param new_group_name: The new name to give to the edited group
    @param new_group_perms: The new perms to give to the edited group
    @param group_id: The id of the groups to edit
    @return: The test client's response
    """

    # here, the key "name" is the name of the group and not the name of the permission
    fake_form_data = {
        'name': new_group_name,
        'perms': new_group_perms
    }

    return client.post(reverse('accounts:edit_group', kwargs={'group_id': group_id}), fake_form_data)
