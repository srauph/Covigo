from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('', views.index, name='index'),
    path('covigo_case_data/', views.covigo_case_data_graphs, name='covigo_case_data'),
    path('external_case_data/', views.external_case_data_graphs, name='external_case_data'),
]
