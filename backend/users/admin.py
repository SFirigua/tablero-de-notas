from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "name", "role", "is_active", "is_staff", "is_superuser")
    list_filter = ("role", "is_active")
    search_fields = ("email", "name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Perfil", {"fields": ("name", "role")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas importantes", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "role", "password1", "password2"),
            },
        ),
    )
