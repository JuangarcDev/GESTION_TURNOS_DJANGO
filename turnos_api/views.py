from django.contrib.auth.models import User, Group
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Funcionario, Ventanilla, Turno, Usuario, Atencion, Puesto, TipoTramite, TipoTurno, EstadoVentanilla, EstadoTurno
from .serializers import FuncionarioSerializer, VentanillaSerializer, TurnoSerializer, UsuarioSerializer, AtencionSerializer, PuestoSerializer, UsuarioAutenticadoSerializer, TipoTramiteSerializer, TipoTurnoSerializer, AsignarVentanillaSerializer, AtenderTurnoSerializer, LogoutSerializer, FinalizarTurnoResponseSerializer, ErrorResponseSerializer, EstadisticasFuncionarioSerializer, EstadisticaLabelValorSerializer
from .utils import handle_custom_exception
from .exceptions import CustomAPIException
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample, OpenApiResponse, extend_schema_view
from django.utils.timezone import now, localtime, make_aware, timedelta
from datetime import datetime, time
import pytz
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from datetime import datetime, timedelta
from rest_framework.generics import ListAPIView
from rest_framework.exceptions import ValidationError, NotFound, APIException, AuthenticationFailed
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import UntypedToken, RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from jwt import decode as jwt_decode
from django.conf import settings
from django.utils import timezone
from django.db.models.functions import TruncDate


# UTILIDAD MOVER POSTERIORMENTE A SU PROPIO FICHERO

def generar_nombre_turno(tipo_tramite_abrev, tipo_turno_abrev):
    hoy = localtime().date()
    contador = Turno.objects.filter(
        fecha_turno__date=hoy,
        tipo_tramite__abreviado=tipo_tramite_abrev,
        tipo_turno__abreviado=tipo_turno_abrev
     ).count() + 1
    
    secuencia = str(contador).zfill(3)
    return f"{tipo_tramite_abrev}{tipo_turno_abrev}{secuencia}"

# Create your views here.
class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.select_related('user')  # OPTIMIZACIÓN
    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            queryset = list(self.get_queryset())  # Evalúa una sola vez
            if not queryset:
                raise CustomAPIException("No se encontraron registros en la base de datos", 404)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "message": "La consulta ha sido exitosa",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except CustomAPIException as e:
            return Response(e.detail, status=e.status_code)
        except Exception as e:
            return Response({
                "success": False,
                "message": "Ocurrió un error inesperado: " + str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VentanillaViewSet(viewsets.ModelViewSet):
    queryset = Ventanilla.objects.select_related('estado')  # OPTIMIZACIÓN
    serializer_class = VentanillaSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            queryset = list(self.get_queryset())
            if not queryset:
                raise CustomAPIException("No se encontraron registros en la base de datos", 404)
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "message": "La consulta ha sido exitosa",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
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

        # Validar ID de usuario
        id_usuario = data.get('id_usuario')
        if not id_usuario:
            return Response({'error': 'Se requiere el id_usuario para crear el turno.'}, status=400)

        # Validar turnos recientes en los últimos 2 minutos
        hace_dos_min = now() - timedelta(minutes=2)
        turno_reciente = Turno.objects.filter(
            id_usuario_id=id_usuario,
            fecha_turno__gte=hace_dos_min
        ).exists()

        if turno_reciente:
            return Response({
                'error': 'Ya tienes un turno registrado en los últimos 2 minutos. Por favor, espera un momento antes de pedir otro.'
            }, status=400)

        # Valor por defecto para fecha_turno
        if 'fecha_turno' not in data or not data['fecha_turno']:
            data['fecha_turno'] = localtime()

        # Valor por defecto para estado
        if 'estado' not in data or not data['estado']:
            data['estado'] = 1

        # Generación automática del código de turno
        if 'turno' not in data or not data['turno']:
            try:
                tramite_id = int(data['tipo_tramite'])
                tipo_id = int(data['tipo_turno'])

                tramite = TipoTramite.objects.only('abreviado').get(id=tramite_id)
                tipo = TipoTurno.objects.only('abreviado').get(id=tipo_id)

                data['turno'] = generar_nombre_turno(tramite.abreviado, tipo.abreviado)
            except (TipoTramite.DoesNotExist, TipoTurno.DoesNotExist):
                return Response({'error': 'Tipo de trámite o tipo de turno no válido.'}, status=400)
            except Exception as e:
                return Response({'error': f'Error generando el nombre del turno: {str(e)}'}, status=400)

        # Serialización y guardado
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset().select_related(
                'tipo_tramite', 'tipo_turno', 'estado', 'id_usuario'
            )
            if not queryset.exists():
                raise CustomAPIException("No se encontraron registros en la base de datos", 404)

            serializer = self.get_serializer(queryset, many=True)
            return Response({
                "success": True,
                "message": "La consulta ha sido exitosa",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
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
            OpenApiParameter(name='estado_id', required=False, type=int, location=OpenApiParameter.QUERY, description='ID del estado del turno (1 a 4, opcional)'),
            OpenApiParameter(name='fecha_inicio', required=False, type=str, location=OpenApiParameter.QUERY, description='Fecha de inicio en formato YYYY-MM-DD'),
            OpenApiParameter(name='fecha_fin', required=False, type=str, location=OpenApiParameter.QUERY, description='Fecha de fin en formato YYYY-MM-DD'),
        ]
    )
    @action(detail=False, methods=['get'], url_path='por-estado', permission_classes=[IsAuthenticated])
    def por_estado(self, request):
        estado_id = request.GET.get('estado_id')
        fecha_inicio_str = request.GET.get('fecha_inicio')
        fecha_fin_str = request.GET.get('fecha_fin')

        # 🔐 Validación y extracción del token
        token_header = request.headers.get('Authorization')
        if not token_header:
            return Response({"error": "Token requerido en el header Authorization"}, status=400)

        try:
            token = token_header.split(' ')[1]
            UntypedToken(token)
        except Exception:
            return Response({"error": "Token inválido o expirado"}, status=401)

        # 🚪 Obtener el puesto asociado al token
        puesto = Puesto.objects.select_related('id_ventanilla').filter(token=token, fecha_salida__isnull=True).first()
        if not puesto:
            return Response({"error": "No se encontró puesto activo asociado al token"}, status=401)
        
        ventanilla_id = puesto.id_ventanilla.id

        # 🧠 Manejo de fechas con timezone
        tz = pytz.timezone('America/Bogota')
        try:
            fecha_inicio_dt = make_aware(datetime.combine(
                datetime.strptime(fecha_inicio_str, "%Y-%m-%d"), time.min
            ), timezone=tz) if fecha_inicio_str else make_aware(datetime.combine(datetime.now(tz).date(), time.min), timezone=tz)

            fecha_fin_dt = make_aware(datetime.combine(
                datetime.strptime(fecha_fin_str, "%Y-%m-%d"), time.max
            ), timezone=tz) if fecha_fin_str else make_aware(datetime.combine(fecha_inicio_dt.date(), time.max), timezone=tz)
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

        # 🔍 Filtro compuesto usando Q
        filtros = Q(fecha_turno__range=(fecha_inicio_dt, fecha_fin_dt))
        
        if estado_id:
            try:
                estado_id = int(estado_id)
                if estado_id not in [1, 2, 3, 4]:
                    raise ValueError
            except ValueError:
                return Response({'error': 'estado_id no válido. Debe estar entre 1 y 4.'}, status=400)

            filtros &= Q(estado_id=estado_id)

            if estado_id == 1:
                filtros &= Q(atencion__isnull=True)
            else:
                filtros &= Q(atencion__id_ventanilla=ventanilla_id)

        # 📦 Consulta optimizada con relaciones cargadas
        turnos = Turno.objects.select_related(
            'id_usuario', 'estado', 'tipo_turno', 'tipo_tramite'
        ).prefetch_related(
            'atencion__id_funcionario__user',
            'atencion__id_ventanilla'
        ).filter(filtros).order_by('fecha_turno')

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

        filtros = Q()
        if turno:
            filtros &= Q(turno__icontains=turno)

        if fecha_turno:
            fecha = parse_date(fecha_turno)
            if not fecha:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
            filtros &= Q(fecha_turno__date=fecha)

        turnos = Turno.objects.select_related('tipo_tramite', 'tipo_turno', 'estado', 'id_usuario').filter(filtros).order_by('fecha_turno')

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

        turnos = Turno.objects.select_related(
            'tipo_tramite', 'tipo_turno', 'estado', 'id_usuario'
        ).filter(id_usuario__cedula=documento).order_by('fecha_turno')

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
        estado_id = request.GET.get('estado_id')
        tipo_tramite_id = request.GET.get('tipo_tramite_id')

        turnos = Turno.objects.select_related(
            'tipo_tramite', 'tipo_turno', 'estado', 'id_usuario'
        )

        if estado_id:
            try:
                estado_id = int(estado_id)
                if estado_id not in [1, 2, 3, 4]:
                    return Response({'error': 'Estado no válido. Valores permitidos: 1, 2, 3, 4.'}, status=400)
                turnos = turnos.filter(estado_id=estado_id)
            except (TypeError, ValueError):
                return Response({'error': 'Debe proporcionar un estado_id válido (int).'}, status=400)

        if tipo_tramite_id:
            try:
                tipo_tramite_id = int(tipo_tramite_id)
                turnos = turnos.filter(tipo_tramite_id=tipo_tramite_id)
            except ValueError:
                return Response({'error': 'tipo_tramite_id debe ser un número entero.'}, status=400)

        turnos = turnos.order_by('-fecha_turno')
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
        cedula = request.query_params.get('cedula', '').strip()

        if not cedula:
            return Response({'success': False, 'message': 'Debe proporcionar una cédula.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            usuario = Usuario.objects.get(cedula=cedula)
        except Usuario.DoesNotExist:
            return Response({'success': False, 'message': 'No se encontró ningún usuario con la cédula proporcionada.'}, status=status.HTTP_404_NOT_FOUND)

        # Validar si el usuario tiene un turno en los últimos 2 minutos
        hace_dos_min = now() - timedelta(minutes=2)
        turno_reciente = Turno.objects.filter(
            id_usuario=usuario.id,
            fecha_turno__gte=hace_dos_min
        ).exists()

        # Respuesta con advertencia si aplica
        response_data = {
            'success': True,
            'message': 'Usuario encontrado exitosamente.',
            'data': self.get_serializer(usuario).data
        }

        if turno_reciente:
            response_data['warning'] = 'Este usuario ya tiene un turno generado en los últimos 2 minutos. Espere un momento antes de solicitar otro.'

        return Response(response_data, status=status.HTTP_200_OK)

class AtencionViewSet(viewsets.ModelViewSet):
    queryset = Atencion.objects.all()
    serializer_class = AtencionSerializer
    permission_classes = [IsAuthenticated]

    # AGREGAMOS QUE PARA EL ENDPOINT DE ULTIMAS 6, SEA ALLOWANY
    def get_permissions(self):
        if self.action == 'ultimas_6':
            return [AllowAny()]
        return super().get_permissions()

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
            atenciones = (
                Atencion.objects.filter(fecha_atencion__date=hoy)
                .select_related('id_turno__id_usuario', 'id_turno__estado', 'id_ventanilla')
                .order_by('-fecha_atencion')[:6]
            )

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
@extend_schema_view(
    get=extend_schema(
        responses=UsuarioAutenticadoSerializer
    )
)
class UsuarioActualView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UsuarioAutenticadoSerializer(request.user)
        return Response(serializer.data)

class BaseListView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = None  # Obligatorio redefinir
    queryset = None

    def list(self, request, *args, **kwargs):
        try:
            return handle_custom_exception(
                self.get_queryset(),
                self.serializer_class,
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

# CREAR VISTA PARA LISTAR TIPO DE TRAMITES
class TipoTramiteListView(BaseListView):
    serializer_class = TipoTramiteSerializer
    queryset = TipoTramite.objects.all()

# CREAR VISTA PARA LISTAR LOS TIPOS DE TURNOS
class TipoTurnoListView(BaseListView):
    serializer_class = TipoTurnoSerializer
    queryset = TipoTurno.objects.all()

        
# ENDPOINTS PARA EL LOGEO Y FUNCIONES GENERALES DEL USUARIO INTERNO
# 0 Utilizar endpoint de TOKEN y posterior el de usuario actual
# 1 LISTAR VENTANILLAS CON ESTADO
@extend_schema(
    responses=VentanillaSerializer(many=True),
    tags=["Ventanillas"]
)
class VentanillaListView(ListAPIView):
    queryset = Ventanilla.objects.all()
    serializer_class = VentanillaSerializer
    permission_classes = [AllowAny]

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
        data = request.data
        funcionario_id = data.get("funcionario_id")
        ventanilla_id = data.get("ventanilla_id")
        confirmar = data.get("confirmar", False)

        # Validación de existencia del funcionario y la ventanilla:
        if not funcionario_id or not ventanilla_id:
            raise ValidationError({
                "funcionario_id": "Este campo es obligatorio.",
                "ventanilla_id": "Este campo es obligatorio."
            })

        funcionario = get_object_or_404(Funcionario, id=funcionario_id)
        ventanilla = get_object_or_404(Ventanilla, id=ventanilla_id)

        # Validación de ocupación de la ventanilla
        if ventanilla.estado.nombre == "Ocupada" and not confirmar:
            raise ConflictError({
                "message": "La ventanilla está actualmente ocupada. Debe confirmar si desea continuar.",
                "require_confirm": True
            })

        # Obtener token del usuario autenticado  Obtener token JWT desde el header
        auth_header = request.headers.get('Authorization', '')
        token_value = auth_header.split(' ')[1] if auth_header.startswith('Bearer ') else None

        # Asignación del puesto con token
        puesto = Puesto.objects.create(
            id_funcionario=funcionario,
            id_ventanilla=ventanilla,
            token=token_value
        )

        # Cambio de estado de la ventanilla
        estado_ocupada = EstadoVentanilla.objects.filter(nombre="Ocupada").first()
        if not estado_ocupada:
            raise APIException("El estado 'Ocupada' no está definido en el sistema.")
        
        ventanilla.estado = estado_ocupada
        ventanilla.save()

        return Response({
            "success": True,
            "message": "Ventanilla asignada correctamente.",
            "puesto_id": puesto.id,
            "token": token_value
        }, status=status.HTTP_201_CREATED)
    
# ENDPOINT PARA ATENDER TURNO. FUNCIONARIO - TOKEN - PUESTO
@extend_schema(
    methods=["POST"],
    request=None,
    responses={
        200: FinalizarTurnoResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
        403: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gestionar_turno(request):
    token_header = request.headers.get('Authorization', '')
    token = token_header.split(' ')[1] if token_header.startswith('Bearer ') else None
    #print(f"\n🔑 TOKEN RECIBIDO: {token}")
    
    if not token:
        return Response({"error": "Token requerido."}, status=400)

    try:
        UntypedToken(token)
    except AuthenticationFailed:
        return Response({"error": "Token inválido o expirado."}, status=401)

    # Obtener puesto activo
    puesto = Puesto.objects.select_related("id_funcionario", "id_ventanilla").filter(
        token=token, fecha_salida__isnull=True
    ).first()
    
    if not puesto:
        #print("❌ No se encontró puesto activo.")
        return Response({"error": "Token inválido o sesión terminada."}, status=401)

    funcionario = puesto.id_funcionario
    ventanilla = puesto.id_ventanilla
    #print(f"✅ FUNCIONARIO: {funcionario}, VENTANILLA: {ventanilla}")

    # --- FINALIZAR TURNO EN ATENCION ---
    atencion_activa = Atencion.objects.select_related("id_turno").filter(
        id_funcionario=funcionario,
        id_ventanilla=ventanilla,
        id_turno__estado__nombre="Atención"
    ).first()

    if atencion_activa:
        turno_activo = atencion_activa.id_turno
        #print(f"✔️ Finalizando turno en atención: {turno_activo.turno}")
        estado_finalizado = EstadoTurno.objects.get(nombre="Finalizado")
        turno_activo.estado = estado_finalizado
        turno_activo.save()
        atencion_activa.fecha_fin_atencion = timezone.now()
        atencion_activa.save()
    else:
        print("ℹ️ No había turno en atención para finalizar.")

    # --- BUSCAR TURNO MAS PRIORITARIO ---
    ahora = timezone.now()

    # ¿Hay ventanillas de productos en el sistema?
    existe_ventanilla_productos = Ventanilla.objects.filter(nombre__icontains='prod').exists()
    # ¿Es ventanilla de productos?
    es_ventanilla_productos = 'prod' in ventanilla.nombre.lower()

    #print(f"🧭 Existen ventanillas de productos: {existe_ventanilla_productos}")
    #print(f"🔎 Ventanilla actual '{ventanilla.nombre}' es de productos: {es_ventanilla_productos}")

    # Filtrar turnos disponibles
    turnos_disponibles = Turno.objects.select_related("tipo_tramite", "estado").filter(
        estado__nombre="Espera"
    )

    # Aplicar lógica según existencia de ventanillas de productos
    if existe_ventanilla_productos:
        # Si existen ventanillas de productos, filtrar turnos por letra según tipo de ventanilla
        if es_ventanilla_productos:
            turnos_disponibles = turnos_disponibles.filter(turno__istartswith='E')
        else:
            turnos_disponibles = turnos_disponibles.exclude(turno__istartswith='E')

# Si no hay turnos aplicables, retornar error
    if not turnos_disponibles.exists():
        #print("❌ No hay turnos disponibles en espera (tras filtrar por ventanilla).")
        return Response({"error": "No hay turnos disponibles para atender."}, status=400)

    # Ordenar por urgencia
    def calcular_porcentaje(turno):
        """
        Calcula el porcentaje de agotamiento del tiempo estimado para un turno.
        Cuanto más alto el porcentaje, más tiempo ha pasado desde que se generó el turno.

        :param fecha_turno: datetime de cuando se generó el turno
        :param tiempo_estimado_minutos: duración máxima estimada del turno (en minutos)
        :param ahora: datetime actual
        :return: porcentaje (float entre 0 y 1) — mayor = más próximo a agotarse
        """    
        # Obtener tiempo estimado según tipo de turno
        if turno.tipo_turno.nombre.lower() == 'prioritario' or turno.tipo_turno.id == 1:
            tiempo_estimado = 15
        elif turno.tipo_turno.nombre.lower() == 'general' or turno.tipo_turno.id == 2:
            tiempo_estimado = turno.tipo_tramite.tiempo_espera
        else:
            tiempo_estimado = 25  # Valor por defecto de seguridad

        transcurrido = (ahora - turno.fecha_turno).total_seconds() / 60  # en minutos

        porcentaje = transcurrido / tiempo_estimado if tiempo_estimado != 0 else 1

        #print(
        #    f"📌 Turno {turno.turno} | Tipo turno: {turno.tipo_turno.nombre} | "
        #    f"Trámite: {turno.tipo_tramite.nombre} | "
        #    f"Fecha turno: {turno.fecha_turno.strftime('%H:%M:%S')} | "
        #    f"Transcurrido: {transcurrido:.2f} min | "
        #    f"Estimado: {tiempo_estimado} min | "
        #    f"Prioridad (%): {porcentaje:.2f}"
        #)

        return porcentaje

    # Ordenar los turnos
    turnos_ordenados = sorted(turnos_disponibles, key=calcular_porcentaje, reverse=True)
    
    turno_prioritario = turnos_ordenados[0]
    #print(f"🎯 Turno seleccionado para atención: {turno_prioritario.turno}")

    # Cambiar estado a "Atención"
    estado_atencion = EstadoTurno.objects.get(nombre="Atención")
    turno_prioritario.estado = estado_atencion
    turno_prioritario.save()

    nueva_atencion = Atencion.objects.create(
        id_funcionario=funcionario,
        id_turno=turno_prioritario,
        id_ventanilla=ventanilla,
        fecha_atencion=ahora
    )

    return Response({
        "message": "Turno finalizado (si existía uno) y nuevo turno atendido.",
        "turno_id": turno_prioritario.id,
        "turno_codigo": turno_prioritario.turno,
        "atencion_id": nueva_atencion.id
    })

#ENDPOINT DE LOGOUT

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=LogoutSerializer,
        responses={200: None, 400: None, 500: None},
        summary="Cerrar sesión",
        description="Recibe el token de refresh en el body para cerrar sesión e invalidar el token.",
    )
    def post(self, request):
        # 1. Invalidar Refresh Token
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data['refresh']
        try:
            token = RefreshToken(refresh_token)
            jti = token['jti']
            outstanding_token = OutstandingToken.objects.filter(jti=jti).first()
            
            if not outstanding_token:
                return Response({"error": "Token no encontrado."}, status=400)
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
        except TokenError:
            return Response({"error": "Refresh token inválido."}, status=400)
        
        #  Paso 2: Cerrar sesión (acceso) y liberar ventanilla
        access_header = request.headers.get('Authorization', '')
        access_token = access_header.split(' ')[1] if access_header.startswith("Bearer ") else None
        if not access_token:
            return Response({"error": "Access token requerido."}, status=400)

        try:
            UntypedToken(access_token)
        except AuthenticationFailed:
            return Response({"error": "Access token inválido."}, status=401)
        
        # Buscar puesto activo con ese access token
        # Paso 3: Obtener el puesto activo del funcionario
        puesto = Puesto.objects.filter(token=access_token, fecha_salida__isnull=True).first()
        if puesto:
            funcionario = puesto.id_funcionario
            ventanilla = puesto.id_ventanilla

            print(f"🔍 Verificando atenciones activas para funcionario: {funcionario} y ventanilla: {ventanilla}")

            # Paso 4: Finalizar turnos en atención activos antes de cerrar sesión
            atenciones_activas = Atencion.objects.select_related("id_turno").filter(
                id_funcionario=funcionario,
                id_ventanilla=ventanilla,
                fecha_fin_atencion__isnull=True
            )

            estado_finalizado = EstadoTurno.objects.get(id=3)  # También puedes usar nombre="Finalizado"

            for atencion in atenciones_activas:
                atencion.fecha_fin_atencion = timezone.now()
                atencion.save()

                turno = atencion.id_turno
                turno.estado = estado_finalizado
                turno.save()

                print(f"✅ Turno {turno.turno} finalizado automáticamente en logout.")

            # Paso 5: Cerrar puesto (liberar ventanilla)
            puesto.fecha_salida = timezone.now()
            puesto.token = None
            puesto.save()

            try:
                estado_libre = EstadoVentanilla.objects.get(nombre="Libre")
                ventanilla.estado = estado_libre
                ventanilla.save()
            except EstadoVentanilla.DoesNotExist:
                return Response({"error": "Estado 'Libre' no definido."}, status=500)

        return Response({"message": "Sesión cerrada correctamente."})
    
# ENDPOINT CON ESTADISTICAS USUARIO VENTANILLA: CANTIDAD DIA, HISTORICO TURNOS ATENDIDOS. TIEMPO PROMEDIO ATENCION POR TURNO, DIA HISTORICO.
@extend_schema(
    responses=EstadisticasFuncionarioSerializer,
    tags=["Estadísticas"]
)
class EstadisticasFuncionarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Verificar si es funcionario
        try:
            funcionario = Funcionario.objects.get(user=request.user)
        except Funcionario.DoesNotExist:
            return Response({'detail': 'El usuario no es un funcionario válido'}, status=403)

        hoy = localtime(now()).date()

        # Atenciones del día de hoy para este funcionario
        atenciones_hoy = Atencion.objects.filter(
            id_funcionario=funcionario,
            fecha_atencion__date=hoy,
            fecha_fin_atencion__isnull=False
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_fin_atencion') - F('fecha_atencion'),
                output_field=DurationField()
            )
        )

        # Conteo de trámites atendidos hoy
        total_tramites_hoy = atenciones_hoy.count()

        # Tiempo promedio de atención hoy (en minutos)
        tiempo_promedio_hoy = atenciones_hoy.aggregate(
            promedio=Avg('duracion')
        )['promedio']
        tiempo_promedio_hoy_min = round(tiempo_promedio_hoy.total_seconds() / 60, 2) if tiempo_promedio_hoy else 0

        # Atenciones pasadas (anteriores a hoy)
        atenciones_pasadas = Atencion.objects.filter(
            id_funcionario=funcionario,
            fecha_atencion__date__lt=hoy,
            fecha_fin_atencion__isnull=False
        ).annotate(
            dia=TruncDate('fecha_atencion'),
            duracion=ExpressionWrapper(
                F('fecha_fin_atencion') - F('fecha_atencion'),
                output_field=DurationField()
            )
        )

        # Promedio de trámites por día (anteriores)
        tramites_por_dia = atenciones_pasadas.values('dia').annotate(total=Count('id'))
        total_dias = tramites_por_dia.count()
        total_tramites_anteriores = sum(item['total'] for item in tramites_por_dia)
        promedio_tramites_por_dia = round(total_tramites_anteriores / total_dias, 2) if total_dias else 0

        # Tiempo promedio de atención por día en días anteriores
        tiempo_promedio_anteriores = atenciones_pasadas.aggregate(
            promedio=Avg('duracion')
        )['promedio']
        tiempo_promedio_anteriores_min = round(tiempo_promedio_anteriores.total_seconds() / 60, 2) if tiempo_promedio_anteriores else 0

        return Response({
            'Conteo_Tramites_Hoy': total_tramites_hoy,
            'Promedio_Tramites_Dia_Historico': promedio_tramites_por_dia,
            'Tiempo_Promedio_Atencion_Dia': tiempo_promedio_hoy_min,
            'Tiempo_Promedio_Atencion_Historico': tiempo_promedio_anteriores_min
        })

# ENDPOINT PARA CANCELAR TURNOS, SI EL TURNO NO ESTA EN ATENCION, PUEDE CANCELARLO CUALQUIER FUNCIONARIO, EN CASO DE QUE SE ENCUENTRE EN ATENCION UNICAMENTE LO PUEDE CANCELAR EL FUNCIONARIO QUE LO SOLICITO
class CancelarTurnoView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: FinalizarTurnoResponseSerializer,
            400: ErrorResponseSerializer,
            401: ErrorResponseSerializer,
            403: ErrorResponseSerializer,
        },
        request=None,
        parameters=[OpenApiParameter(name='turno_id', location=OpenApiParameter.PATH, required=True, type=int)]
    )
    def post(self, request, turno_id):
        token = request.headers.get('Authorization')
        if not token:
            return Response({"error": "Token requerido."}, status=400)

        try:
            token = token.split(' ')[1]
            UntypedToken(token)
        except (IndexError, AuthenticationFailed):
            return Response({"error": "Token inválido o expirado."}, status=401)

        puesto = Puesto.objects.select_related("id_funcionario").filter(token=token, fecha_salida__isnull=True).first()
        if not puesto:
            return Response({"error": "Token inválido o sesión terminada."}, status=401)

        funcionario = puesto.id_funcionario
        turno = get_object_or_404(Turno.objects.select_related("estado"), id=turno_id)
        atencion = None

        if turno.estado.nombre == "Espera":
            pass
        elif turno.estado.nombre == "Atención":
            atencion = Atencion.objects.filter(id_turno=turno, id_funcionario=funcionario).first()
            if not atencion:
                return Response({"error": "No tiene permiso para cancelar este turno en atención."}, status=403)
        else:
            return Response({"error": f"No se puede cancelar un turno en estado '{turno.estado.nombre}'."}, status=400)

        estado_cancelado = get_object_or_404(EstadoTurno, nombre="Cancelado")
        turno.estado = estado_cancelado
        turno.save()

        if atencion:
            atencion.fecha_fin_atencion = timezone.now()
            atencion.save()

        return Response({"message": "Turno cancelado correctamente."}, status=200)
    # ENDPOINTS PARA EL MODULO DE ESTADISTICAS

# 1 TURNOS POR ESTADO EN UN RANGO DE FECHA PARA EL FUNCIONARIO
@extend_schema(
    summary="Cantidad de turnos por estado atendidos por funcionario",
    parameters=[
        OpenApiParameter(name='inicio', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True)
    ],
    responses=EstadisticaLabelValorSerializer(many=True),
    tags=["Estadísticas"]
)
class TurnosPorEstadoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha_inicio = request.GET.get("inicio")
        fecha_fin = request.GET.get("fin")
        user = request.user

        try:
            inicio = make_aware(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
            fin = make_aware(datetime.strptime(fecha_fin, "%Y-%m-%d")) + timedelta(days=1)
        except Exception as e:
            #print(f"❌ Error en fecha: {e}")
            return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, status=400)

        try:
            funcionario = Funcionario.objects.get(user=user)
            #print(f"👤 Funcionario: {funcionario} (ID: {funcionario.id})")
        except Funcionario.DoesNotExist:
            #print("❌ No se encontró un funcionario vinculado al usuario")
            return Response({'detail': 'El usuario no es un funcionario válido'}, status=403)

        # Obtener atenciones según grupo
        if user.groups.filter(name="Supervisores").exists():
            #print("🧭 Usuario es SUPERVISOR: verá todas las atenciones en el rango")
            atenciones = Atencion.objects.filter(fecha_atencion__range=(inicio, fin))
        elif user.groups.filter(name="Ventanillas").exists():
            #print("🧭 Usuario es FUNCIONARIO VENTANILLA: verá solo sus atenciones")
            atenciones = Atencion.objects.filter(id_funcionario=funcionario, fecha_atencion__range=(inicio, fin))
        else:
            #print("❌ Usuario no tiene permisos")
            return Response({"error": "Usuario no autorizado"}, status=403)

        total_atenciones = atenciones.count()
        #print(f"📌 Total atenciones encontradas: {total_atenciones}")

        if total_atenciones == 0:
            #print("⚠️ No se encontraron atenciones en el rango indicado")
            return Response([])

        # Agrupar por estado de turno
        atenciones = atenciones.select_related("id_turno__estado")
        data = atenciones.values("id_turno__estado__nombre").annotate(total=Count("id"))
        #print(f"📊 Conteo por estado: {list(data)}")

        resultado = [{"label": x["id_turno__estado__nombre"], "value": x["total"]} for x in data]

        return Response(resultado)
    
# 2 ESTADISITICAS TURNOS POR HORA O POR DIA EN UN RANGO DE FECHA. VERIFICAR SI CUMPLE CON LA NECESIDAD, AMBIGUO
@extend_schema(
    summary="Cantidad de turnos por hora o día",
    parameters=[
        OpenApiParameter(name='inicio', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='tipo', type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False, description="Agrupación: 'hora' o 'dia'")
    ],
    responses=EstadisticaLabelValorSerializer(many=True),
    tags=["Estadísticas"]
)
class TurnosPorHoraDiaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha_inicio = request.GET.get("inicio")
        fecha_fin = request.GET.get("fin")
        agrupacion = request.GET.get("tipo", "dia")
        user = request.user

        try:
            inicio = make_aware(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
            fin = make_aware(datetime.strptime(fecha_fin, "%Y-%m-%d")) + timedelta(days=1)
        except:
            return Response({"error": "Formato de fecha inválido."}, status=400)

        queryset = Turno.objects.filter(fecha_turno__range=(inicio, fin))

        if user.groups.filter(name="Ventanillas").exists():
            funcionario = Funcionario.objects.get(user=user)
            queryset = queryset.filter(atencion__id_funcionario=funcionario)
        elif not user.groups.filter(name="Supervisores").exists():
            return Response({"error": "Usuario no autorizado"}, status=403)

        if agrupacion == "hora":
            from django.db.models.functions import ExtractHour
            data = queryset.annotate(hora=ExtractHour("fecha_turno")).values("hora").annotate(total=Count("id"))
            resultado = [{"label": f"{x['hora']}:00", "value": x["total"]} for x in data]
        else:
            from django.db.models.functions import TruncDate
            data = queryset.annotate(dia=TruncDate("fecha_turno")).values("dia").annotate(total=Count("id"))
            resultado = [{"label": x["dia"].strftime("%Y-%m-%d"), "value": x["total"]} for x in data]

        return Response(resultado)
    
# 3 TURNOS POR TIPO DE TRAMITE (BARRAS)
@extend_schema(
    summary="Cantidad de turnos por tipo de trámite",
    parameters=[
        OpenApiParameter(name='inicio', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True)
    ],
    responses=EstadisticaLabelValorSerializer(many=True),
    tags=["Estadísticas"]
)
class TurnosPorTramiteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha_inicio = request.GET.get("inicio")
        fecha_fin = request.GET.get("fin")
        user = request.user

        try:
            inicio = make_aware(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
            fin = make_aware(datetime.strptime(fecha_fin, "%Y-%m-%d")) + timedelta(days=1)
        except:
            return Response({"error": "Formato de fecha inválido."}, status=400)

        queryset = Turno.objects.filter(fecha_turno__range=(inicio, fin))

        if user.groups.filter(name="Ventanillas").exists():
            funcionario = Funcionario.objects.get(user=user)
            queryset = queryset.filter(atencion__id_funcionario=funcionario)
        elif not user.groups.filter(name="Supervisores").exists():
            return Response({"error": "Usuario no autorizado"}, status=403)

        data = queryset.values("tipo_tramite__nombre").annotate(total=Count("id"))
        resultado = [{"label": x["tipo_tramite__nombre"], "value": x["total"]} for x in data]
        return Response(resultado)
    
#4 TIEMPO PROMEDIO DE ATENCION POR TRAMITE
@extend_schema(
    summary="Tiempo promedio de atención por tipo de trámite",
    parameters=[
        OpenApiParameter(name='inicio', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True)
    ],
    responses=EstadisticaLabelValorSerializer(many=True),
    tags=["Estadísticas"]
)
class PromedioAtencionPorTramiteView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha_inicio = request.GET.get("inicio")
        fecha_fin = request.GET.get("fin")
        user = request.user

        try:
            inicio = make_aware(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
            fin = make_aware(datetime.strptime(fecha_fin, "%Y-%m-%d")) + timedelta(days=1)
        except:
            return Response({"error": "Formato de fecha inválido."}, status=400)

        queryset = Atencion.objects.filter(
            fecha_atencion__range=(inicio, fin),
            fecha_fin_atencion__isnull=False
        ).annotate(
            duracion=ExpressionWrapper(F('fecha_fin_atencion') - F('fecha_atencion'), output_field=DurationField())
        )

        if user.groups.filter(name="Ventanillas").exists():
            funcionario = Funcionario.objects.get(user=user)
            queryset = queryset.filter(id_funcionario=funcionario)
        elif not user.groups.filter(name="Supervisores").exists():
            return Response({"error": "Usuario no autorizado"}, status=403)

        data = queryset.values("id_turno__tipo_tramite__nombre").annotate(promedio=Avg("duracion"))
        resultado = [
            {"label": x["id_turno__tipo_tramite__nombre"], "value": round(x["promedio"].total_seconds() / 60, 2)}
            for x in data if x["promedio"]
        ]
        return Response(resultado)
    
# 5 TOTALES; CANTIDAD DE TURNOS Y PROMEDIO DE ATENCION, CANTIDA DE GENERALES Y CANTIDAD DE PRIORITARIOS
@extend_schema(
    summary="Totales: cantidad de turnos y tiempo promedio",
    parameters=[
        OpenApiParameter(name='inicio', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True),
        OpenApiParameter(name='fin', type=OpenApiTypes.DATE, location=OpenApiParameter.QUERY, required=True)
    ],
    responses=OpenApiTypes.OBJECT,
    tags=["Estadísticas"]
)
class TotalesGeneralesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fecha_inicio = request.GET.get("inicio")
        fecha_fin = request.GET.get("fin")
        user = request.user

        #print(f" Usuario autenticado: {user.username}")
        #print(f" Rango de fechas recibido: {fecha_inicio} a {fecha_fin}")

        try:
            inicio = make_aware(datetime.strptime(fecha_inicio, "%Y-%m-%d"))
            fin = make_aware(datetime.strptime(fecha_fin, "%Y-%m-%d")) + timedelta(days=1)
        except Exception as e:
            #print(f"❌ Error en fechas: {e}")
            return Response({"error": "Formato de fecha inválido."}, status=400)

        queryset = Atencion.objects.filter(
            fecha_atencion__range=(inicio, fin),
            fecha_fin_atencion__isnull=False
        ).annotate(
            duracion=ExpressionWrapper(
                F('fecha_fin_atencion') - F('fecha_atencion'),
                output_field=DurationField()
            )
        )

        if user.groups.filter(name="Ventanillas").exists():
            funcionario = Funcionario.objects.get(user=user)
            queryset = queryset.filter(id_funcionario=funcionario)
            #print(f" Funcionario filtrado: {funcionario}")
        elif not user.groups.filter(name="Supervisores").exists():
            return Response({"error": "Usuario no autorizado"}, status=403)

        total_turnos = queryset.count()
        promedio_tiempo = queryset.aggregate(prom=Avg("duracion"))["prom"]
        promedio_minutos = round(promedio_tiempo.total_seconds() / 60, 2) if promedio_tiempo else 0

        # ✅ Contar los tipos de turno por nombre
        total_prioritarios = queryset.filter(id_turno__tipo_turno__nombre__iexact="Prioritario").count()
        total_generales = queryset.filter(id_turno__tipo_turno__nombre__iexact="General").count()

        #print(f" Total turnos atendidos: {total_turnos}")
        #print(f" Promedio de tiempo: {promedio_minutos} minutos")
        #print(f" Total prioritarios: {total_prioritarios}")
        #print(f" Total generales: {total_generales}")

        return Response({
            "total_turnos": total_turnos,
            "promedio_tiempo_min": promedio_minutos,
            "total_prioritarios": total_prioritarios,
            "total_generales": total_generales
        })