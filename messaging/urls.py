from django.urls import path

from . import views

app_name = 'messaging'
urlpatterns = [
    path('', views.index, name='index'),
    path('composeMessage/', views.composeMessage, name='composeMessage'),
]