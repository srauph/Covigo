from django.urls import path
from . import views

app_name = 'status'
urlpatterns = [
    path('', views.index, name='index'),
    path('patient-reports/', views.patient_reports, name='patient-reports'),
    path('patient-reports-table/', views.patient_reports_table, name='patient-reports-table'),
    path('patient-reports/patient-report-modal/<int:user_id>/<str:date_updated>/', views.patient_report_modal,
         name='patient-report-modal'),
    path('create-status-report/', views.create_status_report, name='create-status-report'),
    path('edit-status-report/', views.edit_status_report, name='edit-status-report'),
]
