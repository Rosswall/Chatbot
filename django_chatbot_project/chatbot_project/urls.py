from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('chatbot.urls')),
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', RedirectView.as_view(url='/api/', permanent=False)),  # 👈 redirect root to /api/
]