from django.urls import path
from . import views

app_name = 'status'
urlpatterns = [
    path('', views.index, name='index'),
    path('patient-reports/', views.patient_reports, name='patient-reports'),
    path('patient-reports/patient-report-modal/<int:user_id>/<str:date_updated>/', views.patient_report_modal, name='patient-report-modal'),
    #<int:user_id>/<str:date_updated>/
]
