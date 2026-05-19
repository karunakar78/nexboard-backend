from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import ChangePasswordView, LogoutView, ProfileView, RegisterView

from common.throttles import AuthRateThrottle
from rest_framework.throttling import AnonRateThrottle


class ThrottledTokenView(TokenObtainPairView):
    throttle_classes = [AuthRateThrottle]

urlpatterns = [
    path('token/', ThrottledTokenView.as_view(), name='auth-token'),
    path('register/',        RegisterView.as_view(),       name='auth-register'),
    path('token/',           TokenObtainPairView.as_view(), name='auth-token'),
    path('token/refresh/',   TokenRefreshView.as_view(),   name='auth-token-refresh'),
    path('logout/',          LogoutView.as_view(),         name='auth-logout'),
    path('profile/',         ProfileView.as_view(),        name='auth-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
]