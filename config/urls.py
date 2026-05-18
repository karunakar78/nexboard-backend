from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path('admin/',         admin.site.urls),

    # Auth
    path('api/auth/',      include('apps.accounts.urls')),

    path('api/workspaces/', include('apps.workspaces.urls')),

    path('api/workspaces/<uuid:ws_id>/projects/', include('apps.projects.urls')),

    # OpenAPI docs
    path('api/schema/',    SpectacularAPIView.as_view(),        name='schema'),
    path('api/docs/',      SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)