from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet, VentanillaViewSet, TurnoViewSet, UsuarioViewSet, AtencionViewSet, PuestoViewSet, UsuarioActualView, TipoTramiteListView, TipoTurnoListView, VentanillaListView, AsignarVentanillaView, gestionar_turno, LogoutView, EstadisticasFuncionarioView, CancelarTurnoView, TurnosPorEstadoView, TurnosPorHoraDiaView, TurnosPorTramiteView, PromedioAtencionPorTramiteView, TotalesGeneralesView, ListaFuncionariosVentanillaView

# Config de las rutas de la API
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
    path('gestionar-turno/', gestionar_turno, name='gestionar_turno'),path("logout/", LogoutView.as_view(), name="logout"),
    path('estadisticas-funcionario/', EstadisticasFuncionarioView.as_view(), name='estadisticas_funcionario'),
    path('cancelar-turno/<int:turno_id>/', CancelarTurnoView.as_view(), name='cancelar_turno'),
    path("estadisticas/por-estado/", TurnosPorEstadoView.as_view()),
    path("estadisticas/por-tiempo/", TurnosPorHoraDiaView.as_view()),
    path("estadisticas/por-tramite/", TurnosPorTramiteView.as_view()),
    path("estadisticas/atencion-por-tramite/", PromedioAtencionPorTramiteView.as_view()),
    path("estadisticas/totales/", TotalesGeneralesView.as_view()),
    path('funcionarios-por-rol/ventanillas/', ListaFuncionariosVentanillaView.as_view(), name='lista-funcionarios-ventanilla'),
]