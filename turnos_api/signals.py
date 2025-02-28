from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla

@receiver(post_migrate)
def poblar_tablas_dominio(sender, **kwargs):
    if sender.name == "turnos_api":
        # Poblar TipoTurno
        tipos_turno = ["General", "Prioritario"]
        for tipo in tipos_turno:
            TipoTurno.objects.get_or_create(nombre=tipo)

        # Poblar EstadoTurno
        estados_turno = ["Espera", "Atención", "Atendido", "Cancelado"]
        for estado in estados_turno:
            EstadoTurno.objects.get_or_create(nombre=estado)

        # Poblar TipoTramite
        tramites = ["Tramite Consulta", "Tramite Radicacion", "Producto Consulta", "Producto Emisión", "Correspondencia", "Notificación"]
        for tramite in tramites:
            TipoTramite.objects.get_or_create(nombre=tramite)

        #Poblar EstadoVentanilla
        estados_ventanilla = ["Libre", "Ocupada", "Fuera de Servicio", "Otro"]
        for estado_v in estados_ventanilla:
            EstadoVentanilla.objects.get_or_create(nombre=estado_v)