from django.contrib.auth.models import User, Group
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Funcionario, Ventanila, Turno, Usuario, Atencion, Puesto, TipoTramite, TipoTurno, EstadoVentanilla, EstadoTurno
from .serializers import FuncionarioSerializer, VentanillaSerializer, TurnoSerializer, UsuarioSerializer, AtencionSerializer, PuestoSerializer, UsuarioAutenticadoSerializer, TipoTramiteSerializer, TipoTurnoSerializer, AsignarVentanillaSerializer, AtenderTurnoSerializer
from .utils import handle_custom_exception
from .exceptions import CustomAPIException
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.utils.timezone import now, localtime
from django.db.models import Count
from datetime import datetime, timedelta
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError, NotFound, APIException
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import status
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from jwt import decode as jwt_decode
from django.conf import settings
from django.utils import timezone

# UTILIDAD MOVER POSTERIORMENTE A SU PROPIO FICHERO

def generar_nombre_turno(tipo_tramite_abrev, tipo_turno_abrev):
    hoy = now().date()
    contador = Turno.objects.filter(
        fecha_turno__date=hoy,
        tipo_tramite__abreviado=tipo_tramite_abrev,
        tipo_turno__abreviado=tipo_turno_abrev
     ).count() + 1
    
    secuencia = str(contador).zfill(3)
    return f"{tipo_tramite_abrev}{tipo_turno_abrev}{secuencia}"

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
    permission_classes = [IsAuthenticated]

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
    permission_classes = [IsAuthenticated]

    # Permitimos que el metodo POST sea público o no requiera de Autenticación
    def get_permissions(self):
        if self.action == 'create':
            return [] # Permitir que sea público el método POST
        return super().get_permissions()

    # Sobreescribimos metodo create, para completar automaticámente el valor de los 3 atributos(fecha_turno, estado y turno) cuando se cree un nuevo registro de turno
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Obtener la hora actual como fecha_turno por defecto
        if 'fecha_turno' not in data or not data['fecha_turno']:
            data['fecha_turno'] = now()

        # Estado del turno por defecto en espera
        if 'estado' not in data or not data['estado']:
            data['estado'] = 1

        # Generar el nombre del turno
        if 'turno' not in data or not data['turno']:
            try:
                tramite_abrev = Turno.objects.model.tipo_tramite.field.related_model.objects.get(id=int(data['tipo_tramite'])).abreviado
                tipo_abrev = Turno.objects.model.tipo_turno.field.related_model.objects.get(id=int(data['tipo_turno'])).abreviado
                data['turno'] = generar_nombre_turno(tramite_abrev, tipo_abrev)
            except Exception as e:
                return Response({'error': f'Error generando el nombre del turno: {str(e)}'}, status=400)
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
    
    # ENDPOINT PARA BUSCAR POR ESTADO DE TURNO Y POSTERIOR POR TIPO DE TRAMITE
    @extend_schema(
        parameters=[
            OpenApiParameter(name='estado_id', required=False, type=int, location=OpenApiParameter.QUERY, description='ID del estado del turno (1 a 4)'),
            OpenApiParameter(name='tipo_tramite_id', required=False, type=int, location=OpenApiParameter.QUERY, description='ID del tipo de trámite')
        ]
    )
    @action(detail=False, methods=['get'], url_path='buscar-por-estado-tramite')
    def buscar_por_estado_tramite(self, request):
        estado_id = request.GET.get('estado_id', None)
        tipo_tramite_id = request.GET.get('tipo_tramite_id', None)

        # Inicializar la consulta base para todos los turnos
        turnos = Turno.objects.all()

        # Filtrar por estado si se proporciona
        if estado_id:
            try:
                estado_id = int(estado_id)
                if estado_id not in [1, 2, 3, 4]:
                    return Response({'error': 'Estado no válido. Valores permitidos: 1, 2, 3, 4.'}, status=400)
                turnos = turnos.filter(estado_id=estado_id)
            except (TypeError, ValueError):
                return Response({'error': 'Debe proporcionar un estado_id válido (int).'}, status=400)

        # Filtrar por tipo de trámite si se proporciona
        if tipo_tramite_id:
            try:
                tipo_tramite_id = int(tipo_tramite_id)
                turnos = turnos.filter(tipo_tramite_id=tipo_tramite_id)
            except ValueError:
                return Response({'error': 'tipo_tramite_id debe ser un número entero.'}, status=400)

        # Orden descendente por fecha_turno
        turnos = turnos.order_by('-fecha_turno')

        # Serialización de los resultados
        serializer = TurnoSerializer(turnos, many=True)
        return Response(serializer.data)

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action in ['create', 'buscar_por_cedula']:  # POST crear usuario o GET buscar por cédula
            return [AllowAny()]
        return [IsAuthenticated()]  # Para retrieve (por ID), list, update, destroy, etc.

    def retrieve(self, request, *args, **kwargs):
        """Consulta de usuario por ID (protegida por token)."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        parameters=[
            OpenApiParameter(name='cedula', required=True, type=str, location=OpenApiParameter.QUERY, description='Número de cédula del usuario')
        ]
    )
    @action(detail=False, methods=['get'], url_path='buscar-por-cedula')
    def buscar_por_cedula(self, request):
        """Consulta pública de usuario por número de cédula."""
        cedula = request.query_params.get('cedula', '').strip()

        if not cedula:
            return Response({'success': False, 'message': 'Debe proporcionar una cédula.'}, status=status.HTTP_400_BAD_REQUEST)

        usuario = Usuario.objects.filter(cedula=cedula).first()

        if not usuario:
            return Response({'success': False, 'message': 'No se encontró ningún usuario con la cédula proporcionada.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(usuario)
        return Response({
            'success': True,
            'message': 'Usuario encontrado exitosamente.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

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
                "No se encontraron registros en la base de datos"
            )
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

    # ENDPOINT PARA LISTAR LOS ULTIMOS 6 REGISTROS DE ATENCION DEL DIA ACTUAL
    @action(detail=False, methods=['get'], url_path='ultimas-6')
    def ultimas_6(self, request):
        try:
            hoy = localtime(now()).date()
            atenciones = Atencion.objects.filter(
                fecha_atencion__date=hoy
            ).select_related('id_turno__id_usuario', 'id_turno__estado', 'id_ventanilla').order_by('-fecha_atencion')[:6]

            resultado = []
            for atencion in atenciones:
                turno = atencion.id_turno
                usuario = turno.id_usuario if turno else None
                ventanilla = atencion.id_ventanilla if atencion else None

                resultado.append({
                    'turno': turno.turno if turno else None,
                    'estado': turno.estado.nombre if turno and turno.estado else None,
                    'fecha_atencion': localtime(atencion.fecha_atencion),
                    'id_ventanilla': atencion.id_ventanilla.id if atencion.id_ventanilla else None,
                    'ventanilla': ventanilla.nombre if ventanilla else None,
                    'nombres': usuario.nombres if usuario else None,
                    'apellidos': usuario.apellidos if usuario else None,
                })

            return Response(resultado)
        except TypeError as e:
            return Response({
                "success": False,
                "message": f"Error de serialización: {str(e)}"
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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        Usuario = request.user
        serializer = UsuarioAutenticadoSerializer(Usuario)
        return Response(serializer.data)
    
# CREAR VISTA PARA LISTAR TIPO DE TRAMITES
class TipoTramiteListView(ListAPIView):
    queryset = TipoTramite.objects.all()
    serializer_class = TipoTramiteSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                TipoTramiteSerializer,
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

# CREAR VISTA PARA LISTAR LOS TIPOS DE TURNOS
class TipoTurnoListView(ListAPIView):
    queryset = TipoTurno.objects.all()
    serializer_class = TipoTurnoSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                TipoTurnoSerializer,
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
        
# ENDPOINTS PARA EL LOGEO Y FUNCIONES GENERALES DEL USUARIO INTERNO
# 0 Utilizar endpoint de TOKEN y posterior el de usuario actual
# 1 LISTAR VENTANILLAS CON ESTADO

class VentanillaListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        ventanillas = Ventanila.objects.all()
        data = [{"id": v.id, "nombre": v.nombre, "estado": v.estado.nombre} for v in ventanillas]
        return Response(data)

# ENDPOINT PARA CREAR REGISTRO EN PUESTO Y ACTUALIZAR ESTADO DE VENTANILLA
class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict occurred."
    default_code = "conflict"


@extend_schema(
    request=AsignarVentanillaSerializer,
    responses={
        201: OpenApiTypes.OBJECT,
        400: OpenApiTypes.OBJECT,
        404: OpenApiTypes.OBJECT,
        409: OpenApiTypes.OBJECT,
    },
    description="Asigna una ventanilla a un funcionario, creando un registro de puesto y cambiando el estado de la ventanilla a Ocupada."
)
class AsignarVentanillaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        funcionario_id = request.data.get("funcionario_id")
        ventanilla_id = request.data.get("ventanilla_id")
        confirmar = request.data.get("confirmar", False)

        # Validación de parámetros obligatorios
        if not funcionario_id or not ventanilla_id:
            raise ValidationError({
                "funcionario_id": "Este campo es obligatorio.",
                "ventanilla_id": "Este campo es obligatorio."
            })

        # Validación de existencia del funcionario
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
        except Funcionario.DoesNotExist:
            raise NotFound(detail=f"Funcionario con ID {funcionario_id} no encontrado.", code="funcionario_no_encontrado")

        # Validación de existencia de la ventanilla
        try:
            ventanilla = Ventanila.objects.get(id=ventanilla_id)
        except Ventanila.DoesNotExist:
            raise NotFound(detail=f"Ventanilla con ID {ventanilla_id} no encontrada.", code="ventanilla_no_encontrada")

        # Validación de ocupación de la ventanilla
        if ventanilla.estado.nombre == "Ocupada" and not confirmar:
            raise ConflictError(detail={
                "message": "La ventanilla está actualmente ocupada. Debe confirmar si desea continuar.",
                "require_confirm": True
            })


        # Obtener token del usuario autenticado
        # Obtener token JWT desde el header
        auth_header = request.headers.get('Authorization', '')
        token_value = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        # Asignación del puesto con token
        puesto = Puesto.objects.create(
            id_funcionario=funcionario,
            id_ventanilla=ventanilla,
            token=token_value
        )

        # Cambio de estado de la ventanilla
        try:
            estado_ocupada = EstadoVentanilla.objects.get(nombre="Ocupada")
        except EstadoVentanilla.DoesNotExist:
            raise APIException(detail="El estado 'Ocupada' no está definido en el sistema.", code="estado_no_encontrado")

        ventanilla.estado = estado_ocupada
        ventanilla.save()

        return Response({
            "success": True,
            "message": "Ventanilla asignada correctamente.",
            "puesto_id": puesto.id,
            "token": token_value
        }, status=status.HTTP_201_CREATED)
    
# ENDPOINT PARA ATENDER TURNO. FUNCIONARIO - TOKEN - PUESTO
@api_view(['POST'])
def atender_turno(request, turno_id):
    token = request.headers.get('Authorization')
    if not token:
        return Response({"error": "Token requerido."}, status=400)

    try:
        # Extraemos el token del encabezado
        token = token.split(' ')[1]
        UntypedToken(token)  # Verifica que el token es válido
    except IndexError:
        return Response({"error": "Token mal formado."}, status=400)
    except AuthenticationFailed:
        return Response({"error": "Token inválido o expirado."}, status=401)

    #print(f"Token recibido y verificado: {token}")  # Verificación en el log

    puesto = Puesto.objects.filter(token=token, fecha_salida__isnull=True).first()

    if not puesto:
        return Response({"error": "Token inválido o sesión terminada."}, status=401)

    # Verificar si ya hay una atención activa del funcionario
    if Atencion.objects.filter(id_funcionario=puesto.id_funcionario, id_turno__estado__nombre='Atención').exists():
        return Response({"error": "Ya existe un turno en atención. Debe finalizarlo antes."}, status=400)

    turno = get_object_or_404(Turno, id=turno_id)
    if turno.estado.nombre != "Espera":
        return Response({"error": "El turno no está disponible para ser atendido."}, status=400)

    # Cambiar estado del turno a EN ATENCION
    estado_en_atencion = EstadoTurno.objects.get(nombre="Atención")
    turno.estado = estado_en_atencion
    turno.save()

    atencion = Atencion.objects.create(
        id_funcionario=puesto.id_funcionario,
        id_turno=turno,
        id_ventanilla=puesto.id_ventanilla,
        fecha_atencion=now()
    )

    return Response({"message": "Turno atendido con éxito", "atencion_id": atencion.id})

# ENPOINT PARA FINALIZAR ATENCION DE TURNO.
@api_view(['POST'])
def finalizar_turno(request, turno_id):  # Cambio: agregamos turno_id en los parámetros de la vista
    # Verificar si el token está presente en la cabecera
    token = request.headers.get('Authorization')
    if not token:
        return Response({"error": "Token requerido."}, status=400)

    try:
        # Extraemos el token del encabezado y verificamos su validez
        token = token.split(' ')[1]
        UntypedToken(token)  # Verifica que el token es válido
    except IndexError:
        return Response({"error": "Token mal formado."}, status=400)
    except AuthenticationFailed:
        return Response({"error": "Token inválido o expirado."}, status=401)

    # Buscar el puesto asociado al token
    puesto = Puesto.objects.filter(token=token, fecha_salida__isnull=True).first()
    if not puesto:
        return Response({"error": "Token inválido o sesión terminada."}, status=401)

    # Obtener el turno a partir del ID en la URL
    turno = get_object_or_404(Turno, id=turno_id)
    if turno.estado.nombre != "Atención":
        return Response({"error": "Este turno no está en atención actualmente."}, status=400)

    # Validar que el turno fue atendido por este funcionario
    atencion = Atencion.objects.filter(id_turno=turno, id_funcionario=puesto.id_funcionario).first()
    if not atencion:
        return Response({"error": "Este turno no está siendo atendido por usted."}, status=403)

    # Cambiar el estado del turno a 'Atendido'
    estado_atendido = EstadoTurno.objects.get(nombre="Atendido")
    turno.estado = estado_atendido
    turno.save()

    # Registrar la fecha de finalización
    atencion.fecha_fin_atencion = timezone.now()
    atencion.save()

    return Response({"message": "Turno finalizado correctamente."})

# ENDPOINT PARA HACER EL LOGOUT DE LA SESIÓN
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({"detail": "Token no proporcionado."}, status=status.HTTP_400_BAD_REQUEST)

        raw_token = auth_header.split(' ')[1]

        # Paso 1: Obtener jti desde el token
        try:
            # Paso 1: Decodificar el token para obtener el jti
            decoded = jwt_decode(raw_token, settings.SIMPLE_JWT['SIGNING_KEY'], algorithms=["HS256"])
            jti = decoded.get("jti")

            # Paso 2: Intentar invalidar el token (manejar caso cuando no existe)
            token_obj, created = OutstandingToken.objects.get_or_create(
                jti=jti,
                defaults={
                    'token': raw_token,
                    'created_at': timezone.now(),
                    'expires_at': datetime.fromtimestamp(decoded['exp'], timezone.utc),
                    'user_id': request.user.id
                }
            )

            BlacklistedToken.objects.get_or_create(token=token_obj)

        except Exception as e:
            return Response({"detail": "Token inválido o mal formado."}, status=status.HTTP_400_BAD_REQUEST)

        # Paso 3: Cerrar el puesto asociado a ese token
        try:
            puesto = Puesto.objects.get(token=raw_token, fecha_salida__isnull=True)
            puesto.fecha_salida = timezone.now()
            puesto.token = None  # limpiar el token si es necesario
            puesto.save()
        except Puesto.DoesNotExist:
            puesto.token = None
            
        return Response({"detail": "Sesión finalizada correctamente."}, status=status.HTTP_200_OK)