from django.shortcuts import render


def index(request):
    return render(request, 'quarantine_status/index.html')
