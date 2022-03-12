from django.test import TestCase
from accounts.models import *
from django.contrib.auth.models import User


class PatientTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create(username="Patient")
        self.patient2_user = User.objects.create(username="Patient2")
        staff_user = User.objects.create(username="Staff")
        self.staff = Staff.objects.create(user=staff_user)

        self.patient = Patient.objects.create(
            staff=self.staff,
            user=self.patient_user,
            is_confirmed=True,
            is_recovered=True,
            is_quarantining=True,
            code="B0XXYB4B33"
        )
        self.patient2 = Patient.objects.create(user=self.patient2_user, staff=self.staff,)

    def test_patient_set_attributes(self):
        self.assertTrue(self.patient.is_confirmed)
        self.assertTrue(self.patient.is_recovered)
        self.assertTrue(self.patient.is_quarantining)
        self.assertEqual(self.patient.code, "B0XXYB4B33")

    def test_patient_default_attributes(self):
        self.assertFalse(self.patient2.is_confirmed)
        self.assertFalse(self.patient2.is_recovered)
        self.assertFalse(self.patient2.is_quarantining)
        self.assertEqual(self.patient2.code, "")


class PatientStaffTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        patient1_user = User.objects.create(username="Patient1")
        patient2_user = User.objects.create(username="Patient2")
        staff_user = User.objects.create(username="Staff")

        cls.staff = Staff.objects.create(user=staff_user)
        cls.patient = Patient.objects.create(user=patient1_user, staff=cls.staff)
        cls.patient2 = Patient.objects.create(user=patient2_user, staff=cls.staff)

        cls.patients = Patient.objects.all()

    def test_patient_staff_relationship(self):
        self.assertEqual(self.patient.staff, self.staff)

    def test_staff_patient_relationship(self):
        self.assertEqual(self.staff.patients.first(), self.patient)

    def test_staff_patient_set_relationship(self):
        #
        self.assertEqual(set(self.staff.patients.all()), set(self.patients))

