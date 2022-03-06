from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from accounts.utils import get_flag
from accounts.views import flag_user, unflag_user
from accounts.models import Flag


class FlagAssigningTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = User.objects.create(id=1, is_staff=1, username="Andrew")
        self.never_flagged_patient = User.objects.create(id=2, username="Jake")
        self.previously_flagged_patient = User.objects.create(id=3, username="John")

    def test_previously_flagged_user(self):
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient)
        response = flag_user(self.request, self.previously_flagged_patient.id)
        self.assertions(response, True, self.previously_flagged_patient)

    def test_never_flagged_user(self):
        response = flag_user(self.request, self.never_flagged_patient.id)
        self.assertions(response, True, self.never_flagged_patient)

    def test_unflag_user(self):
        Flag.objects.create(staff=self.request.user, patient=self.previously_flagged_patient, is_active=True)
        response = unflag_user(self.request, self.previously_flagged_patient.id)
        self.assertions(response, False, self.previously_flagged_patient)

    def test_unflag_never_flagged_user(self):
        response = unflag_user(self.request, self.never_flagged_patient.id)
        self.assertIsNone(get_flag(self.request.user, self.never_flagged_patient))
        self.assertEqual(response.status_code, 302)

    def assertions(self, response, expected, patient):
        flag = get_flag(self.request.user, patient)
        self.assertEqual(flag.is_active, expected)
        self.assertEqual(response.status_code, 302)
