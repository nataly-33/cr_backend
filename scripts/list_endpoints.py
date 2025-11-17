"""
Script para listar todos los endpoints disponibles en el backend
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.urls import get_resolver
from django.urls.resolvers import URLPattern, URLResolver


def show_urls(urlpatterns, prefix=''):
    """
    Función recursiva para mostrar todos los URLs
    """
    endpoints = []
    
    for pattern in urlpatterns:
        if isinstance(pattern, URLResolver):
            # Es un include()
            new_prefix = prefix + str(pattern.pattern)
            endpoints.extend(show_urls(pattern.url_patterns, new_prefix))
        elif isinstance(pattern, URLPattern):
            # Es un endpoint específico
            path = prefix + str(pattern.pattern)
            # Eliminar caracteres especiales de regex
            path = path.replace('^', '').replace('$', '')
            
            # Si contiene parámetros ViewSet
            if 'api' in path:
                endpoints.append({
                    'path': path,
                    'name': pattern.name or 'unnamed',
                    'methods': get_methods(pattern)
                })
    
    return endpoints


def get_methods(pattern):
    """
    Determinar qué métodos HTTP soporta un patrón
    """
    callback = pattern.callback
    
    # Obtener información del ViewSet o View
    if hasattr(callback, 'cls'):
        # Es un ViewSet
        cls = callback.cls
        methods = set()
        
        # Métodos estándar de CRUD
        if hasattr(cls, 'get'):
            methods.add('GET')
        if hasattr(cls, 'post'):
            methods.add('POST')
        if hasattr(cls, 'put'):
            methods.add('PUT')
        if hasattr(cls, 'patch'):
            methods.add('PATCH')
        if hasattr(cls, 'delete'):
            methods.add('DELETE')
        
        return ', '.join(sorted(methods)) or 'GET, POST, PUT, PATCH, DELETE'
    
    return 'GET'


def main():
    print("\n" + "="*100)
    print("ENDPOINTS DISPONIBLES EN EL BACKEND")
    print("="*100)
    
    resolver = get_resolver()
    
    # Obtener todos los patrones URL
    all_patterns = resolver.url_patterns
    
    endpoints = show_urls(all_patterns)
    
    # Filtrar solo endpoints API
    api_endpoints = [e for e in endpoints if 'api/' in e['path']]
    
    # Agrupar por módulo
    modules = {}
    for endpoint in sorted(api_endpoints, key=lambda x: x['path']):
        path = endpoint['path']
        
        # Extraer módulo
        parts = path.split('/')
        if len(parts) > 2 and parts[1] == 'api':
            module = parts[2] if parts[2] else 'core'
        else:
            module = 'other'
        
        if module not in modules:
            modules[module] = []
        
        modules[module].append(endpoint)
    
    # Mostrar endpoints por módulo
    for module in sorted(modules.keys()):
        endpoints = modules[module]
        print(f"\n📦 {module.upper()}")
        print("-" * 100)
        
        for endpoint in endpoints:
            path = endpoint['path']
            # Truncar path muy largo
            if len(path) > 70:
                path = path[:67] + "..."
            
            print(f"  {path:<70} | {endpoint['methods']}")
    
    print("\n" + "="*100)
    print(f"Total de endpoints: {len(api_endpoints)}")
    print("="*100 + "\n")


if __name__ == '__main__':
    main()
