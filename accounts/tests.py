from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, Client, RequestFactory
from accounts.utils import get_flag
from accounts.views import flaguser, unflaguser
from accounts.models import Flag, Staff
from django.urls import reverse
from django.contrib.auth.models import Group


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


class AccountTestCase(TransactionTestCase):

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
