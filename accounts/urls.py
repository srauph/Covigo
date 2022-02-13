from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('list/', views.user_list, name='list'),
]