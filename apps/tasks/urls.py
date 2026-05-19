from django.urls import path
from .views import (
    ActivityLogListView, CommentListCreateView,
    LabelListCreateView, TaskDetailView, TaskListCreateView,
)

urlpatterns = [
    path('labels/',                          LabelListCreateView.as_view(),  name='label-list'),
    path('',                                 TaskListCreateView.as_view(),   name='task-list'),
    path('<uuid:pk>/',                       TaskDetailView.as_view(),       name='task-detail'),
    path('<uuid:task_id>/comments/',         CommentListCreateView.as_view(), name='comment-list'),
    path('<uuid:task_id>/activity/',         ActivityLogListView.as_view(),  name='activity-log'),
]