from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetConfirmView
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache

from accounts.forms import *
from accounts.models import Flag, Staff, Patient
from accounts.utils import (
    get_superuser_staff_model,
    generate_and_send_email,
    generate_profile_qr,
    get_user_from_uidb64
)


class RegisterPasswordResetConfirmView(PasswordResetConfirmView):
    def dispatch(self, *args, **kwargs):
        self.success_url = reverse_lazy('accounts:register_user_password_done', kwargs={'uidb64': kwargs['uidb64']})
        return super(RegisterPasswordResetConfirmView, self).dispatch(*args, **kwargs)


def process_register_or_edit_user_form(request, user_form, profile_form, mode=None):
    user_email = user_form.data.get("email")
    user_phone = profile_form.data.get("phone_number")
    user_groups = user_form.data.get("groups")
    has_email = user_email != ""
    has_phone = user_phone != ""

    if user_form.is_valid() and profile_form.is_valid() and (has_email or has_phone):

        edited_user = user_form.save(commit=False)

        # TODO: Discuss possibility of having no group and adjust `if` to enforce at least one when editing
        if user_groups:
            edited_user.groups.set(user_groups)

        edited_user.save()
        profile_form.save()

        return True

    else:
        if mode == "Edit" and not (has_email or has_phone):
            user_form.add_error(None, "Please enter an email address or a phone number.")
        return False


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
                subject = "Covigo - Password Reset Requested"
                template = "accounts/authentication/txt/reset_password_email.txt"
                generate_and_send_email(user, subject, template)
                return redirect("accounts:forgot_password_done")
            except MultipleObjectsReturned:
                password_reset_form.add_error(None, "More than one user with the given email address could be found. Please contact the system administrators to fix this issue.")
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


@never_cache
def register_user(request, uidb64, token):
    return redirect('accounts:register_user_password', uidb64=uidb64, token=token)


def register_user_password_done(request, uidb64):
    user = get_user_from_uidb64(uidb64)
    token = default_token_generator.make_token(user)
    return redirect('accounts:register_user_details', uidb64, token)

@never_cache
def register_user_details(request, uidb64, token):
    INTERNAL_SET_DETAILS_SESSION_TOKEN = "_set_details_token"
    user = get_user_from_uidb64(uidb64)
    user_id = user.id
    valid = False

    if user is not None:
        if token == 'set-details':
            session_token = request.session.get(INTERNAL_SET_DETAILS_SESSION_TOKEN)
            if default_token_generator.check_token(user, session_token):
                # If the token is valid, display the password reset form.
                valid = True
        else:
            if default_token_generator.check_token(user, token):
                # Store the token in the session and redirect to the
                # password reset form at a URL without the token. That
                # avoids the possibility of leaking the token in the
                # HTTP Referer header.
                request.session[INTERNAL_SET_DETAILS_SESSION_TOKEN] = token
                redirect_url = request.path.replace(token, 'set-details')
                return redirect(redirect_url, uidb64, token)

    # Process/Create forms if the link is valid
    if valid:
        # Process forms
        if request.method == "POST":
            user_form = RegisterUserForm(request.POST, instance=user, user_id=user_id)
            profile_form = RegisterProfileForm(request.POST, instance=user.profile, user_id=user_id)

            if process_register_or_edit_user_form(request, user_form, profile_form):
                request.session[INTERNAL_SET_DETAILS_SESSION_TOKEN] = None
                return redirect("accounts:register_user_done")

        # Create forms
        else:
            user_form = RegisterUserForm(instance=user, user_id=user_id, initial={"username": None})
            profile_form = RegisterProfileForm(instance=user.profile, user_id=user_id)

        return render(request, "accounts/register_user_details.html", {
            "user_form": user_form,
            "profile_form": profile_form,
            "validlink": True
        })

    # Don't process/create forms if the link is expired or invalid
    else:
        return render(request, "accounts/register_user_details.html", {
            "validlink": False
        })


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')


@login_required
@never_cache
def profile(request, user_id):
    user = User.objects.get(id = user_id)
    image = generate_profile_qr(user_id)
    return render(request, 'accounts/profile.html', {"qr": image, "usr": user, "full_view": True})


@never_cache
def profile_from_code(request, code):
    patient = Patient.objects.get(code = code)
    user = User.objects.get(patient = patient)
    image = generate_profile_qr(user.id)
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
                Patient.objects.create(user=new_user, staff=get_superuser_staff_model())

            if has_email:
                subject = "Covigo - Account Registration"
                template = "accounts/authentication/txt/register_user_email.txt"
                generate_and_send_email(new_user, subject, template)

            return redirect("accounts:list_users")

        else:
            if not (has_email or has_phone):
                user_form.add_error(None, "Please enter an email address or a phone number.")
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
            return redirect("accounts:list_users")

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
def add_group(request):
    if request.method == 'POST':

        group = Group(name=request.POST['name'])
        group.save()
        permission_array = convert_permission_name_to_id(request)

        group.permissions.set(permission_array)

        return redirect('accounts:list_group')

    else:
        return render(request, 'accounts/access_control/group/add_group.html', {
            'permissions': Permission.objects.all()
        })


@login_required
@never_cache
def list_group(request):
    return render(request, 'accounts/access_control/group/list_group.html', {
        'groups': Group.objects.all()
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
    
    return redirect("accounts:list_users")


@login_required
@never_cache
def edit_group(request, group_id):
    group = Group.objects.filter(id=group_id).get()

    if request.method == "POST":
        group.symptom_name = request.POST['name']
        group.save()
        permission_array = convert_permission_name_to_id(request)
        group.permissions.clear()
        group.permissions.set(permission_array)

        return redirect('accounts:list_group')
    else:
        return render(request, 'accounts/access_control/group/edit_group.html', {
            'permissions': Permission.objects.all(),
            'group': group
        })


def convert_permission_name_to_id(request):
    permission_array = []
    for perm in request.POST.getlist('perms'):
        permission_id = Permission.objects.filter(codename=perm).get().id
        permission_array.append(permission_id)
    return permission_array
