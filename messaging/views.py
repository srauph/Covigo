from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


@login_required
@never_cache
def index(request):
    return redirect('messaging:list_messages')


@login_required
@never_cache
def list_messages(request):
    return render(request, 'messaging/list_messages.html')


@login_required
@never_cache
def view_message(request):
    return render(request, 'messaging/view_message.html')


@login_required
@never_cache
def compose_message(request):
    return render(request, 'messaging/compose_message.html')

