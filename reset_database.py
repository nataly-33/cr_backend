#!/usr/bin/env python
"""
Script para resetear la base de datos PostgreSQL completamente
"""
import os
import django
import psycopg2
from psycopg2 import sql

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings

def reset_database():
    """Elimina y recrea la base de datos"""
    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    db_user = db_config['USER']
    db_password = db_config['PASSWORD']
    db_host = db_config['HOST']
    db_port = db_config['PORT']
    
    print(f"Reseteando base de datos: {db_name}")
    print(f"Host: {db_host}:{db_port}")
    
    try:
        # Conectar a PostgreSQL (a la BD postgres, no a la app)
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("✓ Conectado a PostgreSQL")
        
        # Terminar todas las conexiones a la BD destino
        print(f"✓ Terminando conexiones a {db_name}...")
        cur.execute(sql.SQL(
            "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s AND pid != pg_backend_pid()"
        ), [db_name])
        
        # Eliminar la BD
        print(f"✓ Eliminando base de datos {db_name}...")
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(
            sql.Identifier(db_name)
        ))
        
        # Crear la BD nuevamente
        print(f"✓ Creando nueva base de datos {db_name}...")
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(db_name)
        ))
        
        print(f"✓ Base de datos {db_name} recreada exitosamente")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    if reset_database():
        print("\n✓ Fase 1: Base de datos limpia. Ahora ejecutar: python manage.py migrate")
    else:
        print("\n✗ Error al resetear la base de datos")
        exit(1)
