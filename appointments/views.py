from django.shortcuts import render
from django.views.decorators.cache import never_cache


@never_cache
def index(request):
    return render(request, 'appointments/index.html')
