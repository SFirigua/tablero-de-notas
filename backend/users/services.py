"""
Capa de servicios: reglas de negocio de usuarios.
Los serializers/views delegan aquí; la lógica no vive en las views.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


def create_user(*, email, name, password, role=None):
    """
    Crea un usuario con la contraseña inicial provista por el admin.

    El usuario puede iniciar sesión inmediatamente con esas credenciales
    (set_password se aplica dentro del UserManager).
    """
    extra = {"name": name}
    if role:
        extra["role"] = role
    return User.objects.create_user(email=email, password=password, **extra)


def update_user(user, data):
    """
    Aplica cambios parciales a un usuario protegiendo la regla de negocio:

    - No se puede desactivar (is_active=False) ni cambiar de rol (de ADMIN
      a USER) al ÚLTIMO administrador ACTIVO del sistema.

    Violación -> django ValidationError, que el serializer traduce a 400.
    """
    new_is_active = data.get("is_active", user.is_active)
    new_role = data.get("role", user.role)

    is_last_active_admin = (
        user.role == User.Role.ADMIN
        and user.is_active
        and not User.objects.filter(
            role=User.Role.ADMIN, is_active=True
        )
        .exclude(pk=user.pk)
        .exists()
    )

    if is_last_active_admin:
        would_deactivate = new_is_active is False
        would_lose_role = new_role != User.Role.ADMIN
        actions = [
            label
            for label, triggered in (
                ("desactivar", would_deactivate),
                ("cambiar de rol", would_lose_role),
            )
            if triggered
        ]
        if actions:
            raise ValidationError(
                "No se puede "
                + " ni ".join(actions)
                + " al último administrador activo del sistema."
            )

    for field, value in data.items():
        setattr(user, field, value)
    user.save()
    return user
