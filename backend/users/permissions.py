"""
Capa de permisos (Views -> Serializers -> Services/Permissions -> Models).
"""
from django.contrib.auth import get_user_model
from rest_framework import permissions
from rest_framework.exceptions import NotAuthenticated

User = get_user_model()


class IsActiveUser(permissions.BasePermission):
    """
    Gate global (DEFAULT_PERMISSION_CLASSES): cada petición debe traer un
    usuario autenticado y con is_active == True.

    - Sin credenciales / token inválido -> 401 (DRF NotAuthenticated por
      el propio JWTAuthentication).
    - Autenticado pero inactivo -> 401 inmediato vía NotAuthenticated
      (no 403), según requisito de la prueba técnica.
    """

    message = "Usuario inactivo o no autenticado."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            return False
        if not user.is_active:
            raise NotAuthenticated("Usuario inactivo.")
        return True


class IsAdminRole(permissions.BasePermission):
    """Acceso exclusivo para cuentas con rol ADMIN."""

    message = "Se requiere el rol ADMIN."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user
            and user.is_authenticated
            and user.role == User.Role.ADMIN
        )
