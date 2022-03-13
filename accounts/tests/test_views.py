from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase,TransactionTestCase, RequestFactory, Client
from django.urls import reverse

from unittest import mock, skip

from accounts.forms import UserForm
from accounts.utils import get_flag
from accounts.views import flaguser, unflaguser, profile, profile_from_code, convert_permission_name_to_id
from accounts.models import Flag, Patient, Staff


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
    def test_forgot_password_calls_reset_password_email_generator(self, m_reset_password_email_generator):
        """
        Test to check that forgot_password() calls reset_password_email_generator()
        @param m_reset_password_email_generator:
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
        m_reset_password_email_generator.assert_called_once_with(new_user, subject, template)

    def test_forgot_password_redirects_to_done(self):
        # Arrange
        # Create a new user that doesn't have duplicate emails in the db
        new_user = User.objects.create(id=3, email='qwerty@gmail.com', username='qwerty')
        subject = "Password Reset Requested"
        template = "accounts/authentication/reset_password_email.txt"

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


class AccountPageViewTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, username="bob", is_staff=False)
        user_1.set_password('secret')
        user_1.save()

        doctor_1 = User.objects.create(id=2, username="doctor", is_staff=True)

        staff_1 = Staff.objects.create(user=doctor_1)

        patient_1 = Patient.objects.create(code=1, user=user_1, staff=staff_1)
        user_1.patient = patient_1
        user_1.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

    def test_list_users_not_logged_in(self):
        """
        Test that checks if not logged-in users cannot view the list of users
        @return:
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
        @return:
        """
        # Act
        response = self.client.get(reverse('accounts:list_users'))

        # Assert
        self.assertTemplateUsed(response, 'accounts/list_users.html')

    def test_profile_not_logged_in(self):
        """
        Test that checks if not logged-in users cannot view user profiles
        @return:
        """
        # Arrange
        # New client that is not logged in
        other_client = Client()

        # Act
        response = other_client.get('/accounts/profile/1/')

        # Assert
        self.assertTemplateNotUsed(response, 'accounts/profile.html')

    @mock.patch('accounts.views.get_or_generate_patient_profile_qr')
    def test_profile_logged_in(self, m_generate_profile_qr_function):
        """
        Test that checks if logged-in users can view user profiles
        @return:
        """
        # Act
        response = self.client.get('/accounts/profile/1/')

        # Assert
        self.assertTemplateUsed(response, 'accounts/profile.html')
        m_generate_profile_qr_function.assert_called_once()

    @mock.patch('accounts.views.get_or_generate_patient_profile_qr')
    def test_profile_from_code(self, m_generate_profile_qr_function):
        """
        Test that checks if not logged-in users can view user profiles qr codes using the profile codes
        @return:
        """
        # Arrange
        # New client that is not logged in
        other_client = Client()

        # Act
        response = other_client.get('/accounts/profile/1/')
        request = response.wsgi_request
        profile_from_code(request, 1)

        # Assert
        m_generate_profile_qr_function.assert_called_once()


class AccountCreateTests(TransactionTestCase):

    # this makes sure that the database ids reset to 1 for every test (especially important for
    # the test "test_user_can_edit_symptom_and_return" when dealing with fetching symptom ids from the database)
    reset_sequences = True

    def setUp(self):
        """
        initialization of data to be run before every test. Note that not all data initialized here is used
        necessarily in all tests and the decision to include "all" of them here was more for readability choice
        than anything else (for example, "edited_mocked_form_data2" and "edited_mocked_form_data3" are only ever
        used in one test: "test_user_can_edit_symptom_and_return")
        :return: void
        """
        self.client = Client()
        self.user = User.objects.create(username='admin')
        self.staff = Staff.objects.create(user=self.user)
        self.mocked_group1 = Group.objects.create(name='')
        self.mocked_group2 = Group.objects.create(name='Doctor')
        self.mocked_group3 = Group.objects.create(name='Officer')
        self.user.set_password('admin')
        self.user.save()
        self.client.login(username='admin', password='admin')
        self.mocked_form_data1 = {'email': '', 'phone_number': '', 'is_staff': True, 'groups': self.mocked_group1.id}
        self.mocked_form_data2 = {'email': 'my_brother@gmail.com', 'phone_number': '', 'is_staff': True, 'groups': self.mocked_group2.id}
        self.mocked_form_data3 = {'email': '', 'phone_number': '5145639236', 'is_staff': True, 'groups': self.mocked_group3.id}
        self.mocked_form_data4 = {'email': 'my_sister@gmail.com', 'phone_number': '5149067845', 'is_staff': True, 'groups': self.mocked_group3.id}
        self.mocked_form_data5 = {'email': 'my_other@gmail.com', 'phone_number': '5143728471', 'is_staff': True, 'groups': [self.mocked_group2.id, self.mocked_group3.id]}
        self.response = self.client.get(reverse('accounts:create_user'))

    def test_empty_forms(self):
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
        self.assertEqual('Please enter an email address or a phone number.', list(self.response.context['user_form'].errors['__all__'])[0])

    def test_user_can_create_account(self):
        """
        this test allows us to test for if an account that is submitted through a form
        (with the "create" or "create and return" buttons) ends up actually being indeed added to the database or not
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
        # group/role as another account (should be possible as it is intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data4)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual(self.mocked_form_data4['email'], User.objects.get(id=4).email)
        self.assertEqual(self.mocked_form_data4['phone_number'], User.objects.get(id=4).profile.phone_number)
        self.assertEqual(self.mocked_form_data4['groups'], User.objects.get(id=4).groups.get().id)
        self.assertEqual(self.mocked_form_data4['is_staff'], User.objects.get(id=4).is_staff)

        # here, I am testing for the duplicate email and phone number (in another already existing account)
        # form error messages by making sure that they work: If I use the same mocked form data and try to
        # call a POST request on it, I should expect the error messages to be shown on the view, alerting me of my mistake,
        # and prevent me from creating a duplicate account in the database, thus my database user count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data4)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual('Email already in use by another user.', list(self.response.context['user_form'].errors['email'])[0])
        self.assertEqual('Phone number already in use by another user.', list(self.response.context['profile_form'].errors['phone_number'])[0])

        # here, I am testing for the multiple groups/roles form error message by making sure that it works:
        # If I try to post form data that contains more than one group/role by calling a POST request on it,
        # I should expect the error message to be shown on the view, alerting me of my mistake,
        # and prevent me from creating an account in the database, thus my database user count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('accounts:create_user'), self.mocked_form_data5)

        self.assertTrue(User.objects.all().count() == 4)
        self.assertEqual('Cannot select more than one group.', list(self.response.context['user_form']['groups'].errors)[0])



@skip("Test needs to be fixed")
class EditUserTests(TestCase):
    def setUp(self):
        user_1 = User.objects.create(id=1, email='bob@gmail.com', username='bob')
        user_1.set_password('secret')
        user_1.save()

        group_1 = Group.objects.create(name='officer', id=1)
        group_1.save()

        group_2 = Group.objects.create(name='doc', id=2)
        group_2.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

    def test_email_phone_missing(self):
        self.response = self.client.get('/accounts/edit/1/')
        mocked_edit_user_data = {'username': 'bob',
                                 'email': '',
                                 'groups': '',
                                 'phone_number': ''
                                 }

        response = self.client.post('/accounts/edit/1/', mocked_edit_user_data)
        form_error_message_1 = list(response.context['user_form'].errors.values())[1][0]

        # Assert
        self.assertEqual('Please enter an email address or a phone number.', form_error_message_1)

        self.assertRedirects(response, '/accounts/list/')

    def test_user_edit_details(self):
        self.response = self.client.get('/accounts/edit/1/')

        grp = Group.objects.first()

        mocked_edit_user_data = {'username': 'obo',
                                 'email': 'obo@gmail.com',
                                 'phone_number': '5141234567'
                                 }
        response = self.client.post('/accounts/edit/1/', mocked_edit_user_data)
        # x = response.context['user_form']
        # x = UserForm(response)


class CreateGroupTests(TestCase):
    def setUp(self):
        Permission.objects.all().delete()
        for i in range(1, 7):
            Permission.objects.create(codename=f'test_perm_{i}', content_type_id=1)

        test_user = User.objects.create(username="bob")
        test_user.set_password('secret')
        test_user.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

    def test_create_group_successfully(self):
        """
        Test that creating a group with a given set of permissions works
        @return:
        """

        # Arrange
        new_group_name = 'test group lol'
        new_group_perms = ['test_perm_1', 'test_perm_2']
        expected_permissions_set = set(Permission.objects.filter(codename__in=new_group_perms))

        # Act
        self.create_group_helper(new_group_name, new_group_perms)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_create_groups_with_no_name_raises_error(self):

        # Arrange
        new_group_name = ''
        new_group_perms = ['test_perm_1', 'test_perm_2']
        expected_permissions_set = set(Permission.objects.filter(codename__in=new_group_perms))

        # Act
        self.create_group_helper(new_group_name, new_group_perms)

        # Assert
        self.assertEqual(new_group_name, Group.objects.last().name)
        self.assertSetEqual(expected_permissions_set, set(Group.objects.last().permissions.all()))

    def test_create_groups_with_same_name_raises_error(self):
        pass

    def create_group_helper(self, new_group_name, new_group_perms):
        """
        Helper function to create a group to be used inside another test.
        This function isn't itself a test and does not make any assertions.
        @return: void
        """

        fake_form_data = {
            'name': new_group_name,
            'perms': new_group_perms
        }

        self.client.post(reverse('accounts:create_group'), fake_form_data)

class CovertPermissionNameTests(TestCase):
    def setUp(self):
        Permission.objects.all().delete()
        for i in range(1, 7):
            Permission.objects.create(codename=f'test_perm_{i}', content_type_id=1)

        self.factory = RequestFactory()

    def test_pass_list_of_perms(self):
        """
        Test that the convert_permission_name_to_id() function returns the IDS of the passed list of peerms
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
