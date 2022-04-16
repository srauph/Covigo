from django.urls import path
from . import views

app_name = 'appointments'
urlpatterns = [
    path('', views.index, name='index'),
    path('add_availabilities/', views.add_availabilities, name='add_availabilities'),
    path('book_appointments/', views.book_appointments, name='book_appointments'),
    path('cancel_appointments/', views.cancel_appointments_or_delete_availabilities, name='cancel_appointments_or_delete_availabilities'),
    path('current_appointments_table/<mode>/', views.current_appointments_table, name='current_appointments_table'),
    path('session_is_locked/', views.check_session_is_locked, name='session_is_locked'),
]
