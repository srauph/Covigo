from django.urls import path
from . import views

app_name = 'manager'
urlpatterns = [
    path('', views.index, name='index'),
    path('contact_tracing/', views.contact_tracing, name='contact_tracing'),
    path('contact_tracing/<str:file_name>/', views.download_contact_tracing_file, name='download_contact_tracing_file'),
    path('case_data/', views.case_data, name='case_data'),
    path('case_data/<str:file_name>/', views.download_case_data_file, name='download_case_data_file'),
    path('doctors/', views.doctor_patient_list, name='doctors'),
    path('doctors_table/', views.doctor_patient_list_table, name='doctors_table'),
    path('reassign/<int:user_id>/', views.reassign_doctor, name='reassign_doctor'),
    path('reassign_table/<int:user_id>/', views.reassign_doctor_list_table, name='reassign_doctor_list_table'),
]