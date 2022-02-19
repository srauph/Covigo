from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from symptoms.models import Symptom
from symptoms.views import create_symptom
from symptoms.forms import CreateSymptomForm
from django.core import management


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
