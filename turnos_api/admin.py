from django.contrib import admin
from .models import (
    TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla,
    Usuario, Turno, Funcionario, Atencion, Ventanila, Puesto, User
)
from django.contrib.auth.admin import UserAdmin

class UserAdminCustom(UserAdmin):
    model = User
    list_display = ('username', 'email', 'is_staff', 'is_active')
    filter_horizontal = ('groups',)  # Esto permitirá agregar/quitar grupos fácilmente

# Desregistramos y volvemos a registrar el User con la nueva configuración
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)

@admin.register(TipoTurno)
class TipoTurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(EstadoTurno)
class EstadoTurnoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(TipoTramite)
class TipoTramiteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)


@admin.register(EstadoVentanilla)
class EstadoVentanillaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    ordering = ('nombre',)

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'apellidos', 'cedula', 'email', 'municipio', 'fecha_registro')
    list_display_links = ('nombres', 'cedula')
    search_fields = ('nombres', 'apellidos', 'cedula', 'email', 'municipio')
    ordering = ('cedula',)
    list_filter = ('municipio', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    fieldsets = (
        ('Datos Personales', {
            'fields': ('nombres', 'apellidos', 'cedula', 'telefono', 'email', 'direccion', 'municipio')
        }),
        ('Registro', {
            'fields': ('fecha_registro',)
        }),
    )

@admin.register(Turno)
class TurnoAdmin(admin.ModelAdmin):
    list_display = ('turno', 'id_usuario', 'tipo_turno', 'estado', 'tipo_tramite', 'fecha_turno')
    search_fields = ('turno', 'id_usuario__cedula', 'id_usuario__nombres')
    list_filter = ('tipo_turno', 'estado', 'tipo_tramite', 'fecha_turno')
    ordering = ('-fecha_turno',)
    readonly_fields = ('fecha_turno',)

@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'telefono', 'fecha_creacion', 'fecha_edicion')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'telefono')
    ordering = ('user',)
    readonly_fields = ('fecha_creacion', 'fecha_edicion')
    fieldsets = (
        ('Datos Personales', {
            'fields': ('user', 'telefono')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_edicion')
        }),
    )

    # Cuando un usuario se asigne al grupo "Ventanillas", se creará automáticamente el Funcionario
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Verificar si el usuario tiene el grupo "Ventanillas" asignado
        if "Ventanillas" in [group.name for group in obj.user.groups.all()]:
            # Si el grupo "Ventanillas" está asignado, crear o actualizar el Funcionario
            obj.save()

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('id_turno', 'id_funcionario', 'fecha_atencion')
    search_fields = ('id_turno__turno', 'id_funcionario__user')
    list_filter = ('fecha_atencion',)
    ordering = ('-fecha_atencion',)
    readonly_fields = ('fecha_atencion',)

@admin.register(Ventanila)
class VentanilaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estado', 'fecha_creacion', 'fecha_edicion')
    search_fields = ('nombre',)
    list_filter = ('estado',)
    readonly_fields = ('fecha_creacion', 'fecha_edicion')
    
@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ('id_funcionario', 'id_ventanilla', 'fecha_ingreso', 'fecha_salida')
    search_fields = ('id_funcionario__user', 'id_ventanilla__nombre')
    list_filter = ('fecha_ingreso', 'fecha_salida')
    ordering = ('-fecha_ingreso',)
    readonly_fields = ('fecha_ingreso',)
