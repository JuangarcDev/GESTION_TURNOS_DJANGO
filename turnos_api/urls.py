from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet, VentanillaViewSet, TurnoViewSet, UsuarioViewSet, AtencionViewSet, PuestoViewSet, UsuarioActualView, TipoTramiteListView, TipoTurnoListView, VentanillaListView, AsignarVentanillaView, atender_turno, finalizar_turno

# Configuración de las rutas de la API
router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet)
router.register(r'ventanillas', VentanillaViewSet)
router.register(r'turnos', TurnoViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'atenciones', AtencionViewSet)
router.register(r'puestos', PuestoViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('me/', UsuarioActualView.as_view(), name='usuario_actual'),
    path('tipos-tramite/', TipoTramiteListView.as_view(), name='tipo_tramite_list'),
    path('tipos-turno/', TipoTurnoListView.as_view(), name='tipo_turno_list'),
    path('lista-ventanillas-estado/', VentanillaListView.as_view(), name='vetanilla_list'),
    path('asignar-ventanilla-puesto/', AsignarVentanillaView.as_view(), name='asignar_ventanilla'),
    path('atender-turno/<int:turno_id>/', atender_turno, name='atender_turno'),
    path('finalizar-turno/', finalizar_turno, name='finalizar_turno'),
]