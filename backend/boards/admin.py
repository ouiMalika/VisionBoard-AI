from django.contrib import admin
from .models import ClusterJob, Board, Image, Tag


@admin.register(ClusterJob)
class ClusterJobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "status", "board_name", "created_at")
    list_filter = ("status",)


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "board", "url")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
