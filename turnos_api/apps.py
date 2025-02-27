from django.apps import AppConfig


class TurnosApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'turnos_api'

    def ready(self):
        import turnos_api.signals