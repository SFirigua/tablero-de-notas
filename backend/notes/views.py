"""
Capa de views de notas: CRUD + métricas internas.
"""
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsActiveUser, IsAdminRole

from . import permissions as note_permissions
from . import services
from .models import Note
from .serializers import NoteSerializer


class NoteViewSet(viewsets.ModelViewSet):
    """
    CRUD de notas para ADMIN y USER activos (IsAdminOrActiveUser).

    - GET    /api/notes/        lista
    - POST   /api/notes/        crear
    - GET    /api/notes/<id>/   detalle
    - PATCH  /api/notes/<id>/   actualización parcial
      (title, text, status, pos_x, pos_y)
    - DELETE /api/notes/<id>/   eliminar

    PUT deshabilitado (edición siempre parcial vía PATCH).
    """

    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    permission_classes = [IsActiveUser, note_permissions.IsAdminOrActiveUser]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


class NotesStatusMetricsView(APIView):
    """
    GET /api/internal/notes-status/ -> {"pending": X, "in_progress": Y, "done": Z}

    Protegido: requiere JWT de usuario ADMIN. Pensado para consumo interno
    (dashboards/otros servicios de la demo); no está expuesto al tablero.
    """

    permission_classes = [IsActiveUser, IsAdminRole]

    def get(self, request):
        return Response(services.status_counts())
