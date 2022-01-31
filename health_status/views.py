from django.shortcuts import render


def index(request):
    return render(request, 'health_status/index.html')
