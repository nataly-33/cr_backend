from django.urls import path
from . import views

app_name = 'seed'

urlpatterns = [
    # POST /api/seed/generate/ - Ejecutar seeder
    # GET /api/seed/generate/ - Ejecutar seeder
    path('generate/', views.generate_seed, name='generate'),
    
    # GET /api/seed/list/ - Listar seeders disponibles
    path('list/', views.list_seeders, name='list'),
]
