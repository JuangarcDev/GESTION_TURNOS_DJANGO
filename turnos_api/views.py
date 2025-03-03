from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto
from .serializers import FuncionarioSerializer, VentanillaSerializer, TurnoSerializer, UsuarioSerializer, AtencionSerializer, PuestoSerializer

# Create your views here.
class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]

class VentanillaViewSet(viewsets.ModelViewSet):
    queryset = Ventanila.objects.all()
    serializer_class = VentanillaSerializer
    permission_classes = [IsAuthenticated]

class TurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

class AtencionViewSet(viewsets.ModelViewSet):
    queryset = Atencion.objects.all()
    serializer_class = AtencionSerializer
    permission_classes = [IsAuthenticated]

class PuestoViewSet(viewsets.ModelViewSet):
    queryset = Puesto.objects.all()
    serializer_class = PuestoSerializer
    permission_classes = [IsAuthenticated]