from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = ['name', 'workspace', 'status', 'visibility', 'lead', 'created_at']
    list_filter   = ['status', 'visibility']
    search_fields = ['name', 'workspace__name']