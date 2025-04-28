from rest_framework.response import Response
from rest_framework import status
from .exceptions import CustomAPIException

def handle_custom_exception(queryset, serializer_class, success_message, error_message):
    """
    Maneja excepciones para cualquier consulta a la base de datos.
    Lanza una CustomAPIException si no hay resultados.
    """
    if not queryset:
        raise CustomAPIException(error_message, status.HTTP_404_NOT_FOUND)
    
    # Instanciamos el serializer individual, no ListSerializer
    serializer = serializer_class(queryset, many=True)
    
    # Obtenemos el nombre del modelo desde el serializer
    model_name = serializer_class.Meta.model._meta.model_name
    
    return Response({
        "success": True,
        "data": {model_name + 's': serializer.data},
        "message": success_message
    }, status=status.HTTP_200_OK)

