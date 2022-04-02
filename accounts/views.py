import datetime
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView, PasswordChangeView
from django.core import serializers
from django.core.exceptions import MultipleObjectsReturned
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Count
from django.forms import model_to_dict
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters

from Covigo.messages import Messages
from accounts.forms import *
from accounts.models import Flag, Staff, Patient
from accounts.preferences import SystemMessagesPreference, StatusReminderPreference
from accounts.utils import (
    convert_dict_of_bools_to_list,
    get_assigned_staff_id_by_patient_id,
    get_or_generate_patient_profile_qr,
    get_user_from_uidb64,
    return_closest_with_least_patients_doctor,
    send_system_message_to_user,
)
from appointments.models import Appointment
from appointments.utils import rebook_appointment_with_new_doctor
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


@login_required
@never_cache
def two_factor_authentication(request):
    return render(request, 'accounts/authentication/2FA.html')


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

    # messages_filter = Q(author_id=user_id) | Q(recipient_id=user_id)
    # message_group = MessageGroup.objects.filter(messages_filter).order_by('-date_updated')[:3]
    today = datetime.date.today()
    all_filter = Q(patient__isnull=False) & Q(start_date__gte=today)

    if user.is_staff:
        all_appointments = Appointment.objects.filter(staff=user).filter(all_filter).order_by("start_date")[:4]
    else:
        appointments = Appointment.objects.filter(patient=user).filter(all_filter).order_by("start_date")[:4]

    if not user.is_staff:
        if request.method == "POST":
            doctor_staff_id = request.POST.get('doctor_id')

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
        assigned_flags = Flag.objects.filter(patient=user)

        # TODO: Remove this groups name and replace with permission instead
        all_doctors = User.objects.filter(groups__name='doctor')
        # all_doctors = User.objects.filter(is_staff=True)

        return render(request, 'accounts/profile.html', {
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
        })

    else:
        appointments = Appointment.objects.filter(staff=user).filter(all_filter).order_by("start_date")
        appointments_truncated = appointments[:4]
        assigned_patients = user.staff.get_assigned_patient_users()
        issued_flags = Flag.objects.filter(staff=user)

        return render(request, 'accounts/profile.html', {
            "usr": user,
            "appointments": appointments,
            "appointments_truncated": appointments_truncated,
            "assigned_patients": assigned_patients,
            "issued_flags": issued_flags,
            "full_view": True
        })


@never_cache
def profile_from_code(request, code):
    patient = Patient.objects.get(code=code)
    user = User.objects.get(patient=patient)
    image = get_or_generate_patient_profile_qr(user.id)
    return render(request, 'accounts/profile.html', {"qr": image, "usr": user, "full_view": False})


@login_required
@never_cache
def list_users(request):
    return render(request, 'accounts/list_users.html', {
        'users': User.objects.all()
    })


@login_required
@never_cache
def create_user(request):
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
                # Since Patient *requires* an assigned staff, set it to the superuser for now.
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
        "edited_user": user
    })


@login_required
@never_cache
def edit_preferences(request, user_id):
    profile = User.objects.get(id=user_id).profile

    # Process forms
    if request.method == "POST":
        preferences_form = EditPreferencesForm(request.POST)

        if preferences_form.is_valid():
            system_msg_preferences = preferences_form.cleaned_data.get(SystemMessagesPreference.NAME.value)
            status_reminder_interval = preferences_form.cleaned_data.get(StatusReminderPreference.NAME.value)

            preferences = {
                SystemMessagesPreference.NAME.value: {
                    SystemMessagesPreference.EMAIL.value: "use_email" in system_msg_preferences,
                    SystemMessagesPreference.SMS.value: "use_sms" in system_msg_preferences
                },

                StatusReminderPreference.NAME.value: status_reminder_interval,
            }

            profile.preferences = preferences
            profile.save()

            return redirect("accounts:profile", user_id)
    # Create forms
    else:
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
    })


@login_required
@never_cache
def list_groups(request):
    return render(request, 'accounts/access_control/groups/list_groups.html', {
        'groups': Group.objects.all()
    })


@login_required
@never_cache
def create_group(request):
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
                    'permissions': Permission.objects.all(),
                    'new_name': new_name
                })

            else:
                messages.success(request, 'The group/role was created successfully.')
                return redirect('accounts:list_groups')

    return render(request, 'accounts/access_control/groups/create_group.html', {
        'permissions': Permission.objects.all(),
        'new_name': new_name
    })


@login_required
@never_cache
def edit_group(request, group_id):
    group = Group.objects.get(id=group_id)
    old_name = group.name
    new_name = old_name

    if request.method == 'POST':
        new_name = request.POST['name']

        if not new_name:
            messages.error(request, 'Please enter a group/role name.')

        elif new_name == old_name:
            messages.error(request,
                           f"The group/role name was not edited successfully: No edits made on this group/role. If you wish to make no changes, please click the \"Cancel\" button to go back to the list of groups/roles.")
            return render(request, 'accounts/access_control/groups/edit_group.html', {
                'permissions': Permission.objects.all(),
                'new_name': new_name,
                'groups': group
            })

        elif Group.objects.exclude(name=old_name).filter(name=new_name).exists():
            messages.error(request, 'Another group/role with the same name exists.')

        else:
            group.name = new_name
            group.save()

            permission_array = convert_permission_name_to_id(request)
            group.permissions.clear()
            group.permissions.set(permission_array)

            messages.success(request, 'The group/role was edited successfully.')
            return redirect('accounts:list_groups')

    return render(request, 'accounts/access_control/groups/edit_group.html', {
        'permissions': Permission.objects.all(),
        'new_name': new_name,
        'groups': group
    })


@login_required
def flag_user(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

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

    return redirect("accounts:list_users")


@login_required
def unflag_user(request, user_id):
    user_staff = request.user
    user_patient = User.objects.get(id=user_id)

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

    return redirect("accounts:list_users")


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
            if not case_form.has_changed():
                messages.error(
                    request,
                    "The patient's case data was not edited successfully: No edits made on this patient. If you wish to make no changes, please click the \"Cancel\" button to go back to the profile page."
                )
            else:
                is_confirmed = case_form.cleaned_data.get("is_confirmed")
                is_negative = case_form.cleaned_data.get("is_negative")
                is_quarantining = case_form.cleaned_data.get("is_quarantining")

                patient.is_confirmed = is_confirmed
                patient.is_negative = is_negative
                patient.is_quarantining = is_quarantining

                patient.save()
                messages.success(
                    request,
                    "The patient's case data was edited successfully."
                )
                return redirect("accounts:profile", user.id)
        else:
            # No Error expected here, but we have an error message in case something else goes wrong
            messages.error(
                request,
                "The patient's case data was not edited successfully: The form is invalid. Please verify the form's data."
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
    # I assume this is an admin only page
    if request.user.is_superuser:
        return render(request, 'accounts/doctors.html')
    raise Http404("The requested resource was not found on this server.")


def doctor_patient_list_table(request):
    # TODO FILTER FOR DOCTORS ONLY (Currently anyone in accounts_staff is treated as a doctor for the query)
    if request.user.is_superuser:
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
    raise Http404("The requested resource was not found on this server.")
