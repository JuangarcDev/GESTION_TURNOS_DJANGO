from django.utils import timezone
from datetime import timedelta
from turnos_api.models import Puesto, EstadoVentanilla
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed

class SessionExpirationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith("Bearer "):
            try:
                token_str = auth_header.split(" ")[1]
                jwt_auth = JWTAuthentication()
                validated_token = jwt_auth.get_validated_token(token_str)

                puesto = Puesto.objects.filter(token=token_str, fecha_salida__isnull=True).first()

                if puesto:
                    tiempo_maximo = timedelta(minutes=720)
                    tiempo_sesion = timezone.now() - puesto.fecha_ingreso

                    if tiempo_sesion > tiempo_maximo:
                        puesto.fecha_salida = timezone.now()
                        puesto.token = None
                        puesto.save()

                        try:
                            estado_libre = EstadoVentanilla.objects.get(nombre="Libre")
                            ventanilla = puesto.id_ventanilla
                            ventanilla.estado = estado_libre
                            ventanilla.save()
                        except EstadoVentanilla.DoesNotExist:
                            pass

            except (InvalidToken, AuthenticationFailed, IndexError):
                pass
            except Exception as e:
                pass

        response = self.get_response(request)
        return response
