from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.contrib.auth.forms import PasswordResetForm
from accounts.forms import *
from accounts.models import Flag, Staff, Patient
from accounts.utils import get_superuser_staff_model, sendMailToUser


@login_required
@never_cache
def two_factor_authentication(request):
    return render(request, 'accounts/authentication/2FA.html')


# @never_cache
# def login(request):
#     return auth_views.LoginView.as_view(template_name='accounts/authentication/login.html')
#
#
# @never_cache
# def logout(request):
#     return auth_views.LogoutView.as_view()
#
#
# @never_cache
# def forgot_password(request):
#     return redirect(auth_views.PasswordResetView.as_view(template_name='accounts/authentication/forgot_password.html'))
#
#
# @never_cache
# def forgot_password_done(request):
#     return redirect(auth_views.PasswordResetDoneView.as_view())
#
#
# @never_cache
# def change_password(request):
#     return redirect(auth_views.PasswordChangeView.as_view(template_name='accounts/authentication/reset_password.html'))
#
#
# @never_cache
# def change_password_done(request):
#     return redirect(auth_views.PasswordChangeDoneView.as_view())
#
#
# @never_cache
# def reset_password(request):
#     return redirect(auth_views.PasswordResetConfirmView.as_view(template_name='accounts/authentication/reset_password.html'))
#
#
# @never_cache
# def reset_password_done(request):
#     return redirect(auth_views.PasswordResetCompleteView.as_view())

@never_cache
def reset_password_request(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "main/password/password_reset_email.txt"
                    c = {
                        "email": user.email,
                        'domain': '127.0.0.1:8000',
                        'site_name': 'Website',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                    }
                    email = render_to_string(email_template_name, c)
                    sendMailToUser(user, subject, email)
                    return redirect("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="main/password/password_reset.html", context={"password_reset_form": password_reset_form})


@login_required
@never_cache
def index(request):
    return redirect('accounts:list_users')


def profile(request):
    return render(request, 'accounts/profile.html')


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
                Patient.objects.create(user=new_user, staff=get_superuser_staff_model())

            subject = "Welcome to Covigo!"
            message = "Love, Shahd - Mo - Amir - Nizar - Shu - Avg - Isaac - Justin - Aseel"

            if has_email:
                sendMailToUser(new_user, subject, message)

            return redirect("accounts:list_users")

        else:
            if not (has_email or has_phone):
                user_form.add_error(None, "Please enter an email address or a phone number.")
            # pass  # TODO figure out what actually goes here. im 99% sure an error msg should be passed to template here

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
            # pass  # TODO figure out what actually goes here. im 99% sure an error msg should be passed to template here

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
    
    return redirect("accounts:list_users")


@login_required
@never_cache
def edit_group(request, group_id):
    group = Group.objects.filter(id=group_id).get()

    if request.method == "POST":
        group.name = request.POST['name']
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
