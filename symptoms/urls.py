from django.urls import path

from . import views

app_name = 'symptoms'
urlpatterns = [
    path('list/', views.list, name='list'),
    path('create/', views.create, name='create'),
    path('userid/', views.userid, name='userid'),
]