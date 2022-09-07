from django.apps import AppConfig


class ShowroomConnectorConfig(AppConfig):
    name = 'showroom_connector'

    def ready(self):
        # import signal handlers
        from . import signals  # noqa: F401
