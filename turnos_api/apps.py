from django.apps import AppConfig

class TurnosApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'turnos_api'

    def ready(self):
        try:
            import turnos_api.signals
            print("Modulo de signals importado correctamente desde APPS.")
        except Exception as e:
            print(f"Error al importar signals: {e}")