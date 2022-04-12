from django.urls import path
from . import views

app_name = 'symptoms'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_symptoms, name='list_symptoms'),
    path('list_table/', views.list_symptoms_table, name='list_symptoms_table'),
    path('create/', views.create_symptom, name='create_symptom'),
    path('edit/<int:symptom_id>/', views.edit_symptom, name='edit_symptom'),
    path('assign/<int:user_id>/', views.assign_symptom, name='assign_symptom'),
    path('toggle/<int:symptom_id>/', views.toggle_symptom, name='toggle_symptom'),
]