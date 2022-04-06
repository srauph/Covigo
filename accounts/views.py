import datetime
import json

from django.contrib import messages
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordChangeView, LoginView
from django.core.exceptions import MultipleObjectsReturned, PermissionDenied
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from Covigo.default_permissions import DEFAULT_PERMISSIONS
from Covigo.messages import Messages
from Covigo.settings import PRODUCTION_MODE
from accounts.forms import *
from accounts.models import Flag, Staff, Patient, Code
from accounts.preferences import SystemMessagesPreference, StatusReminderPreference
from accounts.utils import (
    convert_dict_of_bools_to_list,
    dictfetchall,
    get_assigned_staff_id_by_patient_id,
    get_flag,
    get_or_generate_patient_profile_qr,
    get_user_from_uidb64,
    return_closest_with_least_patients_doctor,
    send_system_message_to_user,
)
from appointments.models import Appointment
from appointments.utils import rebook_appointment_with_new_doctor
from geopy import distance
from symptoms.utils import is_symptom_editing_allowed


class GroupErrors:
    def __init__(self):
        self.blank_name = False
        self.duplicate_name = False

    def has_errors(self):
        return self.blank_name or self.duplicate_name


def unauthorized(request):
    return HttpResponse('Unauthorized', status=401)


def process_register_or_edit_user_form(request, user_form, profile_form, mode=None):
    user_email = user_form.data.get("email")
    user_phone = profile_form.data.get("phone_number")
    user_groups = user_form.data.get("groups")
    has_email = user_email != ""
    has_phone = user_phone != ""

    if user_form.is_valid() and profile_form.is_valid() and (has_email or has_phone):
        if mode == "Edit" and not user_form.has_changed() and not profile_form.has_changed():
            messages.error(request,
                           "The account was not edited successfully: No edits made on this account. If you wish to make no changes, please click the \"Cancel\" button to go back to the profile page.")
            return False

        edited_user = user_form.save(commit=False)

        # TODO: Discuss possibility of having no groups and adjust `if` to enforce at least one when editing
        if user_groups:
            edited_user.groups.set(user_groups)

        edited_user.save()
        profile_form.save()

        return True

    else:
        if mode == "Edit" and not (has_email or has_phone):
            messages.error(request, 'Please enter an email address or a phone number.')

        if not user_form.is_valid():
            if "username" in user_form.errors:
                messages.error(request, list(user_form['username'].errors)[0])

            if "email" in user_form.errors:
                messages.error(request, list(user_form['email'].errors)[0])

            if "first_name" in user_form.errors:
                messages.error(request, list(user_form['first_name'].errors)[0])

            if "last_name" in user_form.errors:
                messages.error(request, list(user_form['last_name'].errors)[0])

            if "groups" in user_form.errors:
                messages.error(request, list(user_form['groups'].errors)[0])

        if not profile_form.is_valid():
            if "phone_number" in profile_form.errors:
                messages.error(request, list(profile_form['phone_number'].errors)[0])

            if "address" in profile_form.errors:
                messages.error(request, list(profile_form['address'].errors)[0])

            if "postal_code" in profile_form.errors:
                messages.error(request, list(profile_form['postal_code'].errors)[0])

        return False


def convert_permission_name_to_id(request):
    permission_array = []
    for perm in request.POST.getlist('perms'):
        permission_id = Permission.objects.filter(codename=perm).get().id
        permission_array.append(permission_id)
    return permission_array


class LoginViewTo2FA(LoginView):
    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        self.request.session["start_2fa"] = True
        return super(LoginViewTo2FA, self).dispatch(*args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("accounts:two_factor_authentication")


@never_cache
def two_factor_authentication(request):
    if "start_2fa" not in request.session:
        raise Http404

    del request.session["start_2fa"]

    user = request.user
    code, _ = Code.objects.get_or_create(user=request.user.profile)
    code.save()

    logout(request)

    otp = code.number
    message = "Your OTP is " + otp + ". "
    subject = "Covigo OTP"
    send_system_message_to_user(user, message=message, subject=subject)

    request.session["verify_otp"] = True

    return render(request, 'accounts/authentication/2FA.html', {
        "usr": user
    })


@never_cache
def verify_otp(request, user_id):
    user = User.objects.get(id=user_id)
    code = request.POST.get('code')

    try:
        bypass = not PRODUCTION_MODE and code == "420420"
        if bypass or code == Code.objects.get(user_id=user.id).number:
            login(request, user)
            return redirect('index')
        else:
            raise Code.DoesNotExist
    except Code.DoesNotExist:
        messages.error(
            request,
            "Invalid 2FA code."
        )
        return render(request, 'accounts/authentication/2FA.html', {
            "usr": user,
        })


@never_cache
def forgot_password(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            try:
                user = User.objects.get(email=data)
                template = Messages.RESET_PASSWORD.value
                c = {
                    'token': default_token_generator.make_token(user),
                }
                send_system_message_to_user(user, template=template, c=c)
                return redirect("accounts:forgot_password_done")
            except MultipleObjectsReturned:
                # Should not happen because we don't allow multiple users to share an email.
                # This can only occur if the database is corrupted somehow
                messages.error(request,
                               "More than one user with the given email address could be found. Please contact the system administrators to fix this issue.")
            except User.DoesNotExist:
                # Don't let the user know if the email does not exist in our system
                return redirect("accounts:forgot_password_done")
        else:
            messages.error(request, "Please enter a valid email address or phone number.")
    else:
        password_reset_form = PasswordResetForm()
    return render(
        request=request,
        template_name="accounts/authentication/forgot_password.html",
        context={"form": password_reset_form}
    )


@never_cache
def register_user(request, uidb64, token):
    return redirect('accounts:register_user_password', uidb64=uidb64, token=token)


# Yes it's technically not proper to put a class here but since this is a class-based view that in the flow occurs
# between the register_user and register_user_password_done views, I think it makes more sense to put it here.
class RegisterPasswordResetConfirmView(PasswordResetConfirmView):
    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        self.success_url = reverse_lazy('accounts:register_user_password_done', kwargs={'uidb64': kwargs['uidb64']})
        return super(RegisterPasswordResetConfirmView, self).dispatch(*args, **kwargs)


@never_cache
def register_user_password_done(request, uidb64):
    user = get_user_from_uidb64(uidb64)
    token = default_token_generator.make_token(user)
    return redirect('accounts:register_user_details', uidb64, token)


@never_cache
def register_user_details(request, uidb64, token):
    internal_set_details_session_token = "_set_details_token"
    user = get_user_from_uidb64(uidb64)
    user_id = user.id
    valid = False

    if user is not None:
        if token == 'set-details':
            session_token = request.session.get(internal_set_details_session_token)
            if default_token_generator.check_token(user, session_token):
                # If the token is valid, display the password reset form.
                valid = True
        else:
            if default_token_generator.check_token(user, token):
                # Store the token in the session and redirect to the
                # password reset form at a URL without the token. That
                # avoids the possibility of leaking the token in the
                # HTTP Referer header.
                request.session[internal_set_details_session_token] = token
                redirect_url = request.path.replace(token, 'set-details')
                return redirect(redirect_url, uidb64, token)

    # Process/Create forms if the link is valid
    if valid:
        # Process forms
        if request.method == "POST":
            user_form = RegisterUserForm(request.POST, instance=user, user_id=user_id)
            profile_form = RegisterProfileForm(request.POST, instance=user.profile, user_id=user_id)

            if process_register_or_edit_user_form(request, user_form, profile_form):
                patient = user.patient
                patient.assigned_staff_id = return_closest_with_least_patients_doctor(
                    profile_form.data.get("postal_code")).staff.id
                patient.save()
                request.session[internal_set_details_session_token] = None
                return redirect("accounts:register_user_done")

        # Create forms
        else:
            user_form = RegisterUserForm(instance=user, user_id=user_id, initial={"username": None})
            profile_form = RegisterProfileForm(instance=user.profile, user_id=user_id)

        return render(request, "accounts/registration/register_user_details.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "validlink": True
        })

    # Don't process/create forms if the link is expired or invalid
    else:
        return render(request, "accounts/registration/register_user_details.html", {
            "validlink": False
        })


# As before, even though this is a class-based view, I think it makes sense to put it here.
@method_decorator(sensitive_post_parameters(), name='dispatch')
@method_decorator(csrf_protect, name='dispatch')
@method_decorator(login_required, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class ChangePasswordView(PasswordChangeView):
    form_class = ChangePasswordForm
    success_url = reverse_lazy('accounts:change_password_done')
    template_name = 'accounts/authentication/change_password.html'

    def form_valid(self, form, *args):
        form.save()
        # Uncomment this line to enable the following behaviour:
        # Updating the password logs out all other sessions for the user except the current one.
        # update_session_auth_hash(self.request, form.user)
        template = Messages.CHANGED_PASSWORD.value
        send_system_message_to_user(form.user, template=template)
        return HttpResponseRedirect(self.get_success_url())


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')


@never_cache
def change_password_done(request):
    return render(request, 'accounts/authentication/change_password_done.html')


@login_required
@never_cache
def profile(request, user_id):
    user = User.objects.get(id=user_id)

    # if not request.user.is_staff and request.user != user:
    #     raise PermissionDenied

    today = datetime.date.today()
    all_filter = Q(patient__isnull=False) & Q(start_date__gte=today)

    usr_is_doctor = not user.is_superuser and user.has_perm("accounts.is_doctor")

    perms_edit_user = (
        False if user == request.user and not request.user.has_perm("accounts.edit_self") else
        user == request.user and request.user.has_perm("accounts.edit_self")
        or request.user.has_perm("accounts.edit_user")
        or request.user.has_perm("accounts.edit_patient") and not user.is_staff
        or request.user.has_perm("accounts.edit_assigned") and user in request.user.staff.get_assigned_patient_users()
    )

    perms_view_appointments = (
        user == request.user
        or request.user.has_perm("accounts.view_user_appointment")
        or request.user.has_perm("accounts.view_patient_appointment") and not user.is_staff
        or request.user.has_perm("accounts.is_doctor") and user in request.user.staff.get_assigned_patient_users()
    )



    # If profile belongs to a patient
    if not user.is_staff:
        if request.method == "POST":
            doctor_staff_id = request.POST.get('doctor_id')

            if doctor_staff_id == "-1":
                user.patient.assigned_staff = None
            else:
                # rebooks previously booked appointments with the old doctor with the new doctor if the new doctor has
                # an availability at the same day and time as the previously booked appointment
                rebook_appointment_with_new_doctor(doctor_staff_id, get_assigned_staff_id_by_patient_id(user_id), user)
                user.patient.assigned_staff_id = doctor_staff_id
            user.patient.save()

        qr = get_or_generate_patient_profile_qr(user_id)
        assigned_staff = user.patient.get_assigned_staff_user()

        if request.POST.get('Reassign'):
            messages.success(request, "This patient was reassigned to the new doctor successfully.")

        if request.POST.get('Assign'):
            messages.success(request, "This patient was assigned a new doctor successfully.")

        appointments = Appointment.objects.filter(patient=user).filter(all_filter).order_by("start_date")
        appointments_truncated = appointments[:4]
        try:
            assigned_staff_patient_count = user.patient.assigned_staff.get_assigned_patient_users().count()
        except AttributeError:
            assigned_staff_patient_count = 0

        assigned_flags = Flag.objects.filter(patient=user, is_active=True)

        all_doctors = list(User.objects.with_perm("accounts.is_doctor").exclude(is_superuser=True))
        all_doctors.append({
            "first_name": "(Unassign)",
            "staff": {"id": -1},
        })

        flag = get_flag(request.user, user)
        is_flagged = False if not request.user.is_staff else flag and flag.is_active


        perms_flag = (
            False if not request.user.is_staff else
            request.user.has_perm("accounts.flag_patients") and not user.is_staff
            or request.user.has_perm(
                "accounts.flag_assigned") and user in request.user.staff.get_assigned_patient_users()
        )

        perms_code = (
            user == request.user and request.user.has_perm("accounts.view_own_code")
            or request.user.has_perm("accounts.view_patient_code")
            or (
                request.user.has_perm("accounts.view_assigned_code")
                and user in request.user.staff.get_assigned_patient_users()
            )
        )

        perms_test_report = (
            user == request.user
            or request.user.has_perm("accounts.view_patient_test_report")
            or (
                request.user.has_perm("accounts.view_assigned_test_report")
                and user in request.user.staff.get_assigned_patient_users()
            )
        )

        perms_assigned_doctor = (
            user == request.user
            or request.user.has_perm("accounts.view_assigned_doctor")
            or user in request.user.staff.get_assigned_patient_users()
        )

        perms_message_doctor = (
            not user.is_staff and request.user != user.patient.get_assigned_staff_user() and (
                request.user.has_perm("accounts.message_doctor")
                or request.user.has_perm("accounts.message_user")
            )
        )

        perms_assign_symptoms = (
            not user.is_staff and (
                request.user.has_perm("accounts.assign_symptom_patient")
                or request.user.has_perm(
                "accounts.assign_symptom_assigned") and user in request.user.staff.get_assigned_patient_users()
            )
        )

        perms_edit_case = (
            not user.is_staff and (
                request.user.has_perm("accounts.set_patient_case")
                or request.user.has_perm("accounts.set_patient_quarantine")
                or (
                    request.user.has_perm("accounts.is_doctor")
                    and user in request.user.staff.get_assigned_patient_users()
                    and (
                        request.user.has_perm("accounts.set_assigned_case")
                        or request.user.has_perm("accounts.set_assigned_quarantine")
                    )
                )
            )
        )

        return render(request, 'accounts/profile/profile.html', {
            "usr": user,
            "appointments": appointments,
            "appointments_truncated": appointments_truncated,
            "qr": qr,
            "assigned_staff": assigned_staff,
            "assigned_staff_patient_count": assigned_staff_patient_count,
            "assigned_flags": assigned_flags,
            "full_view": True,
            "allow_editing": is_symptom_editing_allowed(user_id),
            "all_doctors": all_doctors,
            "show_left_side": True,
            "is_flagged": is_flagged,

            "perms_edit_user": perms_edit_user,
            "perms_view_appointments": perms_view_appointments,
            "perms_flag": perms_flag,
            "perms_code": perms_code,
            "perms_test_report": perms_test_report,
            "perms_assigned_doctor": perms_assigned_doctor,
            "perms_message_doctor": perms_message_doctor,
            "perms_assign_symptoms": perms_assign_symptoms,
            "perms_edit_case": perms_edit_case,
        })

    # If profile belongs to a staff member
    else:
        appointments = Appointment.objects.filter(staff=user).filter(all_filter).order_by("start_date")
        appointments_truncated = appointments[:4]
        assigned_patients = [] if user.is_superuser else user.staff.get_assigned_patient_users()
        issued_flags = Flag.objects.filter(staff=user, is_active=True)

        perms_assigned_patients = (
                user == request.user
                or request.user.has_perm("accounts.view_assigned_patients")
        )

        show_left_side = (
            usr_is_doctor and perms_assigned_patients
            or not user.is_staff
        )

        return render(request, 'accounts/profile/profile.html', {
            "usr": user,
            "appointments": appointments,
            "appointments_truncated": appointments_truncated,
            "assigned_patients": assigned_patients,
            "issued_flags": issued_flags,
            "full_view": True,
            "show_left_side": show_left_side,

            "usr_is_doctor": usr_is_doctor,
            "perms_edit_user": perms_edit_user,
            "perms_view_appointments": perms_view_appointments,
            "perms_assigned_patients": perms_assigned_patients,
        })


@never_cache
def profile_from_code(request, code):
    patient = Patient.objects.get(code=code)
    user = User.objects.get(patient=patient)
    image = get_or_generate_patient_profile_qr(user.id)
    return render(request, 'accounts/profile/profile.html', {"qr": image, "usr": user, "full_view": False})


@login_required
@never_cache
def list_users(request):
    if request.user.has_perm("accounts.view_flagged_user_list"):
        flagged_filter = Q(id__in=request.user.staffs_created_flags.exclude(is_active=False).values("patient_id"))
    else:
        flagged_filter = Q()

    if request.user.has_perm("accounts.view_user_list"):
        users = User.objects.all()
    elif request.user.has_perm("accounts.view_patient_list"):
        users = User.objects.filter(is_staff=False)
    elif request.user.has_perm("accounts.view_assigned_list"):
        assigned_filter = Q(patient__in=request.user.staff.assigned_patients.all())
        users = User.objects.filter(flagged_filter | assigned_filter)
    elif request.user.has_perm("accounts.view_flagged_user_list"):
        users = User.objects.filter(flagged_filter)
    else:
        raise PermissionDenied

    return render(request, 'accounts/list_users.html', {
        'users': users
    })


@login_required
@never_cache
def create_user(request):
    can_view_page = (
        request.user.has_perm("accounts.create_user")
        or request.user.has_perm("accounts.create_patient")
    )

    if not can_view_page:
        raise PermissionDenied

    # Process forms
    if request.method == "POST":
        user_form = CreateUserForm(request.POST)
        profile_form = CreateProfileForm(request.POST)

        user_email = user_form.data.get("email")
        user_phone = profile_form.data.get("phone_number")
        user_groups = user_form.data.get("groups")
        has_email = user_email != ""
        has_phone = user_phone != ""

        if user_form.is_valid() and profile_form.is_valid() and (has_email or has_phone):
            new_user = user_form.save(commit=False)

            if has_email:
                new_user.username = user_email
            else:
                if not User.objects.filter(username=user_phone).exists():
                    new_user.username = user_phone
                else:
                    new_user.username = f"{user_phone}-{1 + User.objects.filter(username__startswith=user_phone).count()}"

            new_user.save()
            new_user.profile.phone_number = user_phone
            # TODO: Discuss the possibility of having no groups and remove `if` if we enforce having at least one
            if user_groups:
                new_user.groups.set(user_groups)
            new_user.save()

            if new_user.is_staff:
                Staff.objects.create(user=new_user)
            elif not new_user.is_staff:
                # TODO: Figure out if the next todo has been addressed already or not.
                # TODO: discuss if we should keep this behaviour for now or make Patient.staff nullable instead.
                Patient.objects.create(user=new_user)

            template = Messages.REGISTER_USER.value
            c = {
                'token': default_token_generator.make_token(new_user),
            }

            send_system_message_to_user(new_user, template=template, c=c)

            if request.POST.get('Create'):
                messages.success(request, 'The account was created successfully.')
                return render(request, "accounts/create_user.html", {
                    "user_form": user_form,
                    "profile_form": profile_form
                })

            else:
                messages.success(request, 'The account was created successfully.')
                return redirect('accounts:list_users')

        else:
            if not (has_email or has_phone):
                messages.error(request, 'Please enter an email address or a phone number.')

            if not user_form.is_valid():
                if "email" in user_form.errors:
                    messages.error(request, list(user_form['email'].errors)[0])

                if "groups" in user_form.errors:
                    messages.error(request, list(user_form['groups'].errors)[0])

            if not profile_form.is_valid():
                messages.error(request, list(profile_form.errors.values())[0][0])

    # Create forms
    else:
        user_form = CreateUserForm()
        profile_form = CreateProfileForm()

    return render(request, "accounts/create_user.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })


@login_required
@never_cache
def edit_user(request, user_id):
    user = User.objects.get(id=user_id)

    can_view_page = (
        False if user == request.user and not request.user.has_perm("accounts.edit_self") else
        user == request.user and request.user.has_perm("accounts.edit_self")
        or request.user.has_perm("accounts.edit_user")
        or request.user.has_perm("accounts.edit_patient") and not user.is_staff
        or request.user.has_perm("accounts.edit_assigned") and user in request.user.staff.get_assigned_patient_users()
    )

    if not can_view_page:
        raise PermissionDenied

    edit_perms = {
        "edit_username": False if user == request.user and not request.user.has_perm(
            "accounts.edit_username") else True,
        "edit_email": False if user == request.user and not request.user.has_perm("accounts.edit_email") else True,
        "edit_name": False if user == request.user and not request.user.has_perm("accounts.edit_name") else True,
        "edit_phone": False if user == request.user and not request.user.has_perm("accounts.edit_phone") else True,
        "edit_address": False if user == request.user and not request.user.has_perm("accounts.edit_address") else True,
        "edit_preferences": (
            user != request.user and request.user.has_perm("accounts.edit_preference_user")
            or user == request.user and (
                    request.user.has_perm("accounts.system_message_preference")
                    or request.user.has_perm("accounts.status_deadline_reminder_preference")
                    or request.user.has_perm("accounts.appointment_reminder_preference")
            )
        ),
    }

    # Process forms
    if request.method == "POST":
        user_form = EditUserForm(request.POST, instance=user, user_id=user_id)
        profile_form = EditProfileForm(request.POST, instance=user.profile, user_id=user_id)

        if process_register_or_edit_user_form(request, user_form, profile_form, mode="Edit"):
            messages.success(request, 'The account was edited successfully.')
            return redirect('accounts:profile', user_id)

    # Create forms
    else:
        user_form = EditUserForm(instance=user, user_id=user_id)
        profile_form = EditProfileForm(instance=user.profile, user_id=user_id)

    return render(request, "accounts/edit_user.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "edited_user": user,
        "edit_perms": edit_perms,
    })


@login_required
@never_cache
def edit_preferences(request, user_id):
    user = User.objects.get(id=user_id)
    can_view_page = (
        user != request.user and request.user.has_perm("accounts.edit_preference_user")
        or user == request.user and (
                request.user.has_perm("accounts.system_message_preference")
                or request.user.has_perm("accounts.status_deadline_reminder_preference")
                or request.user.has_perm("accounts.appointment_reminder_preference")
        )
    )

    if not can_view_page:
        raise PermissionDenied

    profile = user.profile

    # Process forms
    if request.method == "POST":
        preferences_form = EditPreferencesForm(request.POST)

        if preferences_form.is_valid():
            if convert_dict_of_bools_to_list(profile.preferences[SystemMessagesPreference.NAME.value]) == preferences_form.cleaned_data.get(SystemMessagesPreference.NAME.value) and profile.preferences[StatusReminderPreference.NAME.value] == preferences_form.cleaned_data.get(StatusReminderPreference.NAME.value):
                messages.error(request, f"The account preferences settings were not edited successfully: No edits made on the current account preferences settings. If you wish to make no changes, please click the \"Cancel\" button to go back to your account information in the previous page.")
                return render(request, "accounts/edit_preferences.html", {
                    "preferences_form": preferences_form,
                    "usr": user
                })

            system_msg_preferences = preferences_form.cleaned_data.get(SystemMessagesPreference.NAME.value)
            status_reminder_interval = preferences_form.cleaned_data.get(StatusReminderPreference.NAME.value)

            # Convert to dict to store in profile
            preferences = {
                SystemMessagesPreference.NAME.value: {
                    SystemMessagesPreference.EMAIL.value: "use_email" in system_msg_preferences,
                    SystemMessagesPreference.SMS.value: "use_sms" in system_msg_preferences
                },

                StatusReminderPreference.NAME.value: status_reminder_interval,
            }

            profile.preferences = preferences
            profile.save()

            messages.success(request, f"The account preferences settings were edited successfully.")
            return redirect("accounts:edit_user", user_id)

        else:
            messages.error(request, "Please select at least one system messages preferences method.")

    # Create forms
    else:
        # Try to load current preferences
        if profile.preferences:
            # Load previous user-defined preferences
            old_preferences = dict()

            old_preferences[SystemMessagesPreference.NAME.value] = convert_dict_of_bools_to_list(
                profile.preferences[SystemMessagesPreference.NAME.value])

            if StatusReminderPreference.NAME.value in profile.preferences:
                old_preferences[StatusReminderPreference.NAME.value] = profile.preferences[
                    StatusReminderPreference.NAME.value]
            else:
                # TODO: Replace this with admin-defined default advance warning, if we implement it.
                old_preferences[StatusReminderPreference.NAME.value] = 2

            preferences_form = EditPreferencesForm(old_preferences)
        else:
            # Create a blank form if user has no preferences
            preferences_form = EditPreferencesForm()

    return render(request, "accounts/edit_preferences.html", {
        "preferences_form": preferences_form,
        "usr": user
    })


@login_required
@never_cache
def list_groups(request):
    if not request.user.has_perm("accounts.manage_groups"):
        raise PermissionDenied

    return render(request, 'accounts/access_control/groups/list_groups.html', {
        'groups': Group.objects.all()
    })


@login_required
@never_cache
def create_group(request):
    if not request.user.has_perm("accounts.manage_groups"):
        raise PermissionDenied

    non_default_permissions = Permission.objects.all().exclude(codename__in=DEFAULT_PERMISSIONS)
    new_name = ''

    if request.method == 'POST':
        new_name = request.POST['name']

        if not new_name:
            messages.error(request, 'Please enter a group/role name.')

        elif Group.objects.filter(name=new_name).exists():
            messages.error(request, 'Another group/role with the same name exists.')

        else:
            group = Group(name=new_name)
            group.save()

            permission_array = convert_permission_name_to_id(request)
            group.permissions.set(permission_array)

            if request.POST.get('Create'):
                messages.success(request, 'The group/role was created successfully.')
                return render(request, 'accounts/access_control/groups/create_group.html', {
                    'permissions': non_default_permissions,
                    'new_name': new_name
                })

            else:
                messages.success(request, 'The group/role was created successfully.')
                return redirect('accounts:list_groups')

    return render(request, 'accounts/access_control/groups/create_group.html', {
        'permissions': non_default_permissions,
        'new_name': new_name
    })


@login_required
@never_cache
def edit_group(request, group_id):
    if not request.user.has_perm("accounts.manage_groups"):
        raise PermissionDenied

    non_default_permissions = Permission.objects.all().exclude(codename__in=DEFAULT_PERMISSIONS)
    group = Group.objects.get(id=group_id)
    old_name = group.name
    new_name = old_name

    if request.method == 'POST':
        new_name = request.POST['name']

        if not new_name:
            messages.error(request, 'Please enter a group/role name.')

        elif Group.objects.exclude(name=old_name).filter(name=new_name).exists():
            messages.error(request, 'Another group/role with the same name exists.')

        else:
            permission_array = convert_permission_name_to_id(request)

            if set(group.permissions.values_list("id", flat=True)) == set(permission_array) and new_name == old_name:
                messages.error(
                    request,
                    f"The group/role name was not edited successfully: No edits made on this group/role. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of groups/roles."
                )
                return render(request, 'accounts/access_control/groups/edit_group.html', {
                    'permissions': non_default_permissions,
                    'new_name': new_name,
                    'group': group
                })

            group.name = new_name
            group.save()

            group.permissions.clear()
            group.permissions.set(permission_array)

            messages.success(request, 'The group/role was edited successfully.')
            return redirect('accounts:list_groups')

    return render(request, 'accounts/access_control/groups/edit_group.html', {
        'permissions': non_default_permissions,
        'new_name': new_name,
        'group': group
    })


@login_required
def flag_user(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

    can_edit_flag = (
            user_staff.has_perm("accounts.flag_patients") and not user_patient.is_staff
            or user_staff.has_perm(
        "accounts.flag_assigned") and user_patient in user_staff.staff.get_assigned_patient_users()
    )

    if not can_edit_flag:
        raise PermissionDenied

    flag = user_staff.staffs_created_flags.filter(patient=user_patient)

    if flag:
        flag = flag.get()
        flag.is_active = True
        flag.save()
    else:
        flag = Flag(staff=user_staff, patient=user_patient, is_active=True)
        flag.save()

    # POST request is made when the doctor clicks to flag during viewing a report
    if request.method == "POST":
        # Ensure this was an ajax call
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'is_flagged': f'{flag.is_active}'})

    return redirect("accounts:profile", user_id)


@login_required
def unflag_user(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

    can_edit_flag = (
            user_staff.has_perm("accounts.flag_patients") and not user_patient.is_staff
            or user_staff.has_perm(
        "accounts.flag_assigned") and user_patient in user_staff.staff.get_assigned_patient_users()
    )

    if not can_edit_flag:
        raise PermissionDenied

    flag = user_staff.staffs_created_flags.filter(patient=user_patient)

    if flag:
        flag = flag.get()
        flag.is_active = False
        flag.save()

    # POST request is made when the doctor clicks to flag during viewing a report
    if request.method == "POST":
        # Ensure this was an ajax call
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'is_flagged': f'{flag.is_active}'})

    return redirect("accounts:profile", user_id)


# this function simply renders the Edit status page
# the status can be changed here
@login_required
@never_cache
def edit_case(request, user_id):
    user = User.objects.get(id=user_id)
    patient = user.patient
    if request.method == "POST":
        case_form = EditCaseForm(request.POST)
        if case_form.is_valid():
            is_confirmed_not_changed = patient.is_confirmed == (case_form.cleaned_data['is_confirmed'] == 'True')
            is_negative_not_changed = patient.is_negative == (case_form.cleaned_data['is_negative'] == 'True')
            is_quarantining_not_changed = patient.is_quarantining == (case_form.cleaned_data['is_quarantining'] == 'True')
            if is_confirmed_not_changed and is_negative_not_changed and is_quarantining_not_changed:
                messages.error(
                    request,
                    "This patient's case data was not edited successfully: No edits made on this patient's case data. If you wish to make no changes, please click the \"Cancel\" button to go back to this patient's profile page."
                )
                return render(request, 'accounts/edit_case.html', {
                    "usr": user,
                    "case_form": case_form
                })

            is_confirmed = case_form.cleaned_data.get("is_confirmed")
            is_negative = case_form.cleaned_data.get("is_negative")
            is_quarantining = case_form.cleaned_data.get("is_quarantining")

            patient.is_confirmed = is_confirmed
            patient.is_negative = is_negative
            patient.is_quarantining = is_quarantining

            patient.save()
            messages.success(
                request,
                "This patient's case data was edited successfully."
            )
            return redirect("accounts:profile", user.id)
        else:
            # No Error expected here, but we have an error message in case something else goes wrong
            messages.error(
                request,
                "This patient's case data was not edited successfully: The form is invalid. Please verify the form's data and try again."
            )
    else:
        old_case_info = dict()
        old_case_info["is_confirmed"] = patient.is_confirmed
        old_case_info["is_negative"] = patient.is_negative
        old_case_info["is_quarantining"] = patient.is_quarantining

        case_form = EditCaseForm(old_case_info)

    return render(request, 'accounts/edit_case.html', {
        "usr": user,
        "case_form": case_form
    })


def doctor_patient_list(request):
    if not request.user.has_perm("accounts.edit_assigned_doctor"):
        raise PermissionDenied

    return render(request, 'accounts/doctors.html')


def doctor_patient_list_table(request):
    # TODO FILTER FOR DOCTORS ONLY (Currently anyone in accounts_staff is treated as a doctor for the query)
    if not request.user.has_perm("accounts.edit_assigned_doctor"):
        raise PermissionDenied

    # Raw query to get each doctor and their patient count
    query = Staff.objects.raw(
        "SELECT `auth_user`.`id`, `auth_user`.`first_name`, `auth_user`.`last_name`, `accounts_staff`.`user_id`, COUNT(*) AS patient_count FROM `accounts_staff` JOIN `accounts_patient` ON (`accounts_staff`.`id` = `accounts_patient`.`assigned_staff_id`) LEFT OUTER JOIN `auth_user` ON (`accounts_staff`.`user_id` = `auth_user`.`id`) GROUP BY `accounts_patient`.`assigned_staff_id` ORDER BY `auth_user`.`first_name` , `auth_user`.`last_name`")

    # Build the JSON from the raw query
    table_info = []
    for i in query:
        record = {"user_id": i.user_id, "first_name": i.first_name, "last_name": i.last_name,
                  "patient_count": i.patient_count}
        table_info.append(record)

    # Serialize it
    serialized_reports = json.dumps({'data': table_info}, indent=4)

    return HttpResponse(serialized_reports, content_type='application/json')


def get_distance_from_postal_code_to_current_location(request, postal_code, current_lat, current_long):
    """
    Computes and returns the distance between a specified postal code and a user's specified location.
    The postal code must be a valid Canadian postal code, and the specified location is in latitude and longitude.
    @param request: Request object of the user
    @param postal_code: The "destination" postal code to search against
    @param current_lat: The current latitude of the user
    @param current_long: The current longitude of the user
    @return: HttpResponse containing the computed distance
    """

    c = connection.cursor()
    c.execute('SELECT * from postal_codes where POSTAL_CODE = %s', [postal_code])
    r = dictfetchall(c)
    patient_postal_code_lat_long = (float(r[0]['LATITUDE']), float(r[0]['LONGITUDE']))
    distance_patient_to_doctor = distance.distance(patient_postal_code_lat_long, (current_lat, current_long)).m
    if distance_patient_to_doctor > 1000:
        array = []
        if request.user.profile.violation is not None:
            array = list(json.loads(request.user.profile.violation))
        array.append({
            'type': 'quarantine non-compliance',
            'date-time': datetime.datetime.now()
        })
        request.user.profile.violation = json.dumps(array, indent=4, sort_keys=True, default=str)
        request.user.profile.save()

    return HttpResponse(distance_patient_to_doctor)
