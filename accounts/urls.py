from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from . import views
from .forms import ResetPasswordForm

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_users, name='list_users'),
    path('create/', views.create_user, name='create_user'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),

    path('access_control/group/add', views.add_group, name='add_group'),
    path('access_control/group/list', views.list_group, name='list_group'),
    path('access_control/group/edit/<int:group_id>', views.edit_group, name='edit_group'),

    path('flag/<int:user_id>/', views.flaguser, name='flag_user'),
    path('unflag/<int:user_id>/', views.unflaguser, name='unflag_user'),

    path('two_factor_authentication/', views.two_factor_authentication, name='two_factor_authentication'),
    path('profile/', views.profile, name='profile'),

    path(
        'login/',
        auth_views.LoginView.as_view(template_name='accounts/authentication/login.html'),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),
    path(
        'change_password/',
        auth_views.PasswordChangeView.as_view(template_name='accounts/authentication/reset_password.html'),
        name='change_password'
    ),
    path(
        'change_password/done/',
        auth_views.PasswordChangeDoneView.as_view(),
        name='change_password_done'
    ),
    path(
        'forgot_password/',
        views.forgot_password,
        name='forgot_password'
    ),
    path(
        'forgot_password/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/authentication/forgot_password_done.html'),
        name='forgot_password_done'
    ),
    path(
        'reset_password/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            form_class=ResetPasswordForm,
            template_name='accounts/authentication/reset_password.html',
            success_url=reverse_lazy('accounts:reset_password_done')
        ),
        name='reset_password'
    ),
    path(
        'reset_password/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/authentication/reset_password_done.html'),
        name='reset_password_done'
    ),
]
