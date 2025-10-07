from django.db.models.signals import post_migrate, post_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction, connection
from .models import TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla, Funcionario, Ventanilla

# IMPORTACIONES PARA AUTH
from django.contrib.auth.models import User, Group

def reset_sequence(model, restart_from=None):
    table_name = model._meta.db_table
    sequence_name = f"{table_name}_id_seq"

    with connection.cursor() as cursor:
        if restart_from is not None:
            cursor.execute(f"ALTER SEQUENCE {sequence_name} RESTART WITH {restart_from};")
        else:
            cursor.execute(
                f"SELECT setval('{sequence_name}', COALESCE((SELECT MAX(id) FROM {table_name}), 1), true);"
            )

def renombrar_secuencia_antigua_si_existe():
    with connection.cursor() as cursor:
        cursor.execute("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_class WHERE relname = 'turnos_api_ventanila_id_seq'
                ) THEN
                    RAISE NOTICE 'Renombrando secuencia antigua ventanila_id_seq a ventanilla_id_seq...';
                    ALTER SEQUENCE turnos_api_ventanila_id_seq RENAME TO turnos_api_ventanilla_id_seq;
                END IF;
            END
            $$;
        """)

@receiver(post_migrate)
def poblar_tablas_dominio(sender, **kwargs):
    if sender.name != "turnos_api":
        return

    with transaction.atomic():

        # Renombrar secuencia antigua si tiene el nombre anterior al rename del modelo
        renombrar_secuencia_antigua_si_existe()
        
        # Reiniciar secuencias ANTES de insertar con IDs fijos
        reset_sequence(TipoTurno, restart_from=1)
        reset_sequence(EstadoTurno, restart_from=1)
        reset_sequence(TipoTramite, restart_from=1)
        reset_sequence(EstadoVentanilla, restart_from=1)
        reset_sequence(Ventanilla, restart_from=1)

        # Crear grupo Ventanillas si no existe
        grupo_ventanilla, creado = Group.objects.get_or_create(name="Ventanillas")
        if creado:
            print("Grupo 'Ventanillas' creado.")
        else:
            print("Grupo 'Ventanillas' ya existía.")

        # Poblado con IDs fijos
        tipos_turno = [
            {"id": 1, "nombre": "Prioritario", "abreviado": "P", "tiempo_espera": 15},
            {"id": 2, "nombre": "General", "abreviado": "G", "tiempo_espera": 45},
        ]
        for tipo in tipos_turno:
            TipoTurno.objects.update_or_create(id=tipo["id"], defaults=tipo)

        estados_turno = [
            {"id": 1, "nombre": "Espera"},
            {"id": 2, "nombre": "Atención"},
            {"id": 3, "nombre": "Finalizado"},
            {"id": 4, "nombre": "Cancelado"},
        ]
        for estado in estados_turno:
            EstadoTurno.objects.update_or_create(id=estado["id"], defaults={"nombre": estado["nombre"]})

        tramites = [
            {"id": 1, "nombre": "Producto Consulta", "abreviado": "P", "tiempo_espera": 25, "icono": "bi-search", "color": "#f39c12"},
            {"id": 2, "nombre": "Producto Emisión", "abreviado": "E", "tiempo_espera": 20, "icono": "bi-box-arrow-up", "color": "#27ae60"},
            {"id": 3, "nombre": "Tramite Consulta", "abreviado": "S", "tiempo_espera": 40, "icono": "bi-chat-left-dots", "color": "#8e44ad"},
            {"id": 4, "nombre": "Tramite Radicacion", "abreviado": "T", "tiempo_espera": 25, "icono": "bi-journal-check", "color": "#2980b9"},
            {"id": 5, "nombre": "Correspondencia", "abreviado": "C", "tiempo_espera": 20, "icono": "bi-envelope-open", "color": "#e74c3c"},
            {"id": 6, "nombre": "Notificación", "abreviado": "N", "tiempo_espera": 20, "icono": "bi-bell-fill", "color": "#1abc9c"},
            {"id": 7, "nombre": "Peticiones, Quejas o Reclamos", "abreviado": "R", "tiempo_espera": 30, "icono": "bi-exclamation-circle-fill", "color": "#d35400"},
        ]
        for tramite in tramites:
            TipoTramite.objects.update_or_create(id=tramite["id"], defaults=tramite)

        estados_ventanilla = [
            {"id": 1, "nombre": "Libre"},
            {"id": 2, "nombre": "Ocupada"},
            {"id": 3, "nombre": "Fuera de Servicio"},
            {"id": 4, "nombre": "Otro"},
        ]
        for estado in estados_ventanilla:
            EstadoVentanilla.objects.update_or_create(id=estado["id"], defaults={"nombre": estado["nombre"]})

        # Crear ventanillas por defecto
        estado_libre = EstadoVentanilla.objects.get(nombre='Libre')
        for i in range(1, 6):
            Ventanilla.objects.update_or_create(
                id=i,
                defaults={
                    'nombre': f'Ventanilla {i}',
                    'estado': estado_libre
                }
            )

        # Actualizar secuencias para que sigan desde el ID final
        reset_sequence(TipoTurno)
        reset_sequence(EstadoTurno)
        reset_sequence(TipoTramite)
        reset_sequence(EstadoVentanilla)
        reset_sequence(Ventanilla)

        # print("Tablas de dominio y secuencias configuradas correctamente.")

        
@receiver(post_save, sender=User)
def crear_funcionario_automaticamente(sender, instance, created, **kwargs):
    # print(f"signal activada - Usuario: {instance.username}, created: {created}")
    if created:
        try:
            grupo_ventanilla = Group.objects.get(name='Ventanillas')
            # print(f"¿Usuario en grupo Ventanillas?: {grupo_ventanilla in instance.groups.all()}")
            if grupo_ventanilla in instance.groups.all():
                if not Funcionario.objects.filter(user=instance).exists():
                    Funcionario.objects.create(user=instance)
                    # print("Funcionario creado.")
        except Group.DoesNotExist:
            print("Grupo 'Ventanillas' no existe")

@receiver(m2m_changed, sender=User.groups.through)
def crear_funcionario_si_ventanilla(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        grupo_ventanilla = Group.objects.filter(name="Ventanillas").first()
        if grupo_ventanilla and grupo_ventanilla.pk in pk_set:
            if not Funcionario.objects.filter(user=instance).exists():
                Funcionario.objects.create(user=instance)
                # print(f"Funcionario creado automáticamente para el usuario: {instance.username}")
            else:
                print(f"El usuario {instance.username} ya tiene un Funcionario asignado.")
                