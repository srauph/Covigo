from django.urls import path

from . import views

app_name = 'health_status'
urlpatterns = [
    path('', views.index, name='index'),
]