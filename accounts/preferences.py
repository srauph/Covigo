from enum import Enum


class SystemMessagesPreference(Enum):
    NAME = "system_msg_methods"
    EMAIL = "use_email"
    SMS = "use_sms"


class StatusReminderPreference(Enum):
    NAME = "status_reminder_interval"
