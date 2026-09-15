from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "pos_x", "pos_y", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "text")
