from django.urls import path
from .views import MarkAllReadView, NotificationListView, UnreadCountView

urlpatterns = [
    path('',                 NotificationListView.as_view(), name='notification-list'),
    path('mark-all-read/',   MarkAllReadView.as_view(),      name='notification-mark-read'),
    path('unread-count/',    UnreadCountView.as_view(),      name='notification-unread-count'),
]