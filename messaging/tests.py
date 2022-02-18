from django.contrib.auth.models import User
from django.test import TestCase, Client

from messaging.models import MessageGroup, MessageContent


class MessagingTests(TestCase):

    def setUp(self):
        user_1 = User.objects.create(id=1, username="bob", is_staff=True)
        user_1.set_password('secret')
        user_1.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')
        doctor_1 = User.objects.create(id=2, username="doctor_1", is_staff=True)
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
