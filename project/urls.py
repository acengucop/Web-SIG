from django.contrib import admin
from django.urls import path, include  # Tambahkan include jika belum ada
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('map_app.urls')),  # Pastikan aplikasi Anda terdaftar di sini
]

# Tambahkan ini untuk mendukung file media
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
