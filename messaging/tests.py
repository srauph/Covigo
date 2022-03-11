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

    def test_view_message_page_success(self):
        """
        Checks if currently logged-in user can view their authorized messages
        @return:
        """
        # Arrange & Act
        response = self.client.get('/messaging/view/1/')

        # Assert
        self.assertTemplateUsed(response, 'messaging/view_message.html')

    def test_view_message_page_failure(self):
        """
        Checks if currently logged-in user CANNOT view unauthorized message
        @return:
        """

        # Arrange & Act
        response = self.client.get('/messaging/view/150/')

        # Assert
        self.assertTemplateNotUsed(response, 'messaging/view_message.html')

    def test_reply_message(self):
        """
        Checks if user can reply to a message
        @return:
        """

        # Arrange & Act
        self.client.post('/messaging/view/1/', {
            'content': 'Another message reply!!!'
        })

        # Assert
        self.assertEqual(MessageContent.objects.get(id=3).content, 'Another message reply!!!')

    def test_seen_recipient(self):
        """
        Check if seen status becomes true when recipient opens message
        @return:
        """

        # Arrange
        # Get the current logged-in user (self)
        user_1 = User.objects.get(id=1)

        # Get message group
        msg_group_1 = MessageGroup.objects.get(id=1)

        # Act
        # Send a message to doctor_1
        MessageContent.objects.create(message=msg_group_1, author=user_1,
                                      content="I have a fever of 100 degrees")

        # Assert
        # Check if doctor has seen the new message
        self.assertFalse(msg_group_1.recipient_seen)

        # Arrange
        # Login as doctor_1
        doctor_client = Client()
        doctor_client.login(username='doctor_1', password='secret')

        # Act
        # Make doctor_1 open the message
        doctor_client.get('/messaging/view/1/')

        # Check if doctor has seen the new message
        msg_group_1.refresh_from_db()

        # Assert
        self.assertTrue(msg_group_1.recipient_seen)


class MessagingListTests(TestCase):

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

    def test_open_messages_list(self):
        """
        Check if currently logged-in user can access their message list with id
        @return:
        """
        # Arrange & Act
        response = self.client.get('/messaging/list/1')

        # Assert
        self.assertTemplateUsed(response, 'messaging/list_messages.html')

    def test_toggle_read(self):
        # Arrange & Act
        # Toggle the seen status to be True
        toggle_read(self.request, 1)
        msg_group_1 = MessageGroup.objects.get(id=1)

        # Assert
        self.assertTrue(msg_group_1.author_seen)

        # Act again
        # Toggle it again to be False
        toggle_read(self.request, 1)
        msg_group_1.refresh_from_db()

        # Assert again
        self.assertFalse(msg_group_1.author_seen)

        # Act again
        # Toggle it again to be True
        toggle_read(self.request, 1)
        msg_group_1.refresh_from_db()

        # Assert again
        self.assertTrue(msg_group_1.author_seen)


class MessagingComposeTest(TestCase):

    def setUp(self):
        user_1 = User.objects.create(id=1, username="bob", is_staff=True)
        user_1.set_password('secret')
        user_1.save()

        self.client = Client()
        self.client.login(username='bob', password='secret')

        doctor_1 = User.objects.create(id=2, username="doctor_1", is_staff=True)
        doctor_1.set_password('secret')
        doctor_1.save()

    def test_user_cannot_message_self(self):
        """
        Test to check if user cannot send message to themselves
        @return:
        """

        # Arrange & Act
        # User tries to message self by entering their id in the url
        response = self.client.get('/messaging/compose/1')

        # Assert
        # User is redirected to the messages list
        self.assertRedirects(response, '/messaging/list/')

    def test_create_message_group(self):
        """
        Test to compose a new message
        @return:
        """

        # Arrange
        message_group_data = {'title': 'Question about fever',
                              'priority': '0',
                              'content': 'Please help me with my fever'}

        # Act
        # Submit the form
        response = self.client.post('/messaging/compose/2', message_group_data)

        # Fetch the newly created MessageGroup object after submitting form
        msg_group = MessageGroup.objects.filter(title='Question about fever').first()

        # Assert
        self.assertEqual(msg_group.title, 'Question about fever')

        # Check redirect
        self.assertRedirects(response, '/messaging/list/1')
