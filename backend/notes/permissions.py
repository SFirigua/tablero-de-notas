"""
Capa de permisos de la app notes.
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import constant_time_compare
from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated

User = get_user_model()

INTERNAL_TOKEN_HEADER = "X-Internal-Token"


def has_valid_internal_token(request):
    """Compara (en tiempo constante) la cabecera X-Internal-Token con el token configurado."""
    expected = getattr(settings, "INTERNAL_API_TOKEN", "")
    provided = request.headers.get(INTERNAL_TOKEN_HEADER, "")
    return bool(expected and provided and constant_time_compare(provided, expected))


class IsAdminOrActiveUser(permissions.BasePermission):
    """
    Las notas son accesibles para ADMIN y USER con cuenta activa.

    El control de "cuenta activa" lo hace además el gate global
    (users.permissions.IsActiveUser, que responde 401); este permiso
    restringe explícitamente el conjunto de roles permitidos.
    """

    message = "Se requiere un rol válido (ADMIN o USER)."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.is_active
            and user.role in (User.Role.ADMIN, User.Role.USER)
        )


class IsActiveUserOrInternalToken(permissions.BasePermission):
    """
    Métricas internas: JWT de usuario activo (dashboard) o token compartido
    server-to-server (Lambda -> backend) vía cabecera X-Internal-Token.

    - Sin JWT y sin token válido -> 401.
    - Autenticado pero inactivo -> 401 (mismo criterio que IsActiveUser).
    """

    message = "Usuario inactivo o no autenticado."

    def has_permission(self, request, view):
        if has_valid_internal_token(request):
            return True
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        if not user.is_active:
            raise NotAuthenticated("Usuario inactivo.")
        return True
