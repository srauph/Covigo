from django.contrib.auth.models import User
from django.test import TestCase, Client, RequestFactory

from messaging.models import MessageGroup, MessageContent
from messaging.views import toggle_read


class MessagingViewReplyTests(TestCase):

    def setUp(self):
        user_1 = User.objects.create(id=1, username="bob", is_staff=True)
        user_1.set_password('secret')
        user_1.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

        doctor_1 = User.objects.create(id=2, username="doctor_1", is_staff=True)
        doctor_1.set_password('secret')
        doctor_1.save()

        msg_group_1 = MessageGroup.objects.create(id=1, author=user_1, recipient=doctor_1,
                                                  title="Question about my fever")
        MessageContent.objects.create(message=msg_group_1, author=user_1,
                                      content="Hello doctor, I have a question about my fever")
        MessageContent.objects.create(message=msg_group_1, author=doctor_1,
                                      content="Hi Bob, what seems to be the problem?")

    # Checks if currently logged-in user can view their authorized messages
    def test_view_message_page_success(self):
        response = self.client.get('/messaging/view/1/')
        self.assertTemplateUsed(response, 'messaging/view_message.html')

    # Checks if currently logged-in user CANNOT view unauthorized messages
    def test_view_message_page_failure(self):
        response = self.client.get('/messaging/view/150/')
        self.assertTemplateNotUsed(response, 'messaging/view_message.html')

    # Checks if user can reply to a message
    def test_reply_message(self):
        self.client.post('/messaging/view/1/', {
            'content': 'Another message reply!!!'
        })
        self.assertEqual(MessageContent.objects.get(id=3).content, 'Another message reply!!!')

    # Check if seen status becomes true when recipient opens message
    def test_seen_recipient(self):

        # Get the current logged-in user (self)
        user_1 = User.objects.get(id=1)

        # Get message group
        msg_group_1 = MessageGroup.objects.get(id=1)

        # Send a message to doctor_1
        MessageContent.objects.create(message=msg_group_1, author=user_1,
                                      content="I have a fever of 100 degrees")

        # Check if doctor has seen the new message
        self.assertFalse(msg_group_1.seen)

        # Login as doctor_1
        doctor_client = Client()
        doctor_client.login(username='doctor_1', password='secret')

        # Make doctor_1 open the message
        doctor_client.get('/messaging/view/1/')
        # Check if doctor has seen the new message
        msg_group_1.refresh_from_db()
        self.assertTrue(msg_group_1.seen)

    # Check if seen status is unchanged after sender re-opens the message group after replying
    def test_seen_sender(self):
        # Get the current logged-in user (self)
        user_1 = User.objects.get(id=1)

        # Get message group
        msg_group_1 = MessageGroup.objects.get(id=1)

        # Send a message to doctor_1
        MessageContent.objects.create(message=msg_group_1, author=user_1,
                                      content="My fever is now 150 degrees bruh")

        # Check if doctor has seen the new message
        self.assertFalse(msg_group_1.seen)

        # Make current user re-open the message group
        self.client.get('/messaging/view/1/')

        # Check seen status of message
        msg_group_1.refresh_from_db()
        self.assertFalse(msg_group_1.seen)


class MessagingList(TestCase):

    def setUp(self):
        user_1 = User.objects.create(id=1, username="amir", is_staff=True)
        user_1.set_password('secret')
        user_1.save()

        self.client = Client()
        self.client.login(username='amir', password='secret')

        self.request = RequestFactory().get('/')
        self.request.user = user_1

        doctor_1 = User.objects.create(id=2, username="doctor_1", is_staff=True)

        msg_group_1 = MessageGroup.objects.create(id=1, author=user_1, recipient=doctor_1,
                                                  title="Question about my fever")

    # Check if currently logged-in user can access their message list with id
    def test_open_messages_list(self):
        response = self.client.get('/messaging/list/1')
        self.assertTemplateUsed(response, 'messaging/list_messages.html')

    def test_toggle_read(self):

        # Toggle the seen status to be True
        toggle_read(self.request, 1)
        msg_group_1 = MessageGroup.objects.get(id=1)
        self.assertTrue(msg_group_1.seen)

        # Toggle it again to be False
        toggle_read(self.request, 1)
        msg_group_1.refresh_from_db()
        self.assertFalse(msg_group_1.seen)

        # Toggle it again to be True
        toggle_read(self.request, 1)
        msg_group_1.refresh_from_db()
        self.assertTrue(msg_group_1.seen)


