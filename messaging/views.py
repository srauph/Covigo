from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def index(request):
    return render(request, 'messaging/index.html')


@login_required
@never_cache
def view_message(request):
    return render(request, 'messaging/view_message.html')


@login_required
@never_cache
def compose_message(request):
    return render(request, 'messaging/compose_message.html')

