from django.contrib.auth.models import User
from django.shortcuts import render


def index(request):
    user_count = User.objects.count()
    return render(request, 'manager/index.html', {"user_count": user_count})


def contact_tracing(request):
    user_count = User.objects.count()
    return render(request, 'manager/contact_tracing.html', {"user_count": user_count})
