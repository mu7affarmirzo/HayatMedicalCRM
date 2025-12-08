from django.apps import AppConfig


class LogusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application.logus'

    def ready(self):
        """
        Import signals when the app is ready.
        TASK-022: Auto-logging of booking changes
        """
        import application.logus.signals
