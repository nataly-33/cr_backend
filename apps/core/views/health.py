"""
Health check endpoint for production monitoring.
Verifica conectividad con RDS, Redis, y S3.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import boto3
from botocore.exceptions import ClientError


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint que verifica:
    - Database (RDS PostgreSQL)
    - Cache (Redis ElastiCache)
    - Storage (S3)
    """
    health_status = {
        'status': 'ok',
        'environment': getattr(settings, 'ENVIRONMENT', 'unknown'),
        'version': getattr(settings, 'DEPLOYMENT_VERSION', 'unknown'),
        'checks': {}
    }
    
    # Check Database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = {
            'status': 'connected',
            'type': 'postgresql'
        }
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['database'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check Redis Cache
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['checks']['cache'] = {
                'status': 'connected',
                'type': 'redis'
            }
        else:
            raise Exception("Cache test failed")
    except Exception as e:
        health_status['status'] = 'degraded'
        health_status['checks']['cache'] = {
            'status': 'error',
            'message': str(e)
        }
    
    # Check S3 Storage (solo en producción/staging)
    if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            health_status['checks']['storage'] = {
                'status': 'connected',
                'type': 's3',
                'bucket': settings.AWS_STORAGE_BUCKET_NAME
            }
        except ClientError as e:
            health_status['status'] = 'degraded'
            health_status['checks']['storage'] = {
                'status': 'error',
                'message': str(e)
            }
    else:
        health_status['checks']['storage'] = {
            'status': 'skipped',
            'message': 'S3 not configured'
        }
    
    # Determinar status code
    status_code = 200 if health_status['status'] == 'ok' else 503
    
    return Response(health_status, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request):
    """
    Readiness probe para Kubernetes/ECS.
    Verifica si el servicio está listo para recibir tráfico.
    """
    try:
        # Solo verificar database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return Response({'ready': True}, status=200)
    except Exception as e:
        return Response({
            'ready': False,
            'error': str(e)
        }, status=503)


@api_view(['GET'])
@permission_classes([AllowAny])
def liveness_check(request):
    """
    Liveness probe para Kubernetes/ECS.
    Verifica si el servicio está vivo (no colgado).
    """
    return Response({'alive': True}, status=200)
