from django.db import models


class Note(models.Model):
    """Nota del tablero: posición entera sobre el canvas y estado kanban."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En Progreso"
        DONE = "DONE", "Hecha"

    title = models.CharField("título", max_length=200)
    text = models.TextField("texto", blank=True)
    status = models.CharField(
        "estado",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    pos_x = models.IntegerField("posición X", default=0)
    pos_y = models.IntegerField("posición Y", default=0)
    created_at = models.DateTimeField("creada", auto_now_add=True)
    updated_at = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "nota"
        verbose_name_plural = "notas"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"
