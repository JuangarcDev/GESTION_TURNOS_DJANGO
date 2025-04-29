from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection
from .models import TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.db import connection
from .models import TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla

def reset_sequence(model):
    table_name = model._meta.db_table
    sequence_sql = "ALTER SEQUENCE %s_id_seq RESTART WITH 1;" % table_name
    with connection.cursor() as cursor:
        cursor.execute(sequence_sql)

@receiver(post_migrate)
def poblar_tablas_dominio(sender, **kwargs):
    if sender.name == "turnos_api":
        # LIMPIAR REGISTROS Y REINICIAR SECUENCIA DE ID
        TipoTurno.objects.all().delete()
        reset_sequence(TipoTurno)

        TipoTramite.objects.all().delete()
        reset_sequence(TipoTramite)

        # Poblar TipoTurno
        tipos_turno = [
            {"id": 1, "nombre": "Prioritario", "abreviado": "P", "tiempo_espera": 15},
            {"id": 2, "nombre": "General", "abreviado": "G", "tiempo_espera": 45},
        ]
        for tipo in tipos_turno:
            TipoTurno.objects.create(**tipo)  # ahora sí insertamos con ID fijo


        # Poblar EstadoTurno
        estados_turno = ["Espera", "Atención", "Atendido", "Cancelado"]
        for estado in estados_turno:
            EstadoTurno.objects.get_or_create(nombre=estado)

        # Poblar TipoTramite con valores definidos
        estados_turno = ["Espera", "Atención", "Atendido", "Cancelado"]
        for estado in estados_turno:
            EstadoTurno.objects.get_or_create(nombre=estado)

        # Poblar TipoTramite con valores definidos
        tramites = [
            {"id": 1, "nombre": "Producto Consulta", "abreviado": "P", "tiempo_espera": 25},
            {"id": 2, "nombre": "Producto Emisión", "abreviado": "E", "tiempo_espera": 20},
            {"id": 3, "nombre": "Tramite Consulta", "abreviado": "S", "tiempo_espera": 40},
            {"id": 4, "nombre": "Tramite Radicacion", "abreviado": "T", "tiempo_espera": 25},
            {"id": 5, "nombre": "Correspondencia", "abreviado": "C", "tiempo_espera": 20},
            {"id": 6, "nombre": "Notificación", "abreviado": "N", "tiempo_espera": 20},
            {"id": 7, "nombre": "Peticiones, Quejas o Reclamos", "abreviado": "R", "tiempo_espera": 30},
        ]
        for tramite in tramites:
            TipoTramite.objects.create(**tramite)

        #Poblar EstadoVentanilla
        estados_ventanilla = ["Libre", "Ocupada", "Fuera de Servicio", "Otro"]
        for estado_v in estados_ventanilla:
            EstadoVentanilla.objects.get_or_create(nombre=estado_v)