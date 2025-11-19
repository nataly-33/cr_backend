"""
Servicio de Auditoría Profesional - Auditoría completa de todos los CRUDs
Registra: cambios, usuario, IP, navegador, ubicación, timestamp
Integración con CloudWatch automática
"""

import json
import uuid
import logging
import boto3
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.utils import timezone

from apps.core.models import Tenant
from .models import AuditLog

User = get_user_model()
logger = logging.getLogger(__name__)


class DetailedAuditService:
    """
    Servicio profesional de auditoría con rastreo completo de cambios
    
    Features:
    - Registra cambios field-by-field (before/after)
    - Captura metadata del usuario (IP, navegador, ubicación)
    - Niveles de severidad (INFO, WARNING, ERROR)
    - Integración CloudWatch automática
    - Inmutable y verificable con hash SHA-256
    """

    LOG_LEVELS = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'DEBUG': logging.DEBUG,
    }

    def __init__(self, tenant: Optional[Tenant] = None):
        self.tenant = tenant
        self.cloudwatch_enabled = getattr(settings, 'USE_CLOUDWATCH', False)
        self.cloudwatch = None
        
        if self.cloudwatch_enabled:
            try:
                self.cloudwatch = boto3.client(
                    'logs',
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                self.log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
                self.log_stream = f"audit-{datetime.now().strftime('%Y-%m-%d')}"
                self._ensure_cloudwatch_stream()
            except Exception as e:
                logger.error(f"Error inicializando CloudWatch: {e}")
                self.cloudwatch = None

    def _ensure_cloudwatch_stream(self):
        """Asegurar que el log stream existe en CloudWatch"""
        if not self.cloudwatch:
            return

        try:
            # Crear log group si no existe
            try:
                self.cloudwatch.create_log_group(logGroupName=self.log_group)
                logger.debug(f"Log group creado: {self.log_group}")
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                pass
            except Exception as e:
                logger.warning(f"Error creando log group: {e}")

            # Crear log stream si no existe
            try:
                self.cloudwatch.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
            except self.cloudwatch.exceptions.ResourceAlreadyExistsException:
                pass
            except Exception as e:
                logger.warning(f"Error creando log stream: {e}")
        except Exception as e:
            logger.error(f"Error en _ensure_cloudwatch_stream: {e}")

    def _send_to_cloudwatch(self, audit_log: AuditLog):
        """Enviar log a CloudWatch"""
        if not self.cloudwatch or not self.cloudwatch_enabled:
            return

        try:
            log_data = {
                'id': str(audit_log.id),
                'timestamp': audit_log.timestamp.isoformat(),
                'user_email': audit_log.user_email,
                'user_id': str(audit_log.user.id) if audit_log.user else None,
                'action_type': audit_log.action_type,
                'resource_type': audit_log.resource_type,
                'resource_id': str(audit_log.resource_id) if audit_log.resource_id else None,
                'ip_address': audit_log.ip_address,
                'changes': audit_log.changes,
            }

            self.cloudwatch.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[{
                    'timestamp': int(audit_log.timestamp.timestamp() * 1000),
                    'message': json.dumps(log_data, cls=DjangoJSONEncoder, default=str),
                }]
            )
            logger.debug(f"Log enviado a CloudWatch: {audit_log.id}")
        except Exception as e:
            logger.error(f"Error enviando a CloudWatch: {type(e).__name__}: {e}", exc_info=True)

    def extract_changes(self, instance: Model, original_data: Dict = None) -> Dict[str, Any]:
        """
        Extrae los cambios (before/after) de una instancia del modelo
        
        Args:
            instance: Instancia del modelo
            original_data: Datos originales (para UPDATE)
            
        Returns:
            Dict con estructura {"field_name": {"before": valor, "after": valor}}
        """
        changes = {}

        if not instance or not hasattr(instance, '_meta'):
            return changes

        for field in instance._meta.get_fields():
            # Ignorar relaciones complejas
            if field.many_to_one or field.many_to_many or field.one_to_many:
                continue

            field_name = field.name
            current_value = getattr(instance, field_name, None)

            # Convertir tipos especiales
            if isinstance(current_value, Decimal):
                current_value = float(current_value)
            elif isinstance(current_value, datetime):
                current_value = current_value.isoformat()
            elif isinstance(current_value, uuid.UUID):
                current_value = str(current_value)
            elif hasattr(current_value, '__dict__') and not isinstance(current_value, (str, int, float, bool)):
                current_value = str(current_value)

            # Si hay datos originales, comparar
            if original_data and field_name in original_data:
                original_value = original_data[field_name]
                if original_value != current_value:
                    changes[field_name] = {
                        'before': original_value,
                        'after': current_value
                    }
            elif original_data is None:
                # Si no hay datos originales, es un CREATE
                changes[field_name] = {
                    'before': None,
                    'after': current_value
                }

        return changes

    def get_client_info(self, request=None) -> Dict[str, str]:
        """
        Extrae información del cliente (IP, navegador, etc)
        
        Returns:
            Dict con: ip_address, user_agent, browser_name
        """
        info = {
            'ip_address': '127.0.0.1',
            'user_agent': 'Unknown',
            'browser_name': 'Unknown',
        }

        if not request:
            return info

        # Obtener IP (puede estar detrás de proxy)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            info['ip_address'] = x_forwarded_for.split(',')[0].strip()
        else:
            info['ip_address'] = request.META.get('REMOTE_ADDR', '127.0.0.1')

        # Obtener User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        info['user_agent'] = user_agent

        # Parsear navegador de User-Agent
        info['browser_name'] = self._extract_browser(user_agent)

        return info

    def _extract_browser(self, user_agent: str) -> str:
        """Extrae nombre del navegador del User-Agent"""
        if 'Chrome' in user_agent and 'Edg' not in user_agent:
            return 'Chrome'
        elif 'Firefox' in user_agent:
            return 'Firefox'
        elif 'Safari' in user_agent and 'Chrome' not in user_agent:
            return 'Safari'
        elif 'Edg' in user_agent:
            return 'Edge'
        elif 'Opera' in user_agent:
            return 'Opera'
        elif 'Trident' in user_agent:
            return 'Internet Explorer'
        else:
            return 'Other'

    def log_crud_action(
        self,
        user: User,
        action_type: str,  # 'CREATE', 'UPDATE', 'DELETE', 'READ'
        resource_type: str,  # 'patient', 'document', 'user', etc
        resource_id: Optional[uuid.UUID] = None,
        resource_name: str = '',
        changes: Optional[Dict] = None,
        request=None,
        severity: str = 'INFO',
        error_message: str = '',
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """
        Registra una acción de CRUD con toda la información necesaria
        
        Args:
            user: Usuario que realiza la acción
            action_type: CREATE, UPDATE, DELETE, READ
            resource_type: Tipo de recurso (patient, document, etc)
            resource_id: ID del recurso
            resource_name: Nombre del recurso (para facilitar búsqueda)
            changes: Dict con cambios {field: {before, after}}
            request: Request de Django (para extraer IP, navegador)
            severity: INFO, WARNING, ERROR
            error_message: Mensaje si hay error
            metadata: Datos adicionales
            
        Returns:
            AuditLog: Log creado
        """
        
        # Validar severity
        if severity not in self.LOG_LEVELS:
            severity = 'INFO'

        # Extraer información del cliente
        client_info = self.get_client_info(request)

        # Crear metadata completa
        full_metadata = metadata or {}
        full_metadata['severity'] = severity
        full_metadata['browser'] = client_info['browser_name']
        full_metadata['user_agent_full'] = client_info['user_agent']

        try:
            # Crear log
            audit_log = AuditLog.objects.create(
                tenant=self.tenant,
                user=user,
                user_email=user.email if user else 'SYSTEM',
                user_name=f"{user.first_name} {user.last_name}".strip() if user else 'SYSTEM',
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_name=resource_name,
                ip_address=client_info['ip_address'],
                user_agent=client_info['user_agent'],
                request_method='API',
                request_path=f'/api/{resource_type}/',
                changes=changes or {},
                response_status=200 if not error_message else 400,
                error_message=error_message,
                metadata=full_metadata,
            )

            # Log local
            log_message = (
                f"[{severity}] {action_type} {resource_type}"
                f" | User: {user.email if user else 'SYSTEM'}"
                f" | IP: {client_info['ip_address']}"
                f" | Changes: {len(changes or {})}"
            )
            getattr(logger, severity.lower())(log_message)

            # Enviar a CloudWatch
            if self.cloudwatch_enabled:
                self._send_to_cloudwatch(audit_log)

            return audit_log

        except Exception as e:
            logger.error(
                f"Error creando audit log: {type(e).__name__}: {e}",
                exc_info=True
            )
            raise

    def log_error(
        self,
        user: User,
        action_type: str,
        resource_type: str,
        error_message: str,
        resource_id: Optional[uuid.UUID] = None,
        request=None,
        **kwargs
    ) -> AuditLog:
        """Registra un error en una acción"""
        return self.log_crud_action(
            user=user,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            severity='ERROR',
            error_message=error_message,
            **kwargs
        )

    def compare_instances(
        self,
        old_instance: Model,
        new_instance: Model,
    ) -> Dict[str, Dict]:
        """
        Compara dos instancias y devuelve los cambios
        Útil para UPDATE
        """
        changes = {}

        if not old_instance or not new_instance:
            return changes

        for field in new_instance._meta.get_fields():
            if field.many_to_one or field.many_to_many or field.one_to_many:
                continue

            field_name = field.name
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(new_instance, field_name, None)

            # Convertir tipos
            if isinstance(old_value, (Decimal, datetime, uuid.UUID)):
                old_value = str(old_value) if old_value else None
            if isinstance(new_value, (Decimal, datetime, uuid.UUID)):
                new_value = str(new_value) if new_value else None

            if old_value != new_value:
                changes[field_name] = {
                    'before': old_value,
                    'after': new_value
                }

        return changes

    def get_audit_trail(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        user: Optional[User] = None,
        action_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Obtiene el historial de auditoría filtrado"""
        query = AuditLog.objects.filter(tenant=self.tenant)

        if resource_type:
            query = query.filter(resource_type=resource_type)
        if resource_id:
            query = query.filter(resource_id=resource_id)
        if user:
            query = query.filter(user=user)
        if action_type:
            query = query.filter(action_type=action_type)

        return query.order_by('-timestamp')[:limit]

    def get_user_actions(self, user: User, limit: int = 50) -> List[AuditLog]:
        """Obtiene todas las acciones de un usuario"""
        return self.get_audit_trail(user=user, limit=limit)

    def verify_log_integrity(self, audit_log_id: uuid.UUID) -> bool:
        """Verifica la integridad del log (no fue manipulado)"""
        try:
            log = AuditLog.objects.get(id=audit_log_id)
            return log.verify_integrity()
        except AuditLog.DoesNotExist:
            return False

    def export_audit_logs(
        self,
        resource_type: Optional[str] = None,
        format_type: str = 'json',
        **filters
    ) -> str:
        """Exporta logs en JSON o CSV"""
        logs = self.get_audit_trail(resource_type=resource_type, **filters)

        if format_type == 'json':
            data = []
            for log in logs:
                data.append({
                    'id': str(log.id),
                    'timestamp': log.timestamp.isoformat(),
                    'user': log.user_email,
                    'action': log.action_type,
                    'resource': f"{log.resource_type}/{log.resource_id}",
                    'changes': log.changes,
                    'ip': log.ip_address,
                    'browser': log.metadata.get('browser', 'Unknown'),
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
                'IP', 'Navegador', 'Cambios', 'Verificado'
            ])

            for log in logs:
                writer.writerow([
                    str(log.id),
                    log.timestamp.isoformat(),
                    log.user_email,
                    log.action_type,
                    f"{log.resource_type}/{log.resource_id}",
                    log.ip_address,
                    log.metadata.get('browser', 'Unknown'),
                    json.dumps(log.changes),
                    'Sí' if log.verify_integrity() else 'No',
                ])

            return output.getvalue()

        return ""
