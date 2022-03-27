from django.urls import path
from . import views

app_name = 'manager'
urlpatterns = [
    path('', views.index, name='index'),
    path('contact_tracing', views.contact_tracing, name='contact_tracing'),
]