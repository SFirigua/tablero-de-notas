"""
Seed de datos iniciales:

    python manage.py seed_data

Crea (de forma idempotente):
  - 1 Admin: admin@ejemplo.com / Admin123! (rol ADMIN, superusuario)
  - 1 Usuario normal: user@ejemplo.com / User123! (rol USER)
  - 3 notas en distintas posiciones (pos_x, pos_y) y estados
    (PENDING, IN_PROGRESS, DONE).
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from notes.models import Note

User = get_user_model()

USERS = [
    {
        "email": "admin@ejemplo.com",
        "name": "Admin",
        "password": "Admin123!",
        "role": User.Role.ADMIN,
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "email": "user@ejemplo.com",
        "name": "Usuario Demo",
        "password": "User123!",
        "role": User.Role.USER,
        "is_staff": False,
        "is_superuser": False,
    },
]

NOTES = [
    {
        "title": "Planificar sprint",
        "text": "Definir objetivos y capacidades del equipo para el primer sprint.",
        "pos_x": 80,
        "pos_y": 120,
        "status": Note.Status.PENDING,
    },
    {
        "title": "Diseñar drag & drop de notas",
        "text": "Implementar arrastre sobre el canvas actualizando pos_x / pos_y vía PATCH.",
        "pos_x": 360,
        "pos_y": 260,
        "status": Note.Status.IN_PROGRESS,
    },
    {
        "title": "Configurar docker-compose",
        "text": "Servicios db (PostgreSQL 15), backend (Django) y frontend (Nginx).",
        "pos_x": 640,
        "pos_y": 90,
        "status": Note.Status.DONE,
    },
]


class Command(BaseCommand):
    help = "Inserta usuarios y notas de ejemplo en la base de datos."

    def handle(self, *args, **options):
        # --- Usuarios --------------------------------------------- #
        for data in USERS:
            email = data["email"]
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "name": data["name"],
                    "role": data["role"],
                    "is_staff": data["is_staff"],
                    "is_superuser": data["is_superuser"],
                },
            )
            # Re-aplica la contraseña y flags para mantener el seed idempotente.
            user.set_password(data["password"])
            user.role = data["role"]
            user.is_staff = data["is_staff"]
            user.is_superuser = data["is_superuser"]
            user.is_active = True
            user.save()
            label = "admin" if data["role"] == User.Role.ADMIN else "usuario"
            action = "creado" if created else "actualizado"
            self.stdout.write(self.style.SUCCESS(f"[OK] {label} {email} {action}"))

        # --- Notas -------------------------------------------------- #
        for data in NOTES:
            note, created = Note.objects.get_or_create(
                title=data["title"],
                defaults=data,
            )
            action = "creada" if created else "ya existía"
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] nota '{note.title}' ({note.status}) en "
                    f"({note.pos_x}, {note.pos_y}) {action}"
                )
            )

        self.stdout.write(self.style.MIGRATE_HEADING("Seed completado."))
