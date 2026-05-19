from django.urls import path
from .views import WorkspaceAnalyticsView

urlpatterns = [
    path('', WorkspaceAnalyticsView.as_view(), name='workspace-analytics'),
]