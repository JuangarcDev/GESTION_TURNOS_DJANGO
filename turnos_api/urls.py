from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet, VentanillaViewSet, TurnoViewSet

# Configuración de las rutas de la API
router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet)
router.register(r'ventanillas', VentanillaViewSet)
router.register(r'turnos', TurnoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]