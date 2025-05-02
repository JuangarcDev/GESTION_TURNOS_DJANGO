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
    class Meta:
        model = Turno
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = '__all__'

class AtencionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Atencion
        fields = '__all__'

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