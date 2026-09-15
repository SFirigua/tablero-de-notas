"""
Capa de views: delgado orquestamiento HTTP. La lógica vive en
serializers/services/permissions.
"""
import logging

from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import permissions as user_permissions
from . import serializers as user_serializers

User = get_user_model()
logger = logging.getLogger(__name__)


class UserTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/ -> {access, refresh, user}."""

    serializer_class = user_serializers.UserTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/auth/logout/.

    Con JWT sin estado, el logout es del lado CLIENTE: la app elimina los
    tokens almacenados (localStorage/memoria) y no los envía de nuevo.
    Este endpoint existe para cerrar el ciclo (auditoría/frontend) y no
    invalida el access token ya emitido: expira solo en 15 minutos.
    (Para revocación server-side real se usaría
    rest_framework_simplejwt.token_blacklist; fuera de alcance a propósito.)
    """

    permission_classes = [
        user_permissions.IsActiveUser,
    ]

    def post(self, request):
        if request.user.is_authenticated:
            logger.info("Logout de %s (invalidación del lado cliente).", request.user)
        return Response(
            {
                "detail": "Logout correcto. El cliente debe eliminar el "
                "access y el refresh token almacenados; el access token "
                "caduca automáticamente en 15 minutos."
            }
        )


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Gestión de usuarios, exclusiva del rol ADMIN.

    - GET    /api/users/        lista
    - POST   /api/users/        alta con contraseña inicial
    - GET    /api/users/<id>/   detalle
    - PATCH  /api/users/<id>/   actualización parcial

    Sin DELETE ni PUT (restricción del alcance + http_method_names).
    """

    queryset = User.objects.all()
    permission_classes = [
        user_permissions.IsActiveUser,
        user_permissions.IsAdminRole,
    ]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return user_serializers.UserCreateSerializer
        if self.action in ("partial_update", "update"):
            return user_serializers.UserUpdateSerializer
        return user_serializers.UserReadSerializer
