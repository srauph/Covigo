from django.apps import AppConfig

class CodeConfig(AppConfig):
    name = 'codes'

    def ready(self):
        import codes.signals