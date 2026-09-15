"""
Capa de servicios: lógica de dominio de las notas.
"""
from django.db.models import Count

from .models import Note


def status_counts():
    """Conteo de notas por estado para métricas internas."""
    rows = Note.objects.values("status").annotate(total=Count("id"))
    by_status = {row["status"]: row["total"] for row in rows}
    return {
        "pending": by_status.get(Note.Status.PENDING, 0),
        "in_progress": by_status.get(Note.Status.IN_PROGRESS, 0),
        "done": by_status.get(Note.Status.DONE, 0),
    }
