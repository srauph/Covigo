from django.urls import path
from . import views

app_name = 'appointments'
urlpatterns = [
    path('', views.index, name='index'),
    path('add_availabilities/', views.add_availabilities, name='add_availabilities'),
]