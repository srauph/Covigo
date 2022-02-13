from django.urls import path

from . import views

app_name = 'messaging'
urlpatterns = [
    path('', views.index, name='index'),
    path('view/userId/', views.view_message, name='view_message'),
    path('compose_message/', views.compose_message, name='compose_message'),

]