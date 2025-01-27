from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('add/', views.add_coordinate, name='add_coordinate'),
    path('edit/<int:id>/', views.edit_coordinate, name='edit_coordinate'),
    path('delete/<int:id>/', views.delete_coordinate, name='delete_coordinate'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('about/', views.about_pekanbaru, name='about_pekanbaru'),

]

# Tambahkan konfigurasi untuk media files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)