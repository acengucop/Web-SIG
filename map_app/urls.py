from django.urls import path
from . import views

urlpatterns = [
    path('', views.map_view, name='map_view'),
    path('add/', views.add_coordinate, name='add_coordinate'),
    path('edit/<int:id>/', views.edit_coordinate, name='edit_coordinate'),  # Gunakan <int:id>
    path('delete/<int:id>/', views.delete_coordinate, name='delete_coordinate'),  # Gunakan <int:id>
]
