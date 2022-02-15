from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.db.models import Q
from messaging.models import MessageGroup, MessageContent


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
def view_message(request, message_group_id):
    current_user = request.user
    # Filters for the queries to check if user is authorized to view the messages with a specific message_group_id
    filter1 = Q(id=message_group_id)
    filter2 = Q(author_id=current_user.id) | Q(recipient_id=current_user.id)
    message_group = MessageGroup.objects.filter(filter1 & filter2).get()

    if message_group:
        messages = MessageContent.objects.filter(message_id=message_group_id)

        return render(request, 'messaging/view_message.html', {
            'message_group': message_group,
            'messages': messages
        })
    # User is not authorized to view this message group
    else:
        return redirect('messaging:list_messages')


@login_required
@never_cache
def compose_message(request):
    return render(request, 'messaging/compose_message.html')
