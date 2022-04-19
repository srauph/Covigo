from django.contrib.auth.models import User
from django.test import TransactionTestCase, RequestFactory
from django.urls import reverse

from accounts.models import Staff, Patient
from accounts.tests.test_views import create_test_client


class DoctorReassignmentsTestCase(TransactionTestCase):

    # this makes sure that the database ids reset to 1 for every test (especially important for
    # the tests "test_user_can_assign_patient" and "test_user_can_reassign_patient" when dealing with updating patient assigned staff ids from the database)
    reset_sequences = True

    def setUp(self):
        """
        initialization of data to be run before every test. Note that not all data initialized here is used
        necessarily in all tests and the decision to include "all" of them here was more for readability choice
        than anything else (for example, "doctor2" is only ever used in one test: "test_user_can_reassign_patient")
        :return: void
        """

        self.request = RequestFactory().get('/')

        self.staff1_user = User.objects.create(is_superuser=True, username='admin')
        self.admin = Staff.objects.create(user=self.staff1_user)
        self.staff1_user.set_password('admin')
        self.staff1_user.save()

        self.staff2_user = User.objects.create(is_superuser=True, username='PhillyB1', is_staff=True, first_name="Phil", last_name="Baldhead")
        self.doctor1 = Staff.objects.create(user=self.staff2_user)
        self.staff2_user.set_password('BaldMan123')
        self.staff2_user.save()

        self.patient_user = User.objects.create(is_superuser=True, username='JohnnyD2', is_staff=False, first_name="John", last_name="Doe")
        self.patient = Patient.objects.create(user=self.patient_user)
        self.patient_user.set_password('JohnGuy123')
        self.patient_user.save()

        self.staff3_user = User.objects.create(is_superuser=True, username='DocOck13', is_staff=True, first_name="Doc", last_name="Ock")
        self.doctor2 = Staff.objects.create(user=self.staff3_user)
        self.staff3_user.set_password('CookieMan69420')
        self.staff3_user.save()

    def test_user_can_assign_patient(self):
        """
        this test allows us to test for if an admin/user with the right permissions that assigns a patient to a doctor successfully (with the "Assign" button)
        ends up actually having the specific assigned doctor's id added to the assigned_staff_id column of the respective patient row in the patient database or not
        :return: void
        """

        self.client = create_test_client(test_user=self.staff1_user, test_password='admin')

        self.response = self.client.get(reverse('manager:reassign_doctor',
                                                kwargs={'user_id': self.patient_user.id})
                                        )
        self.assertEqual(self.response.status_code, 200)

        # we should expect the assigned_staff_id column for the specific patient row
        # in the database to be None since no doctor has been assigned to this patient yet
        self.assertEqual(None, self.patient_user.patient.assigned_staff_id)

        # here, we are assigning a specific doctor to the patient we expect the assigned_staff_id column for the
        # specific patient row in the database to be updated accordingly since now a new doctor has been assigned
        # to this patient
        self.response = self.client.post(reverse('manager:reassign_doctor',
                                                 kwargs={'user_id': self.patient_user.id}
                                                 ),
                                         {'new_doctor_id': self.staff2_user.id}
                                         )
        self.patient_user.refresh_from_db()

        self.assertEqual(self.doctor1.id, self.patient_user.patient.assigned_staff_id)

    def test_user_can_reassign_patient(self):
        """
        this test allows us to test for if an admin/user with the right permissions that reassigns a patient to a new doctor successfully (with the "Reassign" button)
        ends up actually having the old assigned doctor's id changed to the new one in the assigned_staff_id column of the respective patient row in the patient database or not
        :return: void
        """

        self.client = create_test_client(test_user=self.staff1_user, test_password='admin')

        self.response = self.client.get(reverse('manager:reassign_doctor',
                                                kwargs={'user_id': self.patient_user.id})
                                        )
        self.assertEqual(self.response.status_code, 200)

        self.response = self.client.post(reverse('manager:reassign_doctor',
                                                 kwargs={'user_id': self.patient_user.id}
                                                 ),
                                         {'new_doctor_id': self.staff2_user.id}
                                         )
        self.patient_user.refresh_from_db()

        self.assertEqual(self.doctor1.id, self.patient_user.patient.assigned_staff_id)

        # here, we are reassigning the patient to a new specific doctor, so we expect the assigned_staff_id column for the
        # specific patient row in the database to be updated accordingly by being changed to the new doctor's id since now
        # a new doctor has been reassigned to this patient
        self.response = self.client.post(reverse('manager:reassign_doctor',
                                                 kwargs={'user_id': self.patient_user.id}
                                                 ),
                                         {'new_doctor_id': self.staff3_user.id}
                                         )
        self.patient_user.refresh_from_db()

        # here, we can see that the assigned_staff_id column for the specific patient row in the database clearly has been updated/changed with the new doctor's id
        self.assertEqual(self.doctor2.id, self.patient_user.patient.assigned_staff_id)

    def test_user_can_unassign_patient(self):
        """
        this test allows us to test for if an admin/user with the right permissions that unassigns a patient from a doctor successfully (with the "Unassign" button)
        ends up actually having the assigned doctor's id removed from the assigned_staff_id column of the respective patient row in the patient database or not
        :return: void
        """

        self.client = create_test_client(test_user=self.staff1_user, test_password='admin')

        self.response = self.client.get(reverse('manager:reassign_doctor',
                                                kwargs={'user_id': self.patient_user.id})
                                        )
        self.assertEqual(self.response.status_code, 200)

        self.response = self.client.post(reverse('manager:reassign_doctor',
                                                 kwargs={'user_id': self.patient_user.id}
                                                 ),
                                         {'new_doctor_id': self.staff2_user.id}
                                         )
        self.patient_user.refresh_from_db()

        self.assertEqual(self.doctor1.id, self.patient_user.patient.assigned_staff_id)

        # here, we are unassigning the patient from their current assigned doctor by setting the doctor's id to -1, so we expect the assigned_staff_id column for the
        # specific patient row in the database to be updated accordingly by being changed and having its current value deleted/removed since now the old assigned doctor
        # has been unassigned from this patient
        self.response = self.client.post(reverse('manager:reassign_doctor',
                                                 kwargs={'user_id': self.patient_user.id}
                                                 ),
                                         {'new_doctor_id': -1}
                                         )
        self.patient_user.refresh_from_db()

        # here, we can see that the assigned_staff_id column for the specific patient row in the database clearly has been updated/changed by removing/deleting the old assigned doctor's id
        self.assertEqual(None, self.patient_user.patient.assigned_staff_id)
