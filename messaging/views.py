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
def view_message(request, message_group_id=3):
    current_user_id = request.user.id
    # Where conditions for the queries to check if user is authorized to view the messages with a specific
    # message_group_id
    where1 = Q(id=message_group_id)
    where2 = Q(author_id=current_user_id) | Q(recipient_id=current_user_id)
    message_group = MessageGroup.objects.filter(where1 & where2).first()

    if message_group:

        messages = MessageContent.objects.filter(message_id=message_group_id)

        # Identify the sender (current user) and receiver
        # This is needed to get the Users names and decide the color of message boxes
        sender = request.user
        if message_group.author_id == current_user_id:
            receiver = User.objects.get(id=message_group.recipient_id)
        else:
            receiver = User.objects.get(id=message_group.author_id)

        return render(request, 'messaging/view_message.html', {
            'message_group': message_group,
            'messages': messages,
            'sender': sender,
            'receiver': receiver
        })
    # User is not authorized to view this message group
    else:
        return redirect('messaging:list_messages')


@login_required
@never_cache
def compose_message(request):
    return render(request, 'messaging/compose_message.html')
