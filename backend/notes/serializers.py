from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = (
            "id",
            "title",
            "text",
            "status",
            "pos_x",
            "pos_y",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
