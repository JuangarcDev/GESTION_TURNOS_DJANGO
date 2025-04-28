from django.contrib.auth.models import User
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto
from .serializers import FuncionarioSerializer, VentanillaSerializer, TurnoSerializer, UsuarioSerializer, AtencionSerializer, PuestoSerializer, UsuarioAutenticadoSerializer
from .utils import handle_custom_exception
from .exceptions import CustomAPIException
from drf_spectacular.utils import extend_schema, OpenApiParameter

# Create your views here.
class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            # Llama a la función común para manejar excepciones
            return handle_custom_exception(
                self.get_queryset(),
                FuncionarioSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron registros en la base de datos"
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
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                VentanillaSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron registros en la base de datos"
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
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                TurnoSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron registros en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    #ACA CREAMOS LA PARTE DEL ENDPOINT PERSONALIZADO PARA BUSCAR POR ID DEL ESTADO EL ACTION PARA CREAR EL ENDPOINT Y EL EXTEND PARA PASARLE EL PARAMETRO QUE RECIBE EL ENDPOINT
    @extend_schema(
            parameters=[
                OpenApiParameter(name='estado_id',required=True, type=int, location=OpenApiParameter.QUERY, description='ID del estado del turno (1 a 4)')
            ]
    )
    @action(detail=False, methods=['get'], url_path='por-estado')
    def por_estado(self, request):
        estado_id = request.GET.get('estado_id')

        try:
            estado_id = int(estado_id)
        except (TypeError, ValueError):
             return Response({'error': 'Debe proporcionar un estado_id válido (int).'}, status=400)

        if estado_id not in [1, 2, 3, 4]:
            return Response({'error': 'Estado no válido. Valores permitidos: 1, 2, 3, 4.'}, status=400)
        
        turnos = Turno.objects.filter(estado_id=estado_id).order_by('fecha_turno')
        serializer = TurnoSerializer(turnos, many=True)
        return Response(serializer.data)
    
    #ACA CREAREMOS EL ENDPOINT PARA BUSCAR POR EL NOMBRE Y OPCIONALMENTE UNA FECHA
    @extend_schema(
        parameters=[
            OpenApiParameter(name='turno', required=False, type=str, location=OpenApiParameter.QUERY, description='Nombre (o parte del nombre) del turno'),
            OpenApiParameter(name='fecha_turno', required=False, type=str, location=OpenApiParameter.QUERY, description='Fecha del turno en formato YYYY-MM-DD')
        ]
    )

    @action(detail=False, methods=['get'], url_path='buscar-por-nombre-fecha')
    def buscar_por_nombre_fecha(self, request):
        turno = request.GET.get('turno', '').strip()
        fecha_turno = request.GET.get('fecha_turno', '').strip()

        turnos = Turno.objects.all()

        if turno:
            turnos = turnos.filter(turno__icontains=turno)

        if fecha_turno:
            fecha = parse_date(fecha_turno)
            if not fecha:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
            turnos = turnos.filter(fecha_turno__date=fecha)

        turnos = turnos.order_by('fecha_turno')
        serializer = TurnoSerializer(turnos, many=True)
        return Response(serializer.data)
    
    # NUEVO ENDPOINT PARA BUSCAR POR LA CEDULA DEL USUARIO
    @extend_schema(
        parameters=[
            OpenApiParameter(name='documento', required=True, type=str, location=OpenApiParameter.QUERY, description='Número de cédula del usuario')
        ]
    )
    @action(detail=False, methods=['get'], url_path='buscar-por-documento')
    def buscar_por_documento(self, request):
        documento = request.GET.get('documento', '').strip()

        if not documento:
            return Response({'error': 'Debe proporcionar un número de documento.'}, status=400)

        # 💡 OJO aquí: relacionamos Turno con Usuario a través de id_usuario__cedula
        turnos = Turno.objects.filter(id_usuario__cedula=documento).order_by('fecha_turno')

        if not turnos.exists():
            return Response({'message': 'No se encontraron turnos para el documento proporcionado.'}, status=404)

        serializer = TurnoSerializer(turnos, many=True)
        return Response(serializer.data)    

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    #permission_classes = [IsAuthenticated]


    def get_permissions(self):
        if self.action == 'create':  # POST
            return [AllowAny()]
        if self.action == 'retrieve':  # GET detalle (consultar 1 usuario por ID o documento)
            return [AllowAny()]
        return [IsAuthenticated()]  # Para list, update, partial_update, destroy

    def retrieve(self, request, *args, **kwargs):
        """Permitir solo la búsqueda por número de documento."""
        cedula = self.request.query_params.get('cedula', None)
        if cedula:
            usuario = Usuario.objects.filter(cedula=cedula).first()
            if usuario:
                serializer = self.get_serializer(usuario)
                return Response({
                    "success": True,
                    "message": "Usuario encontrado exitosamente.",
                    "data": serializer.data
                }, status=200)
            else:
                return Response({
                    "success": False,
                    "message": "No se encontró ningún usuario con el documento proporcionado."
                }, status=404)
        return super().retrieve(request, *args, **kwargs)
    
class AtencionViewSet(viewsets.ModelViewSet):
    queryset = Atencion.objects.all()
    serializer_class = AtencionSerializer
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                AtencionSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron registros en la base de datos"
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
    #permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                PuestoSerializer,
                "La consulta ha sido exitosa",
                "No se encontraron registros en la base de datos"
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
    #permission_classes = [IsAuthenticated]

    def get(self, request):
        Usuario = request.user
        serializer = UsuarioAutenticadoSerializer(Usuario)
        return Response(serializer.data)
    
