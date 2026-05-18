from django.urls import path
from .views import (
    InviteMemberView,
    MemberListView,
    RemoveMemberView,
    UpdateMemberRoleView,
    WorkspaceDetailView,
    WorkspaceListCreateView,
)

urlpatterns = [
    path('',                                WorkspaceListCreateView.as_view(), name='workspace-list'),
    path('<uuid:pk>/',                      WorkspaceDetailView.as_view(),     name='workspace-detail'),
    path('<uuid:pk>/invite/',               InviteMemberView.as_view(),        name='workspace-invite'),
    path('<uuid:pk>/members/',              MemberListView.as_view(),          name='workspace-members'),
    path('<uuid:pk>/members/<uuid:user_id>/', UpdateMemberRoleView.as_view(),  name='workspace-member-role'),
    path('<uuid:pk>/members/<uuid:user_id>/remove/', RemoveMemberView.as_view(), name='workspace-member-remove'),
]