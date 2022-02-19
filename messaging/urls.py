from django.urls import path

from . import views

app_name = 'messaging'
urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.list_messages, name='list_messages'),
    path('compose/', views.compose_message, name='compose_message'),
    path('view/<int:message_group_id>/', views.view_message, name='view_message'),
    path('toggle_read/<int:message_group_id>/', views.toggle_read, name='toggle_read'),
]