from django.urls import path
from . import views

app_name = 'status'
urlpatterns = [
    path('', views.index, name='index'),
    path('patient-reports/', views.patient_reports, name='patient-reports')
]