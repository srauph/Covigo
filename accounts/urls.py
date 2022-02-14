from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_users, name='list_users'),
    path('access_control/group/add', views.add_group, name='add_group'),
    path('access_control/group/list', views.list_group, name='list_group'),
    path('access_control/group/edit/<int:group_id>', views.edit_group, name='edit_group'),
    path('flag/<int:user_id>/', views.flaguser, name='flag_user'),
    path('unflag/<int:user_id>/', views.unflaguser, name='unflag_user'),
]