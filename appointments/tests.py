import datetime
from unittest import skip

from django.urls import reverse
from accounts.models import Patient, Staff
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from accounts.tests.test_views import create_test_client
from appointments.models import Appointment


class AppointmentsTestCase(TransactionTestCase):
    # this makes sure that the database ids reset to 1 for every test (especially important for
    # the tests "test_user_can_cancel_appointments" and "test_doctor_can_delete_availabilities" when dealing with fetching appointment ids from the database)
    reset_sequences = True

    def setUp(self):
        """
        initialization of data to be run before every test. Note that not all data initialized here is used
        necessarily in all tests and the decision to include "all" of them here was more for readability choice
        than anything else (for example, "edited_mocked_form_data2" and "edited_mocked_form_data3" are only ever
        used in one test: "test_user_can_edit_symptom_and_return")
        :return: void
        """

        self.staff_user = User.objects.create(username='PhillyB1', is_staff=True, first_name="Phil",
                                              last_name="Baldhead")
        self.staff = Staff.objects.create(user=self.staff_user)
        self.staff_user.set_password('BaldMan123')
        self.staff_user.save()

        self.patient_user = User.objects.create(username='JohnnyD2', is_staff=False, first_name="John", last_name="Doe")
        self.patient = Patient.objects.create(user=self.patient_user, assigned_staff=self.staff_user.staff)
        self.patient_user.set_password('JohnGuy123')
        self.patient_user.save()

        self.mocked_form_data1 = {'name': '', 'description': ''}
        self.mocked_form_data2 = {'name': 'Fever', 'description': 'A fever is a temperature problem.'}
        self.mocked_form_data3 = {'name': 'Cold', 'description': 'A cold is a virus that attacks the thing.'}
        self.edited_mocked_form_data2 = {'name': 'Runny Nose', 'description': 'A runny nose is a joke of a problem.'}
        self.edited_mocked_form_data3 = {'name': 'Cough', 'description': 'A cough is air that attacks the lungs.'}

    # def test_doctor_can_add_availabilities(self):

    @skip
    def test_patient_can_book_appointments(self):
        """
        this test allows us to test for if one or multiple appointments that are booked by a patient (with the "Book Appointment" and "Book Selected Appointments" button)
        end up actually having their user patient_id added to the patient_id column of the respective appointment row in the appointment database or not
        :return: void
        """
        self.client = create_test_client(test_user=self.staff_user, test_password='BaldMan123')
        self.mocked_form_data = {
            'start_date': '2022-03-27',
            'end_date': '2022-04-02',
            'availability_days': ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
            'slot_duration_hours': 1,
            'slot_duration_minutes': 0,
        }
        self.response = self.client.get(reverse('appointments:add_availabilities'))
        self.assertEqual(self.response.status_code, 200)
        self.assertTrue(Appointment.objects.all().count() == 0)
        self.response = self.client.post(reverse('appointments:add_availabilities'), self.mocked_form_data)

        # since I am using the default start and end times (6:00 AM to 7:00 AM), we expect 7 "open" appointments/availabilities (1 hour slot duration from 6 AM to 7 AM * 7 selected weekdays)
        # to be added to the database here, since proper form data has been inputted in the form fields, and a success message to be displayed on the template for the doctor to see
        self.assertEqual(7, Appointment.objects.all().count())
        self.assertEqual('The availabilities have been created.', str(list(self.response.context['messages'])[0]))
        self.assertEqual(self.mocked_form_data2['name'], self.response.context['form']['name'].value())
        self.assertEqual(self.mocked_form_data2['description'], self.response.context['form']['description'].value())

        # here, I am testing for the form error message by making sure that it works: If I
        # use the same mocked form data and try to call a POST request on it, I should expect the error message to be shown
        # on the view, alerting me of my mistake, and prevent me from creating a duplicate symptom in the database, thus my database symptom count
        # should not increase (intended behaviour)
        # self.response = self.client.post(reverse('symptoms:create_symptom'), self.mocked_form_data2)
        # self.assertTrue(Appointment.objects.all().count() == 1)
        # self.assertEqual('The symptom was not created successfully: This symptom name already exists for a given symptom. Please change the                symptom name.', str(list(self.response.context['messages'])[0]))
        # self.assertEqual(self.mocked_form_data2['name'], self.response.context['form']['name'].value())
        # self.assertEqual(self.mocked_form_data2['description'], self.response.context['form']['description'].value())
