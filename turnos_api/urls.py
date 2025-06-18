from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet, VentanillaViewSet, TurnoViewSet, UsuarioViewSet, AtencionViewSet, PuestoViewSet, UsuarioActualView, TipoTramiteListView, TipoTurnoListView, VentanillaListView, AsignarVentanillaView, atender_turno, finalizar_turno, LogoutView, EstadisticasFuncionarioView, cancelar_turno, TurnosPorEstadoView, TurnosPorHoraDiaView, TurnosPorTramiteView, PromedioAtencionPorTramiteView, TotalesGeneralesView

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
    path('finalizar-turno/<int:turno_id>/', finalizar_turno, name='finalizar_turno'),
    path("logout/", LogoutView.as_view(), name="logout"),
    path('estadisticas-funcionario/', EstadisticasFuncionarioView.as_view(), name='estadisticas_funcionario'),
    path('cancelar-turno/<int:turno_id>/', cancelar_turno, name='cancelar_turno'),
    path("estadisticas/por-estado/", TurnosPorEstadoView.as_view()),
    path("estadisticas/por-tiempo/", TurnosPorHoraDiaView.as_view()),
    path("estadisticas/por-tramite/", TurnosPorTramiteView.as_view()),
    path("estadisticas/atencion-por-tramite/", PromedioAtencionPorTramiteView.as_view()),
    path("estadisticas/totales/", TotalesGeneralesView.as_view()),
]