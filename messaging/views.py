from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.db.models import Q
from messaging.models import MessageGroup, MessageContent
from messaging.forms import ReplyForm, CreateMessageContentForm, CreateMessageGroupForm


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
    if MessageGroup.objects.filter(filter1 & filter2):

        message_group = MessageGroup.objects.filter(filter1 & filter2).get()

        messages = MessageContent.objects.filter(message_id=message_group_id)

        recipient_seen = None

        # Verify who sent the most recent message
        most_recent_message_sender_id = messages.order_by('-date_updated').first().author_id

        # If it's not the current user then they are reading an unopened message and making it "Seen".
        if most_recent_message_sender_id != current_user.id:
            message_group.seen = True
            message_group.save()
        else:
            recipient_seen = has_recipient_seen_sent_message(current_user.id, message_group.id)

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

                # Reset the form
                reply_form = ReplyForm()

                # Update the message group
                message_group.date_updated = new_reply.date_updated
                message_group.seen = False
                message_group.save()

        # Initialize the reply form
        else:
            reply_form = ReplyForm()

        return render(request, 'messaging/view_message.html', {
            'message_group': message_group,
            'messages': messages,
            'form': reply_form,
            'recipient_seen': recipient_seen
        })
    # User is not authorized to view this message group
    else:
        return redirect('messaging:list_messages')


def has_recipient_seen_sent_message(current_user_id, message_group_id):
    most_recent_message_sender_id = MessageContent.objects.filter(message_id=message_group_id).order_by(
        '-date_updated').first().author_id
    if current_user_id == most_recent_message_sender_id:
        return MessageGroup.objects.filter(id=message_group_id).get().seen
    else:
        return None


@login_required
@never_cache
def compose_message(request, user_id):
    if request.method == 'POST':
        msg_group_form = CreateMessageGroupForm(request.POST)
        msg_content_form = CreateMessageContentForm(request.POST)

        if msg_group_form.is_valid() and msg_content_form.is_valid():
            new_msg_group = msg_group_form.save(commit=False)
            new_msg_group.author = request.user
            new_msg_group.recipient = User.objects.get(id=user_id)
            new_msg_group.save()
            MessageContent.objects.create(author=new_msg_group.author,
                                          message=new_msg_group,
                                          content=msg_content_form.data.get('content'))
            return redirect("messaging:list_messages", request.user.id)

    else:
        msg_group_form = CreateMessageGroupForm()
        msg_content_form = CreateMessageContentForm()

    return render(request, 'messaging/compose_message.html', {
        'msg_group_form': msg_group_form,
        'msg_content_form': msg_content_form
    })


@login_required
@never_cache
def toggle_read(request, message_group_id):
    msg_group = MessageGroup.objects.get(id=message_group_id)

    msg_group.seen = not msg_group.seen
    msg_group.save()
    return redirect('messaging:list_messages')
