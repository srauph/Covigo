from django.urls import reverse
import base64

from django.template.loader import render_to_string

from messaging.models import MessageGroup

import rsa

def send_notification(sender_id, recipient_id, notification_message, app_name=None, href=None):
    """
    Utility function to send notifications.
    Developer needs to only add one of either the app_name or the href input.
    Specify the app name if you want the user to be redirected to the index page of the app after clicking the
    notification. Specify the href if you want the user to be redirected to a specific page of the app,
    such as a specific message group that requires an id, after clicking the notification.

    @param sender_id:  id of user who initiated the notification creation
    @param recipient_id: id of user who is receiving the new notification
    @param notification_message: Description of the notification
    @param app_name: The name of the app to be redirected to the index page, such as messaging, appointments, etc.
    @param href: Format should be for example: href = reverse('messaging:view_message', args=[12])
    @return: status index page or 404 if user is not a staff

    """
    if not href:
        href = reverse(f"{app_name}:index")

    # Adding the href directly to the message group title text
    message_with_link = f"<span class='notification-link cursor-pointer' data-href={href}>{notification_message}</span>"

    notification = MessageGroup.objects.create(author_id=sender_id, recipient_id=recipient_id,
                                               title=message_with_link, type=1)
    notification.save()

class RSAEncryption:
    #keyLocation: place where you store the keys
    def __init__(self, key_location):
        self.key_location = key_location
        self.public_key_location = self.key_location/"publicKey.pem"
        self.private_key_location = self.key_location/"privateKey.pem"

    def generate_keys(self):
        (self.public_key, self.private_key) = rsa.newkeys(1024)
        with open(self.public_key_location, 'wb') as p:
            p.write(self.public_key.save_pkcs1('PEM'))
        with open(self.private_key_location, 'wb') as p:
            p.write(self.private_key.save_pkcs1('PEM'))

    def load_keys(self):
        with open(self.public_key_location, 'rb') as p:
            self.public_key = rsa.PublicKey.load_pkcs1(p.read())
        with open(self.private_key_location, 'rb') as p:
            self.private_key = rsa.PrivateKey.load_pkcs1(p.read())
        return self.private_key, self.public_key

    def encrypt(self, message):
        return base64.b64encode(rsa.encrypt(message.encode(), self.public_key)).decode()

    def decrypt(self, cipher_text):
        cipher_text = base64.b64decode(cipher_text.encode())
        return rsa.decrypt(cipher_text, self.private_key).decode()
