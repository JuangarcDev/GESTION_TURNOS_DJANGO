from django.apps import AppConfig

class TurnosApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'turnos_api'

    def ready(self):
        print("⏳ Ejecutando método ready() en TurnosApiConfig...")
        try:
            import turnos_api.signals
            print("✅ Módulo de señales importado correctamente desde APPS.")
        except Exception as e:
            print(f"❌ Error al importar señales: {e}")