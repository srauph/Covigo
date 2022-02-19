from symptoms.views import create_symptom, toggle_symptom
from symptoms.forms import CreateSymptomForm
from django.core import management
from django.utils.decorators import method_decorator
from symptoms.models import Symptom, PatientSymptom
from symptoms.utils import symptom_count_by_id
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase, Client, RequestFactory


class SymptomCreationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.request = RequestFactory().get('/')
        cls.request = User()
        cls.symptom = Symptom.objects.create()
        cls.cases = [
            {
                'name': "Fever",
                'description': 'A fever is a temperature problem.',
                'expected name': 'Fever',
                'expected description': 'A fever is a temperature problem.',
                'message': "When both the name and the description are inputted."
            },
            {
                'name': 'Cold',
                'description': None,
                'expected name': 'Cold',
                'expected description': None,
                'message': "When only the name is inputted."
            },
            {
                'name': None,
                'description': 'A cold is a virus that attacks the thing.',
                'expected name': None,
                'expected description': 'A cold is a virus that attacks the thing.',
                'message': "When only the description is inputted."
            },
            {
                'name': None,
                'description': None,
                'expected name': None,
                'expected description': None,
                'message': "When both the name and description are not inputted."
            }
        ]

    def test_forms(self):
        empty_form = CreateSymptomForm()
        self.assertIn("name", empty_form.fields)
        self.assertIn("description", empty_form.fields)

    def test_user_can_create_symptom(self):
        for case in self.cases:
            with self.subTest(case.get('message')):
                # self.form.name = self.symptom.name
                # self.form.description = self.symptom.description
                self.symptom.name = case.get('name'),
                self.symptom.description = case.get('description')
                mocked_form = CreateSymptomForm(self.request.POST)
                create_symptom(self.request)
                self.assertTrue(mocked_form.fields["name"])
                self.assertTrue(mocked_form.fields["description"])
                print(mocked_form.errors)
                # self.symptom.name = case.get('symptom name')
                # self.create.description = case.get('symptom description')
                # self.assertTrue(mocked_form.is_valid())
                # self.AssertTrue(mocked_form.cleaned_data.get('name') == self.symptom.name)
                # self.AssertTrue(mocked_form.cleaned_data.get('description') == self.symptom.description)
                mocked_form.save()
                self.assertEqual(case.get('expected name'), mocked_form.name)
                self.assertEqual(case.get('expected description'), mocked_form.description)
                management.call_command('flush', interactive=False)
# Create your tests here.


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
