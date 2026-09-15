"""
Capa de permisos de la app notes.
"""
from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()


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
