from django.urls import path

from . import views

app_name = 'symptoms'
urlpatterns = [
    path('list/', views.list_symptoms, name='list'),
    path('create/', views.create, name='create'),
    path('assign/user_id/', views.assign, name='assign'),
]