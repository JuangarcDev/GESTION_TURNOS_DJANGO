from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto
from .serializers import FuncionarioSerializer, VentanillaSerializer, TurnoSerializer, UsuarioSerializer, AtencionSerializer, PuestoSerializer, UsuarioAutenticadoSerializer
from .utils import handle_custom_exception
from .exceptions import CustomAPIException

# Create your views here.
class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            # Llama a la función común para manejar excepciones
            return handle_custom_exception(
                self.get_queryset(),
                FuncionarioSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron funcionarios en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)
        
        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VentanillaViewSet(viewsets.ModelViewSet):
    queryset = Ventanila.objects.all()
    serializer_class = VentanillaSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                VentanillaSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron turnos en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

class TurnoViewSet(viewsets.ModelViewSet):
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                TurnoSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron turnos en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                UsuarioSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron turnos en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AtencionViewSet(viewsets.ModelViewSet):
    queryset = Atencion.objects.all()
    serializer_class = AtencionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                AtencionSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron turnos en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

class PuestoViewSet(viewsets.ModelViewSet):
    queryset = Puesto.objects.all()
    serializer_class = PuestoSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                PuestoSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron turnos en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#  API VIEW USUARIO AUTENTICADO
class UsuarioActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        Usuario = request.user
        serializer = UsuarioAutenticadoSerializer(Usuario)
        return Response(serializer.data)