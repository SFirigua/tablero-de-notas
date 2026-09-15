"""
Capa de serializers: validación de entrada/salida; delegan reglas de
negocio a users.services.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from . import services

User = get_user_model()


class UserTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login JWT: devuelve access/refresh + resumen del usuario."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["name"] = user.name
        token["role"] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "name": self.user.name,
            "role": self.user.role,
        }
        return data


class UserReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "is_active", "is_staff")
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Alta de usuarios por el ADMIN. La contraseña inicial es obligatoria y
    queda activa para login inmediato (el usuario nace con is_active=True).
    """

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("id", "email", "name", "role", "password")
        read_only_fields = ("id",)
        extra_kwargs = {
            "role": {"required": False},
        }

    def create(self, validated_data):
        return services.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """PATCH parcial: email, name, role, is_active (nunca password)."""

    class Meta:
        model = User
        fields = ("email", "name", "role", "is_active")
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ese email ya está registrado.")
        return value

    def update(self, instance, validated_data):
        try:
            return services.update_user(instance, validated_data)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": exc.messages})
