from django.contrib.auth.models import User
from rest_framework import serializers
from.models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto, TipoTramite, TipoTurno

class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'

class VentanillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ventanila
        fields = '__all__'

class TurnoSerializer(serializers.ModelSerializer):
    tipo_tramite_nombre = serializers.CharField(source='tipo_tramite.nombre', read_only=True)
    tipo_turno_nombre = serializers.CharField(source='tipo_turno.nombre', read_only=True)
    nombre_usuario = serializers.CharField(source='id_usuario.nombres', read_only=True)
    apellido_usuario = serializers.CharField(source='id_usuario.apellidos', read_only=True)
    cedula_usuario = serializers.CharField(source='id_usuario.cedula', read_only=True)
    tramite_color = serializers.CharField(source='tipo_tramite.color', read_only=True)
    tipo_turno_color = serializers.CharField(source='tipo_turno.color', read_only=True)

    class Meta:
        model = Turno
        fields = [
            'id',
            'id_usuario',
            'nombre_usuario',
            'apellido_usuario',
            'turno',
            'tipo_turno',
            'tipo_turno_nombre',
            'estado',
            'tipo_tramite',
            'tipo_tramite_nombre',
            'fecha_turno',
            'cedula_usuario',
            'tramite_color',
            'tipo_turno_color',
        ]

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class AtencionSerializer(serializers.ModelSerializer):

    turno = serializers.CharField(source='id_turno.turno', read_only=True)
    estado = serializers.CharField(source='id_turno.estado.nombre', read_only=True)
    nombres_usuario = serializers.CharField(source='id_turno.id_usuario.nombres', read_only=True)
    apellidos_usuario = serializers.CharField(source='id_turno.id_usuario.apellidos', read_only=True)
    ventanilla_nombre = serializers.CharField(source='id_ventanilla.nombre', read_only=True)
    funcionario_nombre = serializers.CharField(source='id_funcionario.user.get_full_name', read_only=True)

    class Meta:
        model = Atencion
        fields = [
            'id',
            'fecha_atencion',
            'turno',
            'estado',
            'nombres_usuario',
            'apellidos_usuario',
            'ventanilla_nombre',
            'funcionario_nombre',
            'id_turno',
            'id_ventanilla',
            'id_funcionario'
        ]

class PuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Puesto
        fields = '__all__'

class UsuarioAutenticadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

class TipoTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTurno
        fields = '__all__'

class TipoTramiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTramite
        fields = '__all__'