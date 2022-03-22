from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import MultipleObjectsReturned
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache

from accounts.forms import *
from accounts.models import Flag, Staff, Patient
from accounts.utils import get_superuser_staff_model, send_email_to_user, send_sms_to_user, reset_password_email_generator, get_or_generate_patient_profile_qr
from accounts.utils import (
    send_email_to_user,
    reset_password_email_generator,
    get_or_generate_patient_profile_qr
)
from symptoms.utils import is_symptom_editing_allowed


class GroupErrors:
    def __init__(self):
        self.blank_name = False
        self.duplicate_name = False

    def has_errors(self):
        return self.blank_name or self.duplicate_name


def unauthorized(request):
    return HttpResponse('Unauthorized', status=401)

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
                subject = "Password Reset Requested"
                template = "accounts/authentication/reset_password_email.txt"
                reset_password_email_generator(user, subject, template)
                return redirect("accounts:forgot_password_done")
            except MultipleObjectsReturned:
                password_reset_form.add_error(None,
                                              "More than one user with the given email address could be found. Please contact the system administrators to fix this issue.")
            except User.DoesNotExist:
                password_reset_form.add_error(None, "No user with the given email address could be found.")
        else:
            password_reset_form.add_error(None, "Please enter a valid email address or phone number.")
    else:
        password_reset_form = PasswordResetForm()
    return render(
        request=request,
        template_name="accounts/authentication/forgot_password.html",
        context={"form": password_reset_form}
    )


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')


@login_required
@never_cache
def profile(request, user_id):
    user = User.objects.get(id=user_id)
    image = get_or_generate_patient_profile_qr(user_id)
    all_doctors = User.objects.filter(groups__name='doctor')

    if request.method == "POST":
        doctor_staff_id = request.POST.get('doctor_id')
        user.patient.assigned_staff_id = doctor_staff_id
        user.save()
    return render(request, 'accounts/profile.html',
                  {"qr": image,
                   "usr": user,
                   "all_doctors": all_doctors,
                   "full_view": True,
                   "allow_editing": is_symptom_editing_allowed(user_id)})


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
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)

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
                new_user.username = user_phone

            new_user.save()
            new_user.profile.phone_number = user_phone
            # TODO: Discuss the possibility of having no group and remove `if` if we enforce having at least one
            if user_groups:
                new_user.groups.set(user_groups)
            new_user.save()

            if new_user.is_staff:
                Staff.objects.create(user=new_user)
            elif not new_user.is_staff:
                # Since Patient *requires* an assigned staff, set it to the superuser for now.
                # TODO: discuss if we should keep this behaviour for now or make Patient.staff nullable instead.
                Patient.objects.create(user=new_user)

            subject = "Welcome to Covigo!"
            message = "Love, Shahd - Mo - Amir - Nizar - Shu - Avg - Isaac - Justin - Aseel"

            if has_email:
                send_email_to_user(new_user, subject, message)

            elif has_phone:
                send_sms_to_user(new_user, user_phone, message)

            else:
                None

            return redirect("accounts:list_users")

        else:
            if not (has_email or has_phone):
                user_form.add_error(None, "Please enter an email address or a phone number.")
    # Create forms
    else:
        user_form = UserForm()
        profile_form = ProfileForm()

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

        user_email = user_form.data.get("email")
        user_phone = profile_form.data.get("phone_number")
        user_groups = user_form.data.get("groups")
        has_email = user_email != ""
        has_phone = user_phone != ""

        if user_form.is_valid() and profile_form.is_valid() and (has_email or has_phone):

            edited_user = user_form.save(commit=False)

            # TODO: Discuss the possibility of having no group and remove `if` if we enforce having at least one
            if user_groups:
                edited_user.groups.set(user_groups)

            edited_user.save()
            profile_form.save()

            return redirect("accounts:list_users")

        else:
            if not (has_email or has_phone):
                user_form.add_error(None, "Please enter an email address or a phone number.")

    # Create forms
    else:
        user_form = EditUserForm(instance=user, user_id=user_id)
        profile_form = EditProfileForm(instance=user.profile, user_id=user_id)

    return render(request, "accounts/edit_user.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })


@login_required
@never_cache
def list_group(request):
    return render(request, 'accounts/access_control/group/list_group.html', {
        'groups': Group.objects.all()
    })


@login_required
@never_cache
def create_group(request):
    new_name = ''
    errors = GroupErrors()

    if request.method == 'POST':
        new_name = request.POST['name']

        if not new_name:
            errors.blank_name = True

        elif Group.objects.filter(name=new_name).exists():
            errors.duplicate_name = True

        else:
            group = Group(name=new_name)
            group.save()

            permission_array = convert_permission_name_to_id(request)
            group.permissions.set(permission_array)

            return redirect('accounts:list_group')

    return render(request, 'accounts/access_control/group/add_group.html', {
        'permissions': Permission.objects.all(),
        'new_name': new_name,
        'errors': errors,
    })


@login_required
@never_cache
def edit_group(request, group_id):
    group = Group.objects.get(id=group_id)
    old_name = group.name
    new_name = old_name
    errors = GroupErrors()

    if request.method == 'POST':
        new_name = request.POST['name']

        if not new_name:
            errors.blank_name = True

        elif Group.objects.exclude(name=old_name).filter(name=new_name).exists():
            errors.duplicate_name = True

        else:
            group.name = new_name
            group.save()

            permission_array = convert_permission_name_to_id(request)
            group.permissions.clear()
            group.permissions.set(permission_array)

            return redirect('accounts:list_group')

    return render(request, 'accounts/access_control/group/edit_group.html', {
        'permissions': Permission.objects.all(),
        'new_name': new_name,
        'errors': errors,
        'group': group
    })


@login_required
def flaguser(request, user_id):
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
def unflaguser(request, user_id):
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


def convert_permission_name_to_id(request):
    permission_array = []
    for perm in request.POST.getlist('perms'):
        permission_id = Permission.objects.filter(codename=perm).get().id
        permission_array.append(permission_id)
    return permission_array
