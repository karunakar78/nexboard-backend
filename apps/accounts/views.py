from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from common.throttles import AuthRateThrottle

from .serializers import ChangePasswordSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Open endpoint — no auth required.
    CreateAPIView handles POST only, runs serializer.is_valid(), calls save().
    """
    serializer_class    = RegisterSerializer
    permission_classes  = [permissions.AllowAny]
    throttle_classes = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Issue tokens immediately on registration so the client
        # doesn't need a separate login call
        refresh = RefreshToken.for_user(user)
        return Response({
            'status': 'success',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access':  str(refresh.access_token),
            },
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/  — fetch logged-in user's profile
    PATCH /api/auth/profile/ — partial update (name, avatar)
    RetrieveUpdateAPIView gives us GET + PUT + PATCH for free.
    We override get_object so users can only ever see their own profile.
    """
    serializer_class   = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names  = ['get', 'patch']   # disable full PUT

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'status': 'success', 'message': 'Password updated.'})


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token so it can't be used again.
    The access token expires naturally (60 min) — that's acceptable
    for stateless JWT. If you need instant access token revocation
    you'd need a Redis blocklist checked on every request.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'status': 'success', 'message': 'Logged out.'})
        except Exception:
            return Response(
                {'status': 'error', 'message': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )