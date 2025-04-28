from django.contrib import admin
from .models import (
    TipoTurno, EstadoTurno, TipoTramite, EstadoVentanilla,
    Usuario, Turno, Funcionario, Atencion, Ventanila, Puesto
)

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
    list_display = ('usario', 'nombre', 'telefono', 'email', 'fecha_creacion', 'fecha_edicion')
    search_fields = ('usario', 'nombre', 'email')
    ordering = ('usario',)
    readonly_fields = ('fecha_creacion', 'fecha_edicion')
    fieldsets = (
        ('Información de Acceso', {
            'fields': ('usario', 'password')
        }),
        ('Datos Personales', {
            'fields': ('nombre', 'telefono', 'email')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_edicion')
        }),
    )

@admin.register(Atencion)
class AtencionAdmin(admin.ModelAdmin):
    list_display = ('id_turno', 'id_funcionario', 'fecha_atencion')
    search_fields = ('id_turno__turno', 'id_funcionario__nombre')
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
    search_fields = ('id_funcionario__nombre', 'id_ventanilla__nombre')
    list_filter = ('fecha_ingreso', 'fecha_salida')
    ordering = ('-fecha_ingreso',)
    readonly_fields = ('fecha_ingreso',)
