from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('wallet.urls')),
    
    # --- مسارات توثيق OpenAPI / Swagger ---
    # توليد ملف الـ Schema الخام بصيغة YAML/JSON
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # واجهة Swagger التفاعلية للاختبار
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # واجهة ReDoc البديلة (ممتازة للقراءة والتصفح النظري)
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
