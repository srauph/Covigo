from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    phone_number = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    postal_code = models.CharField(max_length=255, blank=True)
    preferences = models.JSONField(blank=True, null=True)

    class Meta:
        permissions = [
            ("edit_self", "Can edit their own user"),
            ("cancel_appointment", "Can cancel an appointment"),
            ("edit_password", "Can change their own password while logged in"),
            ("edit_username", "Can edit their username"),
            ("edit_name", "Can edit their first and last name"),
            ("edit_email", "Can edit their email address"),
            ("edit_phone", "Can edit their phone number"),
            ("edit_address", "Can edit their address and postal code"),
            ("system_message_preference", "Can edit their system message preference"),
            ("status_deadline_reminder_preference", "Can edit their status update deadline reminder preference"),
            ("appointment_reminder_preference", "Can edit their appointment reminder preference"),
        ]

    def __str__(self):
        return f"{self.user}_profile"


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )

    class Meta:
        permissions = [
            ("is_doctor", "Staff member is a doctor user"),
            ("flag_assigned", "Can flag assigned patients"),
            ("flag_patients", "Can flag any patient"),
            ("flag_view_all", "Can view all assigned flags"),
            ("create_patient", "Can add a patient user"),
            ("create_user", "Can add any user"),
            ("edit_assigned", "Can edit assigned patients"),
            ("edit_patient", "Can edit any patient"),
            ("edit_user", "Can edit any user"),
            ("remove_availability", "Can delete an appointment availability"),
            ("manage_groups", "Can create a new group or edit existing groups"),
            ("assign_group", "Can edit a new or existing user's assigned groups"),
            ("message_assigned", "Can compose a new message with assigned patients"),
            ("message_patient", "Can compose a new message with any patient"),
            ("message_user", "Can compose a new message with any user"),
            ("manage_symptoms", "Can create, edit, enable, or disable symptoms"),
            ("assign_symptom_assigned", "Can assign or update symptoms for assigned patients"),
            ("assign_symptom_patient", "Can assign or update symptoms for any patient"),
            ("dashboard_covigo_data", "Can view Covigo case data in dashboard"),
            ("dashboard_external_data", "Can view external case data in dashboard"),
            ("view_patient_code", "Can view any patient's QR and patient code"),
            ("view_patient_confirmed", "Can view any patient's confirmed status"),
            ("view_patient_negative", "Can view any patient's latest test status (negative or must test)"),
            ("view_patient_quarantine", "Can view any patient's quarantine status"),
            ("set_patient_case", "Can edit any patient's case status (confirmed and latest test)"),
            ("set_patient_quarantine", "Can edit any patient's quarantine status"),
            ("view_patient_test_report", "Can view any patient's test report"),
            ("view_assigned_code", "Can view an assigned patient's QR and patient code"),
            ("view_assigned_confirmed", "Can view an assigned patient's confirmed status"),
            ("view_assigned_negative", "Can view an assigned patient's latest test status (negative or must test)"),
            ("view_assigned_quarantine", "Can view an assigned patient's quarantine status"),
            ("set_assigned_case", "Can edit an assigned patient's case status (confirmed and latest test)"),
            ("set_assigned_quarantine", "Can edit an assigned patient's quarantine status"),
            ("view_assigned_test_report", "Can view an assigned patient's test report"),
            ("view_assigned_doctor", "Can view any patient's assigned doctor"),
            ("edit_assigned_doctor", "Can manage doctor patient assignments and reassign a patient to any other doctor"),
            ("view_assigned_patients", "Can view a doctor's assigned patients"),
            ("view_manager_data", "Can view the data in the Management page"),
            ("edit_preference_user", "Can edit another user's preferences"),
            ("view_assigned_list", "Can view their assigned patients in Accounts page"),
            ("view_patient_list", "Can view all patients in Accounts page"),
            ("view_user_list", "Can view all users in the Accounts page"),
            ("manage_contact_tracing", "Can access the contact tracing management page"),
            ("manage_case_data", "Can access the case data management page"),
            # ("request_resubmission", "Can request that a patient resubmit their status report"),
            # ("view_status_assigned", "Can view assigned patients' status reports"),
            # ("view_status_any", "Can view any patient's status report"),
        ]

    def get_assigned_patient_users(self):
        return User.objects.filter(patient__in=self.assigned_patients.all())

    def __str__(self):
        return f"{self.user}_staff"

    def get_active_flag_count(self):
        """
        Gets and returns the active number of flags issued by this staff.
        @return: returns active flag count or else 0
        """
        try:
            return Flag.objects.filter(staff=self.user, is_active=True).count()
        except:
            return 0


class Patient(models.Model):
    """
    is_confirmed: A confirmed patient is one who had covid, either now or previously.
    is_negative: A negative patient is one who is proven to not have covid via a negative test.
                 A patient who isn't negative either has covid or is a "probable case"
    is_quarantining: A quarantining patient is one who is in isolation.
                     This applies whether they have covid or not (eg living with someone with covid)
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    assigned_staff = models.ForeignKey(
        Staff,
        related_name="assigned_patients",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_confirmed = models.BooleanField(default=False)
    is_negative = models.BooleanField(default=False)
    is_quarantining = models.BooleanField(default=False)
    code = models.CharField(max_length=255)

    class Meta:
        permissions = [
            ("message_doctor", "Can compose a new message with the assigned doctor"),
            ("dashboard_doctor", "Can view the assigned doctor's contact information (name, email, phone number) in dashboard"),
            ("view_own_code", "Can view their own QR and patient code"),
        ]

    def get_assigned_staff_user(self):
        try:
            return self.assigned_staff.user
        except AttributeError:
            return None

    def __str__(self):
        return f"{self.user}_patient"

    def get_active_flag_count(self, staff_user):
        """
        Gets and returns the active flag count for a patient by staff.
        @return: returns active flag count or else 0
        """
        try:
            return Flag.objects.filter(patient=self.user, staff=staff_user, is_active=True).count()
        except Exception:
            return 0


class Flag(models.Model):
    staff = models.ForeignKey(
        User,
        related_name="staffs_created_flags",
        on_delete=models.CASCADE
    )
    patient = models.ForeignKey(
        User,
        related_name="patients_assigned_flags",
        on_delete=models.CASCADE
    )
    is_active = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['staff', 'patient'], name='unique_flag')
        ]

    def __str__(self):
        return f"{self.patient}_flaggedby_{self.staff}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
