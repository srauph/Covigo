from django.urls import reverse
from symptoms.views import toggle_symptom
from symptoms.models import Symptom, PatientSymptom
from symptoms.utils import symptom_count_by_id
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, Client, RequestFactory


class SymptomTestCase(TransactionTestCase):

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
        self.user.set_password('admin')
        self.user.save()
        self.client.login(username='admin', password='admin')
        self.mocked_form_data1 = {'name': '', 'description': ''}
        self.mocked_form_data2 = {'name': 'Fever', 'description': 'A fever is a temperature problem.'}
        self.mocked_form_data3 = {'name': 'Cold', 'description': 'A cold is a virus that attacks the thing.'}
        self.edited_mocked_form_data2 = {'name': 'Runny Nose', 'description': 'A runny nose is a joke of a problem.'}
        self.edited_mocked_form_data3 = {'name': 'Cough', 'description': 'A cough is air that attacks the lungs.'}
        self.response = self.client.get(reverse('symptoms:create_symptom'))

    def test_empty_forms(self):
        """
        this test allows us to test directly for form fields when dealing with empty forms
        :return: void
        """
        # this insures that the specific GET request has succeeded (OK) through
        # the reverse URL naming attribute for the "create_symptom.html" page
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(Symptom.objects.all().count() == 0)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data1)

        # we expect no symptoms to be added to the database here since nothing has been inputted
        # in the form fields so there's no "real" post data submission
        self.assertTrue(Symptom.objects.all().count() == 0)
        self.assertEqual('This field is required.', list(self.response.context['form'].errors.values())[0][0])

    def test_user_can_create_symptom(self):
        """
        this test allows us to test for if a symptom that is submitted through a form
        (with the "create" button) ends up actually being indeed added to the database or not
        :return: void
        """
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(Symptom.objects.all().count() == 0)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data2)

        # we expect one symptom to be added to the database here, since proper
        # form data has been inputted in the form fields, the form data to still
        # be shown on the view and a success message to be displayed on the template for the user to see
        self.assertTrue(Symptom.objects.all().count() == 1)
        self.assertEqual('The symptom was created successfully.', str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.mocked_form_data2['name'], self.response.context['form']['name'].value())
        self.assertEqual(self.mocked_form_data2['description'], self.response.context['form']['description'].value())

        # here, I am testing for the form error message by making sure that it works: If I
        # use the same mocked form data and try to call a POST request on it, I should expect the error message to be shown
        # on the view, alerting me of my mistake, and prevent me from creating a duplicate symptom in the database, thus my database symptom count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data2)
        self.assertTrue(Symptom.objects.all().count() == 1)
        self.assertEqual('The symptom was not created successfully: This symptom name already exists for a given symptom. Please change the symptom name.', str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.mocked_form_data2['name'], self.response.context['form']['name'].value())
        self.assertEqual(self.mocked_form_data2['description'], self.response.context['form']['description'].value())

    def test_user_can_create_symptom_and_return(self):
        """
        this test allows us to test for if a symptom that is submitted through a form
        (with the "create and return" button) ends up actually being indeed added to the database or not
        :return: void
        """
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(Symptom.objects.all().count() == 0)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data2)
        self.assertEqual('The symptom was created successfully.', str(list(self.response.context['messages'])[0]))
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data3)
        self.assertEqual('The symptom was created successfully.', str(list(self.response.context['messages'])[0]))

        # we expect two symptoms to be added to the database here since proper
        # form data has been inputted in the form fields
        self.assertTrue(Symptom.objects.all().count() == 2)

        # here, I am testing for the form error message by making sure that it works: If I
        # use the same mocked form data and try to call a POST request on it, I should expect the error message to be shown
        # on the view, alerting me of my mistake, and prevent me from creating a duplicate symptom in the database, thus my database symptom count
        # should not increase (intended behaviour)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data3)
        self.assertTrue(Symptom.objects.all().count() == 2)
        self.assertEqual('The symptom was not created successfully: This symptom name already exists for a given symptom. Please change the symptom name.', str(list(self.response.context['messages'])[0]))
        self.response = self.client.get(reverse('symptoms:list_symptoms'))
        self.assertEqual(self.response.status_code, 200)

        # these two assertions below check that the list of symptoms page actually shows
        # the two posted symptoms in its context
        self.assertEqual(set(self.response.context['symptoms']), set(Symptom.objects.all()))
        self.assertEqual(
            list(self.response.context['symptoms'].values("description")),
            list(Symptom.objects.values("description"))
        )

    def test_user_can_edit_symptom_and_return(self):
        """
        this test allows us to test for if a symptom that is edited and submitted through a form
        ends up actually being indeed properly edited in the list of symptoms and in the database or not
        :return: void
        """
        self.assertEqual(self.response.status_code, 200)

        # we should expect to have no symptoms in the database if we start with an empty database
        self.assertTrue(Symptom.objects.all().count() == 0)
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data2)
        self.assertEqual('The symptom was created successfully.', str(list(self.response.context['messages'])[0]))
        self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data3)
        self.assertEqual('The symptom was created successfully.', str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(Symptom.objects.all().count() == 2)

        # for lack of details, this following statement would translate to the "edit_symptom.html" page
        # opening up with a specific symptom from the symptom list already loaded on its form on the view
        # and ready to be edited
        self.response = self.client.get(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=1).id}
                    )
        )
        self.assertEqual(self.response.status_code, 200)

        # for lack of details, this following statement would translate to an administrator making a change/edit
        # to the form data of an existing symptom taken from the symptom list and "posting" that new symptom back
        # to the view of the "list_symptoms.html" page
        self.response = self.client.post(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=1).id}
                    ),
            self.edited_mocked_form_data2
        )
        self.response = self.client.get(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=2).id}
                    )
        )
        self.assertEqual(self.response.status_code, 200)
        self.response = self.client.post(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=2).id}
                    ),
            self.edited_mocked_form_data3
        )

        # here, I am testing for the form error message by making sure that it works: If I
        # try to submit the same mocked form data with no edits on both the symptom name and description
        # by calling a POST request on it, I should expect the error message to be shown
        # on the view as the form should return the error message and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=2).id}
                    ),
            self.edited_mocked_form_data3
        )
        self.assertEqual('The symptom was not edited successfully: No edits made on this symptom. If you wish to make no changes, please click the "Cancel" button to go back to the list of symptoms.', str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.edited_mocked_form_data3['name'], self.response.context['form']['name'].value())
        self.assertEqual(self.edited_mocked_form_data3['description'], self.response.context['form']['description'].value())

        # if I try to submit an edited symptom that has a symptom name already identical to an existing one, I should
        # also expect a form error message to be shown on the view as the form should return the error message
        # and alert me of my mistake (intended behaviour)
        self.response = self.client.post(
            reverse('symptoms:edit_symptom',
                    kwargs={'symptom_id': Symptom.objects.get(id=2).id}
                    ),
            self.edited_mocked_form_data2
        )
        self.assertEqual('The symptom was not edited successfully: This symptom name already exists for a given symptom. Please change the symptom name.', str(list(self.response.context['messages'])[0]))

        # this just makes sure that the database still contains
        # the same number of symptoms in it as it did earlier, thus
        # showing that the contents of existing symptoms
        # were changed, rather than the changes showing up
        # as new symptoms in the database entirely
        self.assertTrue(Symptom.objects.all().count() == 2)
        self.response = self.client.get(reverse('symptoms:list_symptoms'))
        self.assertEqual(self.response.status_code, 200)

        # these two assertions below check that the list of symptoms page actually shows
        # the two posted symptoms with changes in its context
        self.assertEqual(set(self.response.context['symptoms']), set(Symptom.objects.all()))
        self.assertEqual(
            list(self.response.context['symptoms'].values("description")),
            list(Symptom.objects.values("description"))
        )


class ToggleSymptomTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory().get('/')
        cls.request.user = User()
        cls.symptom = Symptom.objects.create(name="test_symptom")

    def test_set_active(self):
        cases = [
            {'is_active': True, 'expected': False, 'msg': "When is_active is True"},
            {'is_active': False, 'expected': True, 'msg': "When is_active is False"}
        ]
        for case in cases:
            with self.subTest(case.get('msg')):
                self.symptom.is_active = case.get('is_active')
                self.symptom.save()
                toggle_symptom(self.request, self.symptom.id)
                self.symptom.refresh_from_db()
                self.assertEqual(case.get('expected'), self.symptom.is_active)


class CountSymptomsByIDTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(1, 4):
            Symptom.objects.create(id=i)
            User.objects.create(id=i, username=f"User{i}")

        for i in range(1, 4):
            # Assign all symptoms to users 1 and 2
            PatientSymptom.objects.create(symptom_id=i, user_id=1)
            PatientSymptom.objects.create(symptom_id=i, user_id=2)

        # Assign symptoms 1 and 3 to user 3 ONLY (do not assign symptom 2 to user 3)
        PatientSymptom.objects.create(symptom_id=1, user_id=3)
        PatientSymptom.objects.create(symptom_id=3, user_id=3)

    def test_count_id(self):
        cases = [
            {'input_list': [1], 'expected': 3, 'msg': "When input_list is [1]"},
            {'input_list': [2], 'expected': 2, 'msg': "When input_list is [2]"},
            {'input_list': [1, 2], 'expected': 2, 'msg': "When input_list is [1, 2]"},
            {'input_list': [1, 2, 3], 'expected': 2, 'msg': "When input_list is [1, 2, 3]"}
        ]
        for case in cases:
            with self.subTest(case.get('msg')):
                self.assertEqual(case.get('expected'), symptom_count_by_id(case.get('input_list')))
