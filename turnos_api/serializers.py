from rest_framework import serializers
from.models import Funcionario, Ventanila, Turno

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