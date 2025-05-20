from django.contrib.auth.models import User
from rest_framework import serializers
from.models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto, TipoTramite, TipoTurno, EstadoVentanilla, EstadoTurno

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
    tiempo_estimado_maximo = serializers.SerializerMethodField()

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
            'tiempo_estimado_maximo',
            'estado',
            'tipo_tramite',
            'tipo_tramite_nombre',
            'fecha_turno',
            'cedula_usuario',
            'tramite_color',
            'tipo_turno_color',
        ]

    def get_tiempo_estimado_maximo(self, obj):
        if obj.tipo_turno.id == 1:  # Prioritario
            return 15
        elif obj.tipo_turno.id == 2:  # General
            return obj.tipo_tramite.tiempo_espera
        return None


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
    tiempo_atencion = serializers.SerializerMethodField()

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
            'id_funcionario',
            'fecha_fin_atencion',
            'tiempo_atencion'
        ]

    def get_tiempo_atencion(self, obj):
        if obj.fecha_fin_atencion and obj.fecha_atencion:
            delta = obj.fecha_fin_atencion - obj.fecha_atencion
            return round(delta.total_seconds() / 60, 2)  # puedes convertir a minutos si prefieres
        return None

class PuestoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Puesto
        fields = '__all__'

class UsuarioAutenticadoSerializer(serializers.ModelSerializer):
    func_ventanilla = serializers.SerializerMethodField()
    id_funcionario = serializers.CharField(source="funcionario.id", read_only=True)
    class Meta:
        model = User
        fields = ["id", 
                  "username", 
                  "first_name", 
                  "last_name", 
                  "func_ventanilla",
                  "id_funcionario"]

    def get_func_ventanilla(self, obj):
        return obj.groups.filter(name="Ventanillas").exists()

class TipoTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTurno
        fields = '__all__'

class TipoTramiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoTramite
        fields = '__all__'

class EstadoVentanillaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoVentanilla
        fields = '__all__'

class EstadoTurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoTurno
        fields = '__all__'


# SERIALIZADOR PERSONALIZADO PARA ASIGNAR PUESTO:
class AsignarVentanillaSerializer(serializers.Serializer):
    funcionario_id = serializers.IntegerField()
    ventanilla_id = serializers.IntegerField()
    confirmar = serializers.BooleanField(required=False)
    # Este campo es opcional si solo lo asignas internamente
    token = serializers.CharField(read_only=True)

# SERIALIZADOR PERSONALIZADO PARA ATENDER TURNO
class AtenderTurnoSerializer(serializers.Serializer):
    id_turno = serializers.IntegerField(required=True)

# SERIALIZADOR PARA INVALIDAR EL TOKEN Y REALIZAR EL LOGGOUT
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="Token de refresh que se va a invalidar")