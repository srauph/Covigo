from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_users, name='list_users'),
    path('access_control/group/add', views.add_group, name='add_group'),
]