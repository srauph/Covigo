from django.urls import path
from messaging import views


urlpatterns = [
    path('', views.list_notifications, name='list_notifications'),
    path('table/', views.list_notifications_table, name='list_notifications_table'),
    path('read/<int:message_group_id>/', views.read_notification, name='read_notification'),
    path('toggle_read/<int:message_group_id>/', views.toggle_read_notification, name='toggle_read_notification'),
]
