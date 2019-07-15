from django.apps import AppConfig


class GeneralConfig(AppConfig):
    name = 'general'

    def ready(self):
        # import signal handlers
        from . import signals  # noqa: F401
