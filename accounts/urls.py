from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_users, name='list_users'),
    path('flag/<int:user_id>/', views.flaguser, name='flag_user'),
    path('unflag/<int:user_id>/', views.unflaguser, name='unflag_user'),
]