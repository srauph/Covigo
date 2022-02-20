from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import User
from django.db.models import Q
from messaging.models import MessageGroup
from messaging.models import MessageContent
from messaging.forms import CreateMessageForm


@login_required
@never_cache
def index(request):
    return redirect('messaging:list_messages')


@login_required
@never_cache
def list_messages(request, user_id=''):
    # TODO: access control for messages
    current_user = request.user

    if user_id == '':
        filter1 = Q(author_id=current_user.id) | Q(recipient_id=current_user.id)
    else:
        filter1 = Q(author_id=user_id) | Q(recipient_id=user_id)

    message_group = MessageGroup.objects.filter(filter1).all()

    return render(request, 'messaging/list_messages.html', {
        'message_group': message_group,
    })


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

    initial_data = {
        'recipient': "TEST"
    }

    if request.method == 'POST':
        create_message_form = CreateMessageForm(request.POST, initial=initial_data)

    else:
        create_message_form = CreateMessageForm(initial=initial_data)

    return render(request, 'messaging/compose_message.html', {
        'form': create_message_form
    })


@login_required
@never_cache
def toggle_read(request, message_group_id):
    msg_group = MessageGroup.objects.get(id=message_group_id)

    msg_group.seen = not msg_group.seen
    msg_group.save()
    return redirect('messaging:list_messages')
