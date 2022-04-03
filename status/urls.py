from django.urls import path
from . import views

app_name = 'status'
urlpatterns = [
    path('', views.index, name='index'),
    path('patient_reports/', views.patient_reports, name='patient_reports'),
    path('patient_reports_table/', views.patient_reports_table, name='patient_reports_table'),
    path(
        'patient_reports/patient_report_modal/<int:user_id>/<str:date_updated>/',
        views.patient_report_modal,
        name='patient_report_modal'
    ),
    path(
        'patient_reports/patient_report_modal_table/<int:user_id>/<str:date_updated>/',
        views.patient_reports_modal_table,
        name='patient_report_modal_table'
    ),
    path('create_status_report/', views.create_patient_report, name='create_status_report'),
    path('edit_status_report/', views.edit_patient_report, name='edit_status_report'),
    path('resubmit_request/<int:patient_symptom_id>', views.resubmit_request, name='resubmit_request'),
    path('test_results/<int:user_id>/', views.test_result, name='test_results'),
    path('test_results_table/<int:user_id>/', views.test_results_table, name='test_results_table'),
    path('test_report/<int:user_id>/', views.test_report, name='test_report')
]
