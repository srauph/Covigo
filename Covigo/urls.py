"""Covigo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('', include('dashboard.urls')),
    path('admin/', admin.site.urls),
    path('manager/', include('manager.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('health_status/', include('health_status.urls')),
    path('appointments/', include('appointments.urls')),
    path('messaging/', include('messaging.urls')),
    path('quarantine_status/', include('quarantine_status.urls')),
    path('symptoms/', include('symptoms.urls')),
]
