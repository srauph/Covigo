import datetime
import json

from django.urls import reverse
from django.contrib.auth.models import User
from django.test import TransactionTestCase, RequestFactory

from accounts.models import Patient, Staff
from accounts.tests.test_views import create_test_client
from appointments.models import Appointment
from appointments.utils import (
    book_appointment,
    cancel_appointment,
    delete_availability,
    rebook_appointment_with_new_doctor,
)


class AppointmentsTestCase(TransactionTestCase):

    # this makes sure that the database ids reset to 1 for every test (especially important for
    # the tests "test_user_can_cancel_appointments" and "test_doctor_can_delete_availabilities" when dealing with fetching appointment ids from the database)
    reset_sequences = True

    def setUp(self):
        """
        initialization of data to be run before every test. Note that not all data initialized here is used
        necessarily in all tests and the decision to include "all" of them here was more for readability choice
        than anything else (for example, "mocked_appointment_data4" and "mocked_appointment_data5" are only ever
        used in one test: "test_appointments_rebooked_with_new_reassigned_doctor")
        :return: void
        """

        self.request = RequestFactory().get('/')

        self.staff1_user = User.objects.create(is_superuser=True, username='PhillyB1', is_staff=True, first_name="Phil", last_name="Baldhead")
        self.doctor1 = Staff.objects.create(user=self.staff1_user)
        self.staff1_user.set_password('BaldMan123')
        self.staff1_user.save()

        self.patient_user = User.objects.create(is_superuser=True, username='JohnnyD2', is_staff=False, first_name="John", last_name="Doe")
        self.patient = Patient.objects.create(user=self.patient_user, assigned_staff=self.doctor1)
        self.patient_user.set_password('JohnGuy123')
        self.patient_user.save()

        self.staff2_user = User.objects.create(username='DocOck13', is_staff=True, first_name="Doc", last_name="Ock")
        self.doctor2 = Staff.objects.create(user=self.staff2_user)
        self.staff2_user.set_password('CookieMan69420')
        self.staff2_user.save()

        self.mocked_appointment_data1 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 20, 6, 0), end_date=datetime.datetime(2022, 5, 20, 7, 0), staff_id=self.doctor1.id)
        self.mocked_appointment_data2 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 21, 6, 0), end_date=datetime.datetime(2022, 5, 21, 7, 0), staff_id=self.doctor1.id)
        self.mocked_appointment_data3 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 22, 6, 0), end_date=datetime.datetime(2022, 5, 22, 7, 0), staff_id=self.doctor1.id)
        self.mocked_appointment_data4 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 20, 6, 0), end_date=datetime.datetime(2022, 5, 20, 7, 0), staff_id=self.doctor2.id)
        self.mocked_appointment_data5 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 21, 6, 0), end_date=datetime.datetime(2022, 5, 21, 7, 0), staff_id=self.doctor2.id)
        self.mocked_appointment_data6 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 22, 6, 0), end_date=datetime.datetime(2022, 5, 22, 7, 0), staff_id=self.doctor2.id)

    def test_patient_can_book_appointments(self):
        """
        this test allows us to test for if one or multiple appointments that are booked by a patient (with the "Book Appointment" and "Book Selected Appointments" buttons)
        ends up actually having their user patient_id added to the patient_id column of the respective appointment row in the appointment database or not
        :return: void
        """

        self.client = create_test_client(test_user=self.patient_user, test_password='JohnGuy123')

        self.response = self.client.get(reverse('appointments:book_appointments'))
        self.assertEqual(self.response.status_code, 200)

        # here, I am checking that, indeed, the proper number of appointment objects were
        # created in the database and are displayed on the template view page for the patient to see
        self.assertTrue(Appointment.objects.filter(staff_id=self.doctor1.id).count() == 3)

        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Book'}))
        loaded_response = json.loads(self.response.content)
        self.assertEqual(str(self.mocked_appointment_data1.start_date.time())[:5], loaded_response['data'][0]['start'])
        self.assertEqual(str(self.mocked_appointment_data1.start_date.date()), loaded_response['data'][0]['date'])
        self.assertEqual(str(self.mocked_appointment_data1.end_date.time())[:5], loaded_response['data'][0]['end'])
        self.assertEqual(str(self.mocked_appointment_data1.end_date.date()), loaded_response['data'][0]['date'])

        self.client.post(reverse('appointments:book_appointments'), {'book_appt': [self.mocked_appointment_data1.id]})
        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Book'}))
        loaded_response = json.loads(self.response.content)

        # here, we expect the user patient's id to be added to the patient_id column
        # of this specific appointment to signal that it was indeed properly booked by this
        # patient (simulates the patient booking only one individual appointment
        # using the "Book Appointment" button), thus, logically, there should be one
        # less available appointment (2 remaining appointments offered by this currently
        # assigned doctor) in the template/page context
        self.assertTrue(Appointment.objects.get(id=1).patient_id == self.patient_user.id)
        self.assertEqual(2, len(loaded_response['data']))

        self.assertEqual(str(self.mocked_appointment_data2.start_date.time())[:5], loaded_response['data'][0]['start'])
        self.assertEqual(str(self.mocked_appointment_data2.start_date.date()), loaded_response['data'][0]['date'])
        self.assertEqual(str(self.mocked_appointment_data2.end_date.time())[:5], loaded_response['data'][0]['end'])
        self.assertEqual(str(self.mocked_appointment_data2.end_date.date()), loaded_response['data'][0]['date'])

        self.assertEqual(str(self.mocked_appointment_data3.start_date.time())[:5], loaded_response['data'][1]['start'])
        self.assertEqual(str(self.mocked_appointment_data3.start_date.date()), loaded_response['data'][1]['date'])
        self.assertEqual(str(self.mocked_appointment_data3.end_date.time())[:5], loaded_response['data'][1]['end'])
        self.assertEqual(str(self.mocked_appointment_data3.end_date.date()), loaded_response['data'][1]['date'])

        book_selected_appointments = [self.mocked_appointment_data2.id, self.mocked_appointment_data3.id]

        for mocked_appointment_id in book_selected_appointments:
            self.response = self.client.post(reverse('appointments:book_appointments'), {'book_appt': [mocked_appointment_id]})

        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Book'}))

        # here, we expect the user patient's id to be added to the patient_id column
        # of the remaining 2 appointments to signal that they were indeed properly booked by this
        # patient (simulates the patient booking all selected appointments
        # using the "Book Selected Appointments" button), thus, logically, there
        # should be no more available appointments (0 remaining appointments offered by this
        # currently assigned doctor) in the template/page context
        self.assertTrue(Appointment.objects.get(id=2).patient_id == self.patient_user.id)
        self.assertTrue(Appointment.objects.get(id=3).patient_id == self.patient_user.id)
        self.assertEqual(0, len(json.loads(self.response.content)['data']))

    def test_user_can_cancel_appointments(self):
        """
        this test allows us to test for if one or multiple appointments that are canceled by a user, whether patient or doctor, (with the "Cancel Appointment" and "Cancel Selected Appointments" buttons)
        end up actually setting the patient's id in the respective appointment's patient_id column to "None" in the appointment database or not
        :return: void
        """

        self.client = create_test_client(test_user=self.patient_user, test_password='JohnGuy123')

        self.response = self.client.get(reverse('appointments:cancel_appointments_or_delete_availabilities'))
        self.assertEqual(self.response.status_code, 200)

        # here, I am checking that, indeed, the proper number of
        # appointment objects are already present in the database
        self.assertTrue(Appointment.objects.filter(staff_id=self.doctor1.id).count() == 3)

        self.client.post(reverse('appointments:cancel_appointments_or_delete_availabilities'), {'book_appt': [self.mocked_appointment_data1.id]})
        self.client.post(reverse('appointments:cancel_appointments_or_delete_availabilities'), {'cancel_appt': [self.mocked_appointment_data1.id]})

        # here, we expect the user patient's id to be removed from the patient_id column
        # of this specific booked appointment by setting the patient_id column to "None"
        # to signal that it was indeed properly canceled by this user/patient (simulates the user/patient
        # cancelling only one individual appointment using the "Cancel Appointment" button)
        self.assertTrue(Appointment.objects.get(id=1).patient_id is None)

        self.booked_appointment = book_appointment(self.request, self.mocked_appointment_data2.id, self.patient_user, False)
        self.booked_appointment = book_appointment(self.request, self.mocked_appointment_data3.id, self.patient_user, False)

        cancel_selected_appointments = [self.mocked_appointment_data2.id, self.mocked_appointment_data3.id]

        for mocked_appointment_id in cancel_selected_appointments:
            self.response = self.client.post(reverse('appointments:cancel_appointments_or_delete_availabilities'), {'cancel_appt': [mocked_appointment_id]})

        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Cancel'}))

        # here, we expect the user patient's id to be removed from the patient_id column
        # of the remaining 2 booked appointments to signal that they were indeed properly canceled by this
        # user/patient (simulates the user/patient cancelling all selected appointments
        # using the "Cancel Selected Appointments" button), thus, logically, there
        # should be no more booked appointments (0 remaining booked appointments with this
        # currently assigned doctor) in the template/page context
        self.assertTrue(Appointment.objects.get(id=2).patient_id is None)
        self.assertTrue(Appointment.objects.get(id=3).patient_id is None)
        self.assertEqual(0, len(json.loads(self.response.content)['data']))

    def test_doctor_can_delete_availabilities(self):
        """
        this test allows us to test for if one or multiple availabilities that are deleted by a doctor (with the "Delete Availability" and "Delete Selected Availabilities" buttons)
        end up actually being deleted from the appointment database or not by deleting the entire respective appointment object row
        :return: void
        """

        self.client = create_test_client(test_user=self.staff1_user, test_password='BaldMan123')

        self.response = self.client.get(reverse('appointments:cancel_appointments_or_delete_availabilities'))
        self.assertEqual(self.response.status_code, 200)

        # here, I am checking that, indeed, the proper number of
        # appointment objects are already present in the database
        self.assertTrue(Appointment.objects.filter(staff_id=self.doctor1.id).count() == 3)

        self.client.post(reverse('appointments:cancel_appointments_or_delete_availabilities'), {'delete_avail': [self.mocked_appointment_data1.id]})
        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Cancel'}))

        # here, we expect the entire respective appointment object to be deleted completely from the database
        # to signal that it was indeed properly deleted by this doctor (simulates the doctor deleting only one individual
        # availability using the "Delete Availability" button), thus, logically, there should be one less open
        # availability (2 remaining availabilities this currently assigned doctor has) in the template/page context
        self.assertTrue(Appointment.objects.filter(staff_id=self.doctor1.id).count() == 2)
        self.assertEqual(2, len(json.loads(self.response.content)['data']))

        delete_selected_availabilities = [self.mocked_appointment_data2.id, self.mocked_appointment_data3.id]

        for mocked_appointment_id in delete_selected_availabilities:
            self.client.post(reverse('appointments:cancel_appointments_or_delete_availabilities'), {'delete_avail': [mocked_appointment_id]})

        self.response = self.client.get(reverse('appointments:current_appointments_table', kwargs={'mode': 'Cancel'}))

        # here, we expect the remaining 2 appointment objects to be deleted completely from the database
        # to signal that they were indeed properly deleted by this doctor (simulates the doctor deleting all
        # selected availabilities using the "Delete Selected Availabilities" button), thus, logically,
        # there should be no more open availability (0 remaining availabilities this currently
        # assigned doctor has) in the template/page context
        self.assertTrue(Appointment.objects.filter(staff_id=self.doctor1.id).count() == 0)
        self.assertEqual(0, len(json.loads(self.response.content)['data']))

    def test_appointments_rebooked_with_new_reassigned_doctor(self):
        """
        this test allows us to test for if one or multiple appointments that are booked by a patient with one doctor end up actually
        being transferred to another newly assigned doctor, if this new doctor has the same appointment availabilities as the old one, or not
        :return: void
        """

        self.mocked_appointment_data7 = Appointment.objects.create(start_date=datetime.datetime(2022, 5, 23, 6, 0), end_date=datetime.datetime(2022, 5, 23, 7, 0), staff_id=self.doctor1.id)

        self.client = create_test_client(test_user=self.patient_user, test_password='JohnGuy123')

        self.response = self.client.get(reverse('appointments:book_appointments'))
        self.assertEqual(self.response.status_code, 200)

        # here, I am checking that, indeed, the proper number of
        # appointment objects are already present in the database
        self.assertTrue(Appointment.objects.all().count() == 7)

        book_selected_appointments = [self.mocked_appointment_data1.id, self.mocked_appointment_data2.id, self.mocked_appointment_data3.id]

        for mocked_appointment_id in book_selected_appointments:
            self.booked_appointments = book_appointment(self.request, mocked_appointment_id, self.patient_user, False)

        rebook_appointment_with_new_doctor(self.mocked_appointment_data4.staff_id, self.mocked_appointment_data1.staff_id, self.patient_user)

        # here, we expect the user patient's id to be added to the patient_id column
        # of all 3 appointment objects that represent the identical availabilities
        # of the newly assigned doctor in order to signal that they were indeed properly
        # reassigned to the newly assigned doctor (simulates an administrator
        # reassigning a new doctor to a patient with the same appointment availabilities)
        self.assertTrue(Appointment.objects.get(id=4).patient_id == self.patient_user.id)
        self.assertTrue(Appointment.objects.get(id=5).patient_id == self.patient_user.id)
        self.assertTrue(Appointment.objects.get(id=6).patient_id == self.patient_user.id)

        self.booked_appointment = book_appointment(self.request, self.mocked_appointment_data7.id, self.patient_user, False)
        rebook_appointment_with_new_doctor(self.mocked_appointment_data4.staff_id, self.mocked_appointment_data1.staff_id, self.patient_user)

        # here, since the newly assigned doctor does not have an identical open availability
        # like the previously assigned doctor, we expect this specific booked appointment object
        # to be canceled by the system when the reassignment is done by removing the patient's id
        # from the patient_id column of this specific booked appointment and setting its value to "None"
        self.assertTrue(Appointment.objects.get(id=7).patient_id is None)

        # here, I am checking that, indeed, all the appointment objects are still present in the database
        # and that the specific appointment was not indeed deleted from the database but rather simply canceled
        self.assertTrue(Appointment.objects.all().count() == 7)
