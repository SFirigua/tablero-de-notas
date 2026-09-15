from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NoteViewSet, NotesStatusMetricsView

router = DefaultRouter()
router.register("notes", NoteViewSet, basename="note")

internal_patterns = [
    path("notes-status/", NotesStatusMetricsView.as_view(), name="notes_status_metrics"),
]

urlpatterns = [
    path("internal/", include(internal_patterns)),
    path("", include(router.urls)),
]
