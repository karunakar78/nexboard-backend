from django.contrib import admin
from .models import Workspace, WorkspaceMember, WorkspaceInvite


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display  = ['name', 'slug', 'owner', 'created_at']
    search_fields = ['name', 'owner__email']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display  = ['workspace', 'user', 'role', 'created_at']
    list_filter   = ['role']


@admin.register(WorkspaceInvite)
class WorkspaceInviteAdmin(admin.ModelAdmin):
    list_display  = ['workspace', 'email', 'role', 'status', 'expires_at']
    list_filter   = ['status']