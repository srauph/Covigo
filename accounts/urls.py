from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_users, name='list_users'),
    path('create/', views.create_user, name='create_user'),
    path('access_control/group/add', views.add_group, name='add_group'),
    path('access_control/group/list', views.list_group, name='list_group'),
    path('access_control/group/edit/<int:group_id>', views.edit_group, name='edit_group'),
    path('flag/<int:user_id>/', views.flaguser, name='flag_user'),
    path('unflag/<int:user_id>/', views.unflaguser, name='unflag_user'),
    path('two_factor_authentication/', views.two_factor_authentication, name='two_factor_authentication'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/', views.reset_password, name='reset_password'),
    path('profile/', views.profile, name='profile'),
]