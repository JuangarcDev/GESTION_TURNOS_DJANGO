from django.db.models.signals import post_migrate, post_save, m2m_changed
from django.dispatch import receiver
from django.db import connection
from .models import TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla, Funcionario
from django.db.models.signals import post_migrate
from django.db import connection
# IMPORTACIONES PARA AUTH
from django.contrib.auth.models import User, Group

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
        estados_turno = ["Pendiante", "En atención", "Finalizado", "Cancelado"]
        for estado in estados_turno:
            EstadoTurno.objects.get_or_create(nombre=estado)

        # Poblar TipoTramite con valores definidos
        estados_turno = ["Pendiante", "En atención", "Finalizado", "Cancelado"]
        for estado in estados_turno:
            EstadoTurno.objects.get_or_create(nombre=estado)

        # Poblar TipoTramite con valores definidos
        tramites = [
            {"id": 1, "nombre": "Producto Consulta", "abreviado": "P", "tiempo_espera": 25,"icono": "bi-search", "color": "#f39c12"},
            {"id": 2, "nombre": "Producto Emisión", "abreviado": "E", "tiempo_espera": 20,"icono": "bi-box-arrow-up", "color": "#27ae60"},
            {"id": 3, "nombre": "Tramite Consulta", "abreviado": "S", "tiempo_espera": 40,"icono": "bi-chat-left-dots", "color": "#8e44ad"},
            {"id": 4, "nombre": "Tramite Radicacion", "abreviado": "T", "tiempo_espera": 25,"icono": "bi-journal-check", "color": "#2980b9"},
            {"id": 5, "nombre": "Correspondencia", "abreviado": "C", "tiempo_espera": 20,"icono": "bi-envelope-open","color": "#e74c3c"},
            {"id": 6, "nombre": "Notificación", "abreviado": "N", "tiempo_espera": 20,"icono": "bi-bell-fill","color": "#1abc9c"},
            {"id": 7, "nombre": "Peticiones, Quejas o Reclamos", "abreviado": "R", "tiempo_espera": 30,"icono": "bi-exclamation-circle-fill","color": "#d35400"},
        ]
        for tramite in tramites:
            TipoTramite.objects.create(**tramite)

        #Poblar EstadoVentanilla
        estados_ventanilla = ["Libre", "Ocupada", "Fuera de Servicio", "Otro"]
        for estado_v in estados_ventanilla:
            EstadoVentanilla.objects.get_or_create(nombre=estado_v)

@receiver(post_save, sender=User)
def crear_funcionario_automaticamente(sender, instance, created, **kwargs):
    print(f"🧪 Señal activada - Usuario: {instance.username}, created: {created}")
    if created:
        try:
            grupo_ventanilla = Group.objects.get(name='Ventanillas')
            print(f"➡️ ¿Usuario en grupo Ventanillas?: {grupo_ventanilla in instance.groups.all()}")
            if grupo_ventanilla in instance.groups.all():
                if not Funcionario.objects.filter(user=instance).exists():
                    Funcionario.objects.create(user=instance)
                    print("✅ Funcionario creado.")
        except Group.DoesNotExist:
            print("❌ Grupo 'Ventanillas' no existe")

@receiver(m2m_changed, sender=User.groups.through)
def crear_funcionario_si_ventanilla(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        grupo_ventanilla = Group.objects.filter(name="Ventanillas").first()
        if grupo_ventanilla and grupo_ventanilla.pk in pk_set:
            if not Funcionario.objects.filter(user=instance).exists():
                Funcionario.objects.create(user=instance)
                print(f"✅ Funcionario creado automáticamente para el usuario: {instance.username}")
            else:
                print(f"ℹ️ El usuario {instance.username} ya tiene un Funcionario asignado.")