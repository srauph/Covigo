import json
import re

from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.db.models import Q
from messaging.models import MessageGroup, MessageContent
from messaging.forms import ReplyForm, CreateMessageContentForm, CreateMessageGroupForm
from messaging.utils import send_notification


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
        filter1 = (Q(author_id=current_user.id) | Q(recipient_id=current_user.id)) & Q(type=0)
    else:
        filter1 = (Q(author_id=user_id) | Q(recipient_id=user_id)) & Q(type=0)

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
    filter3 = Q(type=0)
    if MessageGroup.objects.filter(filter1 & filter2 & filter3):

        message_group = MessageGroup.objects.filter(filter1 & filter2 & filter3).get()

        messages = MessageContent.objects.filter(message_id=message_group_id)

        # Check if we are author or recipient
        if message_group.author.id == current_user.id:
            message_group.author_seen = True
        elif message_group.recipient.id == current_user.id:
            message_group.recipient_seen = True
        else:
            # TODO: Proper exception handling
            raise Exception("Logged in user is neither author nor recipient")
        message_group.save()

        # If user sent a reply
        if request.method == 'POST':
            reply_form = ReplyForm(request.POST)

            if reply_form.is_valid():
                # Add attributes before saving to db since they're not fields in the form class
                new_reply = reply_form.save(commit=False)
                new_reply.message = message_group
                new_reply.author = current_user
                # Save to db
                new_reply.save()


                # Send notification
                if message_group.author.id == current_user.id:
                    href = reverse('messaging:view_message', args=[message_group.id])
                    send_notification(message_group.author.id, message_group.recipient.id,
                                      "New message from " + message_group.author.first_name + " " + message_group.author.last_name,
                                      href=href)

                elif message_group.recipient.id == current_user.id:
                    href = reverse('messaging:view_message', args=[message_group.id])
                    send_notification(message_group.recipient.id, message_group.author.id,
                                      "New message from " + message_group.recipient.first_name + " " + message_group.recipient.last_name,
                                      href=href)

                # Reset the form
                reply_form = ReplyForm()

                # Update the message group
                message_group.date_updated = new_reply.date_updated

                # Check if we are author or recipient
                if message_group.author.id == current_user.id:
                    message_group.recipient_seen = False
                elif message_group.recipient.id == current_user.id:
                    message_group.author_seen = False
                else:
                    # TODO: Proper exception handling
                    raise Exception("Logged in user is neither author nor recipient")
                message_group.save()

        # Initialize the reply form
        else:
            reply_form = ReplyForm()

        if message_group.author.id == current_user.id:
            seen = message_group.recipient_seen
        elif message_group.recipient.id == current_user.id:
            seen = message_group.author_seen
        else:
            # TODO: Proper exception handling
            raise Exception("Logged in user is neither author nor recipient")

        return render(request, 'messaging/view_message.html', {
            'message_group': message_group,
            'messages': messages,
            'form': reply_form,
            'seen': seen
        })
    # User is not authorized to view this message group
    else:
        return redirect('messaging:list_messages')


@login_required
@never_cache
def compose_message(request, user_id):
    # To prevent users from being able to send messages to themselves
    if request.user.id != user_id:

        recipient_user = User.objects.get(id=user_id)
        if recipient_user.first_name == "" and recipient_user.last_name == "":
            recipient_name = recipient_user
        else:
            recipient_name = f"{recipient_user.first_name} {recipient_user.last_name}"

        if request.method == 'POST':
            msg_group_form = CreateMessageGroupForm(request.POST, recipient=recipient_name)
            msg_content_form = CreateMessageContentForm(request.POST)

            if msg_group_form.is_valid() and msg_content_form.is_valid():
                new_msg_group = msg_group_form.save(commit=False)
                new_msg_group.author = request.user
                new_msg_group.recipient = recipient_user
                new_msg_group.author_seen = True
                new_msg_group.type = 0
                new_msg_group.save()
                MessageContent.objects.create(
                    author=new_msg_group.author,
                    message=new_msg_group,
                    content=msg_content_form.data.get('content'),
                )

                # Send notification
                send_notification(new_msg_group.author.id, new_msg_group.recipient.id,
                                  "New message from " + new_msg_group.author.first_name + " " + new_msg_group.author.last_name)

                return redirect("messaging:list_messages", request.user.id)

        else:
            msg_group_form = CreateMessageGroupForm(recipient=recipient_name)
            msg_content_form = CreateMessageContentForm()

        return render(request, 'messaging/compose_message.html', {
            'msg_group_form': msg_group_form,
            'msg_content_form': msg_content_form
        })
    else:
        return redirect("messaging:list_messages")


@login_required
@never_cache
def toggle_read(request, message_group_id):
    current_user = request.user
    message_group = MessageGroup.objects.get(id=message_group_id)

    # Check if we are author or recipient
    if message_group.author.id == current_user.id:
        message_group.author_seen = not message_group.author_seen
    elif message_group.recipient.id == current_user.id:
        message_group.recipient_seen = not message_group.recipient_seen
    else:
        # TODO: Proper exception handling
        raise Exception("Logged in user is neither author nor recipient")

    message_group.save()

    return redirect('messaging:list_messages')


@login_required
@never_cache
def list_notifications(request):
    current_user = request.user

    # Fetch received notifications
    filter1 = Q(recipient_id=current_user.id) & Q(type=1)

    message_group = list(MessageGroup.objects.filter(filter1).all().values())
    links = dict()


    for i in message_group:
        a = re.sub("<a href=", "", i['title'] )
        a = re.sub(">.*", "", a)

        i['title'] = re.sub("<a href=[^>]*>", "", i['title'] )
        i['title'] = re.sub("</a>", "", i['title'])

        i['link'] = a


    return render(request, 'notifications/list_notifications.html', {
        'message_group': message_group,
    })


@login_required
@never_cache
def toggle_read_notification(request, message_group_id):
    current_user = request.user
    message_group = MessageGroup.objects.get(id=message_group_id)

    # Check if we are author or recipient
    if message_group.author.id == current_user.id:
        message_group.author_seen = not message_group.author_seen
    elif message_group.recipient.id == current_user.id:
        message_group.recipient_seen = not message_group.recipient_seen
    else:
        # TODO: Proper exception handling
        raise Exception("Logged in user is neither author nor recipient")

    message_group.save()

    return redirect('/notifications')


def get_notifications(request):
    current_user = request.user

    # Fetch all unread notifications
    filter1 = Q(recipient_id=current_user.id) & Q(recipient_seen=False) & Q(type=1)

    all_notifications = list(MessageGroup.objects.filter(filter1).order_by('-date_created').all().values())

    result = {'notifications': all_notifications}

    json_result = json.dumps({'data': result}, cls=DjangoJSONEncoder, default=str)

    return HttpResponse(json_result, content_type='application/json')
