import json
from enum import Enum


with open("./Covigo/message_templates.json") as templates:
    MESSAGE_TEMPLATES = json.load(templates)


class Messages(Enum):
    REGISTER_USER = MESSAGE_TEMPLATES["register_user"]
    RESET_PASSWORD = MESSAGE_TEMPLATES["reset_password"]
    CHANGED_PASSWORD = MESSAGE_TEMPLATES["user_changed_password"]
    STATUS_UPDATE = MESSAGE_TEMPLATES["status_update"]
    MESSAGE_SENT = MESSAGE_TEMPLATES["message_sent"]
    MESSAGE_REPLY = MESSAGE_TEMPLATES["message_reply"]
