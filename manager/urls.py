from django.urls import path
from . import views

app_name = 'manager'
urlpatterns = [
    path('', views.index, name='index'),
    path('contact_tracing/', views.contact_tracing, name='contact_tracing'),
    path('case_data/', views.case_data, name='case_data'),
    path('case_data/<str:file_name>/', views.download_case_data_file, name='download_case_data_file'),
]