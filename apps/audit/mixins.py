"""
Mixin para auditoría de ViewSets - Se integra sin romper código existente
Uso: simplemente agregar AuditMixin a cualquier ViewSet
"""

import uuid
import logging
from typing import Any, Dict, Optional

from rest_framework.response import Response
from rest_framework import status

from .detailed_audit import DetailedAuditService

logger = logging.getLogger(__name__)


class AuditMixin:
    """
    Mixin para auditar CRUDs en ViewSets automáticamente
    
    Se integra sin cambiar la funcionalidad existente.
    Simplemente agrega auditoría a create, update, destroy.
    
    Uso:
        class MyViewSet(AuditMixin, viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            serializer_class = MySerializer
            
    El mixin detecta automáticamente:
    - resource_type (basado en el nombre del modelo)
    - cambios (before/after)
    - usuario, IP, navegador
    """

    # Override en la subclase si es necesario
    audit_resource_type = None  # ej: 'patient', 'document'

    def get_audit_service(self) -> DetailedAuditService:
        """Obtiene la instancia del servicio de auditoría"""
        tenant = getattr(self.request, 'tenant', None)
        return DetailedAuditService(tenant=tenant)

    def get_audit_resource_type(self) -> str:
        """Obtiene el tipo de recurso (puede override en subclase)"""
        if self.audit_resource_type:
            return self.audit_resource_type

        # Detectar automáticamente del nombre del modelo
        if hasattr(self, 'queryset') and self.queryset:
            model = self.queryset.model
            return model.__name__.lower()

        return 'resource'

    def get_audit_resource_id(self, instance: Any) -> Optional[uuid.UUID]:
        """Obtiene el ID del recurso"""
        if hasattr(instance, 'id'):
            resource_id = instance.id
            if isinstance(resource_id, uuid.UUID):
                return resource_id
            try:
                return uuid.UUID(str(resource_id))
            except:
                return None
        return None

    def get_audit_resource_name(self, instance: Any) -> str:
        """Obtiene un nombre descriptivo del recurso"""
        # Intentar diferentes campos comunes
        for field in ['name', 'title', 'subject', 'email', 'username']:
            if hasattr(instance, field):
                value = getattr(instance, field, '')
                if value:
                    return str(value)

        return str(instance.id) if hasattr(instance, 'id') else 'Unknown'

    def create(self, request, *args, **kwargs):
        """
        CREATE: Audita la creación de un recurso
        NO modifica la funcionalidad original
        """
        try:
            # Llamar al método original
            response = super().create(request, *args, **kwargs)

            # Si fue exitoso, auditar
            if response.status_code == status.HTTP_201_CREATED:
                self._audit_create_action(request, response)

            return response

        except Exception as e:
            # Auditar el error
            self._audit_error_action(
                request=request,
                action_type='CREATE',
                error_message=str(e)
            )
            raise

    def update(self, request, *args, **kwargs):
        """
        UPDATE: Audita la actualización de un recurso
        NO modifica la funcionalidad original
        """
        try:
            # Obtener instancia anterior (para comparar cambios)
            instance = self.get_object()
            old_data = self._serialize_instance(instance)

            # Llamar al método original
            response = super().update(request, *args, **kwargs)

            # Si fue exitoso, auditar
            if response.status_code in [status.HTTP_200_OK, status.HTTP_202_ACCEPTED]:
                self._audit_update_action(request, instance, old_data, response)

            return response

        except Exception as e:
            self._audit_error_action(
                request=request,
                action_type='UPDATE',
                error_message=str(e)
            )
            raise

    def destroy(self, request, *args, **kwargs):
        """
        DELETE: Audita la eliminación de un recurso
        NO modifica la funcionalidad original
        """
        try:
            # Obtener instancia antes de eliminar
            instance = self.get_object()
            resource_id = self.get_audit_resource_id(instance)
            resource_name = self.get_audit_resource_name(instance)

            # Llamar al método original
            response = super().destroy(request, *args, **kwargs)

            # Si fue exitoso, auditar
            if response.status_code == status.HTTP_204_NO_CONTENT:
                self._audit_delete_action(
                    request=request,
                    resource_id=resource_id,
                    resource_name=resource_name
                )

            return response

        except Exception as e:
            self._audit_error_action(
                request=request,
                action_type='DELETE',
                error_message=str(e)
            )
            raise

    # =========================================================================
    # MÉTODOS PRIVADOS DE AUDITORÍA (No tocar)
    # =========================================================================

    def _serialize_instance(self, instance: Any) -> Dict:
        """Serializa una instancia a dict para comparar"""
        data = {}
        if hasattr(instance, '__dict__'):
            data = instance.__dict__.copy()
            # Remover campos internos de Django
            data.pop('_state', None)
        return data

    def _audit_create_action(self, request, response):
        """Audita creación"""
        try:
            audit_service = self.get_audit_service()
            user = request.user if request.user.is_authenticated else None

            # Extraer datos creados de la respuesta
            created_data = response.data if isinstance(response.data, dict) else {}
            resource_id = created_data.get('id')
            if resource_id and isinstance(resource_id, str):
                try:
                    resource_id = uuid.UUID(resource_id)
                except:
                    resource_id = None

            # Cambios: None → valores creados (simplificado)
            changes = {
                k: {'before': None, 'after': v}
                for k, v in created_data.items()
                if k not in ['id', 'created_at', 'updated_at']
            }

            audit_service.log_crud_action(
                user=user,
                action_type='CREATE',
                resource_type=self.get_audit_resource_type(),
                resource_id=resource_id,
                resource_name=created_data.get('name', created_data.get('title', '')),
                changes=changes,
                request=request,
                severity='INFO',
            )
        except Exception as e:
            logger.error(f"Error auditando CREATE: {e}", exc_info=True)

    def _audit_update_action(self, request, old_instance, old_data, response):
        """Audita actualización"""
        try:
            audit_service = self.get_audit_service()
            user = request.user if request.user.is_authenticated else None

            # Comparar cambios
            new_data = response.data if isinstance(response.data, dict) else {}
            changes = {}

            for key, new_value in new_data.items():
                old_value = old_data.get(key)
                if old_value != new_value and key not in ['updated_at', 'id']:
                    changes[key] = {
                        'before': old_value,
                        'after': new_value
                    }

            resource_id = self.get_audit_resource_id(old_instance)

            audit_service.log_crud_action(
                user=user,
                action_type='UPDATE',
                resource_type=self.get_audit_resource_type(),
                resource_id=resource_id,
                resource_name=self.get_audit_resource_name(old_instance),
                changes=changes if changes else {'no_changes': True},
                request=request,
                severity='INFO' if changes else 'DEBUG',
            )
        except Exception as e:
            logger.error(f"Error auditando UPDATE: {e}", exc_info=True)

    def _audit_delete_action(self, request, resource_id, resource_name):
        """Audita eliminación"""
        try:
            audit_service = self.get_audit_service()
            user = request.user if request.user.is_authenticated else None

            audit_service.log_crud_action(
                user=user,
                action_type='DELETE',
                resource_type=self.get_audit_resource_type(),
                resource_id=resource_id,
                resource_name=resource_name,
                changes={'status': {'before': 'active', 'after': 'deleted'}},
                request=request,
                severity='WARNING',  # DELETE es importante
            )
        except Exception as e:
            logger.error(f"Error auditando DELETE: {e}", exc_info=True)

    def _audit_error_action(self, request, action_type, error_message):
        """Audita un error"""
        try:
            audit_service = self.get_audit_service()
            user = request.user if request.user.is_authenticated else None

            audit_service.log_error(
                user=user,
                action_type=action_type,
                resource_type=self.get_audit_resource_type(),
                error_message=error_message,
                request=request,
            )
        except Exception as e:
            logger.error(f"Error auditando error: {e}", exc_info=True)
