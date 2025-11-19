"""
Servicios de auditoría - Logs inmutables + CloudWatch
"""

import json
import uuid
import boto3
from datetime import datetime
from typing import Dict, Any, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder

from apps.core.models import Tenant
from .models import AuditLog

User = get_user_model()


class AuditLogService:
    """
    Servicio para crear logs de auditoría inmutables
    Integrado con AWS CloudWatch
    """

    def __init__(self, tenant: Optional[Tenant] = None):
        self.tenant = tenant
        self.cloudwatch_enabled = getattr(settings, 'USE_CLOUDWATCH', False)

        if self.cloudwatch_enabled:
            self.cloudwatch = boto3.client(
                'logs',
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
            )
            self.log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs/audit')
            self.log_stream = f"audit-{datetime.now().strftime('%Y-%m-%d')}"
            self._ensure_log_stream()

    def _ensure_log_stream(self):
        """Asegurar que el log stream existe en CloudWatch"""
        if not self.cloudwatch_enabled:
            return
        
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Primero intentar crear el log group (por si no existe)
            try:
                self.cloudwatch.create_log_group(
                    logGroupName=self.log_group
                )
                logger.info(f"✓ Log group created: {self.log_group}")
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                logger.debug(f"Log group already exists: {self.log_group}")
            except Exception as e:
                logger.error(f"Error creating log group: {e}")
            
            # Luego crear el stream
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
                logger.info(f"✓ Log stream created: {self.log_stream}")
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                logger.debug(f"Log stream already exists: {self.log_stream}")
            except Exception as e:
                logger.error(f"Error creating log stream: {e}")
                
        except Exception as e:
            logger.error(f"Unexpected error in _ensure_log_stream: {type(e).__name__}: {e}", exc_info=True)

    def log_action(
        self,
        user: User,
        action_type: str,
        resource_type: str,
        resource_id: Optional[uuid.UUID] = None,
        resource_name: str = '',
        ip_address: str = '',
        user_agent: str = '',
        request_method: str = '',
        request_path: str = '',
        request_body: Optional[Dict] = None,
        changes: Optional[Dict] = None,
        response_status: Optional[int] = None,
        error_message: str = '',
        session_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """
        Crear un log de auditoría inmutable

        Args:
            user: Usuario que realiza la acción
            action_type: CREATE, READ, UPDATE, DELETE, etc.
            resource_type: patient, document, user, etc.
            resource_id: ID del recurso afectado
            resource_name: Nombre del recurso
            ip_address: IP del cliente
            user_agent: User Agent del cliente
            request_method: GET, POST, PUT, DELETE
            request_path: /api/patients/
            request_body: Cuerpo de la petición
            changes: {"before": {...}, "after": {...}}
            response_status: HTTP status code
            error_message: Mensaje de error si aplica
            session_id: ID de sesión
            metadata: Datos adicionales

        Returns:
            AuditLog: Log creado
        """
        
        audit_log = AuditLog.objects.create(
            tenant=self.tenant,
            user=user,
            user_email=user.email if user else 'SYSTEM',
            user_name=f"{user.first_name} {user.last_name}".strip() if user else 'SYSTEM',
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            ip_address=ip_address or '127.0.0.1',
            user_agent=user_agent or 'Unknown',
            request_method=request_method or 'UNKNOWN',
            request_path=request_path or '/',
            request_body=request_body or {},
            changes=changes or {},
            response_status=response_status,
            error_message=error_message,
            session_id=session_id,
            metadata=metadata or {},
        )

        # Enviar a CloudWatch si está habilitado
        if self.cloudwatch_enabled:
            self._send_to_cloudwatch(audit_log)

        return audit_log

    def _send_to_cloudwatch(self, audit_log: AuditLog):
        """Enviar log a AWS CloudWatch"""
        if not self.cloudwatch_enabled:
            return

        import logging
        logger = logging.getLogger(__name__)

        try:
            log_data = {
                'id': str(audit_log.id),
                'timestamp': audit_log.timestamp.isoformat(),
                'user_email': audit_log.user_email,
                'user_name': audit_log.user_name,
                'action_type': audit_log.action_type,
                'resource_type': audit_log.resource_type,
                'resource_id': str(audit_log.resource_id) if audit_log.resource_id else None,
                'resource_name': audit_log.resource_name,
                'ip_address': audit_log.ip_address,
                'user_agent': audit_log.user_agent,
                'request_method': audit_log.request_method,
                'request_path': audit_log.request_path,
                'response_status': audit_log.response_status,
                'changes': audit_log.changes,
                'error_message': audit_log.error_message,
                'log_hash': audit_log.log_hash,
            }

            # Intentar obtener el nextSequenceToken del último evento
            sequence_token = None
            try:
                response = self.cloudwatch.describe_log_streams(
                    logGroupName=self.log_group,
                    logStreamNamePrefix=self.log_stream,
                    limit=1
                )
                if response['logStreams']:
                    sequence_token = response['logStreams'][0].get('uploadSequenceToken')
            except Exception as e:
                logger.debug(f"Could not get sequence token: {e}")
            
            # Preparar parámetros para put_log_events
            put_params = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [
                    {
                        'timestamp': int(audit_log.timestamp.timestamp() * 1000),
                        'message': json.dumps(log_data, cls=DjangoJSONEncoder),
                    }
                ]
            }
            
            # Agregar sequence token si existe
            if sequence_token:
                put_params['sequenceToken'] = sequence_token
            
            response = self.cloudwatch.put_log_events(**put_params)
            logger.info(f"✓ Audit log sent to CloudWatch: {audit_log.id}")
            
        except self.cloudwatch.exceptions.InvalidSequenceTokenException as e:
            # Si el token es inválido, reintentar sin token
            logger.warning(f"Invalid sequence token, retrying without token: {e}")
            try:
                self.cloudwatch.put_log_events(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream,
                    logEvents=[
                        {
                            'timestamp': int(audit_log.timestamp.timestamp() * 1000),
                            'message': json.dumps(log_data, cls=DjangoJSONEncoder),
                        }
                    ]
                )
                logger.info(f"✓ Audit log sent to CloudWatch (retry): {audit_log.id}")
            except Exception as retry_error:
                logger.error(f"✗ Failed to send log after retry: {type(retry_error).__name__}: {str(retry_error)}", exc_info=True)
        except Exception as e:
            # Log error pero no fallar la acción principal
            logger.error(f"✗ Error enviando log a CloudWatch: {type(e).__name__}: {str(e)}", exc_info=True)

    def verify_log_integrity(self, audit_log_id: uuid.UUID) -> bool:
        """
        Verificar integridad de un log
        
        Returns:
            bool: True si el log no ha sido manipulado
        """
        try:
            log = AuditLog.objects.get(id=audit_log_id)
            return log.verify_integrity()
        except AuditLog.DoesNotExist:
            return False

    def get_audit_trail(
        self,
        user: Optional[User] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """
        Obtener trail de auditoría filtrado

        Returns:
            list: Logs filtrados
        """
        query = AuditLog.objects.filter(tenant=self.tenant)

        if user:
            query = query.filter(user=user)
        if resource_type:
            query = query.filter(resource_type=resource_type)
        if resource_id:
            query = query.filter(resource_id=resource_id)
        if action_type:
            query = query.filter(action_type=action_type)

        return query[offset:offset + limit]

    def get_user_audit_trail(self, user: User, limit: int = 50) -> list:
        """Obtener historial de auditoría de un usuario"""
        return self.get_audit_trail(user=user, limit=limit)

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> list:
        """Obtener historial completo de cambios de un recurso"""
        return self.get_audit_trail(
            resource_type=resource_type,
            resource_id=resource_id,
        )

    def export_audit_logs(
        self,
        format_type: str = 'json',
        **filters
    ) -> str:
        """
        Exportar logs de auditoría
        
        Args:
            format_type: 'json' o 'csv'
            **filters: Filtros adicionales
            
        Returns:
            str: Datos exportados
        """
        logs = self.get_audit_trail(**filters)

        if format_type == 'json':
            data = []
            for log in logs:
                data.append({
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'user': log.user_email,
                    'action': log.action_type,
                    'resource': f"{log.resource_type}/{log.resource_id}",
                    'ip': log.ip_address,
                    'status': log.response_status,
                    'hash': log.log_hash,
                    'verified': log.verify_integrity(),
                })
            return json.dumps(data, cls=DjangoJSONEncoder, indent=2)

        elif format_type == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'ID', 'Timestamp', 'Usuario', 'Acción', 'Recurso',
                'IP', 'Status', 'Hash', 'Verificado'
            ])
            
            for log in logs:
                writer.writerow([
                    str(log.id),
                    log.timestamp.isoformat(),
                    log.user_email,
                    log.action_type,
                    f"{log.resource_type}/{log.resource_id}",
                    log.ip_address,
                    log.response_status,
                    log.log_hash,
                    'Sí' if log.verify_integrity() else 'No',
                ])
            
            return output.getvalue()

        return ""
