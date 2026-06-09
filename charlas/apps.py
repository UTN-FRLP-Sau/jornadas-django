from django.apps import AppConfig


class CharlasConfig(AppConfig):
    name = 'charlas'

    def ready(self):
        import charlas.signals  # noqa: F401
