from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    """Manager para el usuario personalizado (USERNAME_FIELD = email)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.USER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("role") != User.Role.ADMIN:
            raise ValueError("El superusuario debe tener role=ADMIN.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Usuario del sistema. El email es único y se usa para autenticarse."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        USER = "USER", "Usuario"

    email = models.EmailField("correo electrónico", unique=True)
    name = models.CharField("nombre", max_length=150)
    role = models.CharField(
        "rol",
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    is_active = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("equipo", default=False)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    objects = UserManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.role})"
