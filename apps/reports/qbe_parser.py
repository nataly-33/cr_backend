"""
QBE (Query By Example) Parser - Parseador seguro para reportes dinámicos

Este módulo implementa un parser seguro que convierte ejemplos JSON
(Query By Example) en filtros Django ORM, previniendo SQL injection
mediante whitelist de campos permitidos.
"""

from django.db.models import Q, Model
from django.db import models as django_models
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class QBEParseError(Exception):
    """Excepción base para errores de QBE"""
    pass


class InvalidFieldError(QBEParseError):
    """Campo no permitido o no existe"""
    pass


class InvalidOperatorError(QBEParseError):
    """Operador no soportado"""
    pass


class InvalidValueError(QBEParseError):
    """Valor inválido para el tipo de campo"""
    pass


class QBEParser:
    """
    Parser seguro para Query By Example (QBE)
    
    Convierte ejemplos JSON en filtros Django ORM seguros,
    previniendo SQL injection mediante:
    - Whitelist de modelos permitidos
    - Whitelist de campos por modelo
    - Validación de tipos de datos
    - Uso exclusivo de Django ORM (no raw SQL)
    
    Ejemplo uso:
    >>> from apps.documents.models import ClinicalDocument
    >>> parser = QBEParser('documents')
    >>> example = {
    ...     'specialty': 'Cardiología',
    ...     'document_type': 'Historia Clínica',
    ...     'created_at_from': '2025-10-01',
    ...     'created_at_to': '2025-10-31'
    ... }
    >>> q_object = parser.parse_example(example)
    >>> queryset = ClinicalDocument.objects.filter(q_object)
    """
    
    # Whitelist de modelos permitidos
    ALLOWED_MODELS = {
        'documents': 'apps.documents.ClinicalDocument',
        'patients': 'apps.patients.Patient',
        'clinical_records': 'apps.clinical_records.ClinicalRecord',
        'users': 'apps.accounts.User',
        'audit_logs': 'apps.audit.AuditLog',
    }
    
    # Whitelist de campos permitidos por modelo
    ALLOWED_FIELDS = {
        'documents': {
            'document_type': 'exact',      # Tipo de documento
            'specialty': 'exact',           # Especialidad
            'doctor_name': 'icontains',     # Nombre del doctor
            'created_at': 'range',          # Fecha de creación (usa _from/_to)
            'document_date': 'range',       # Fecha del documento (usa _from/_to)
            'clinical_record': 'exact',     # ID del registro clínico
            'is_signed': 'exact',           # Si está firmado
            'status': 'exact',              # Estado del documento
        },
        'patients': {
            'first_name': 'icontains',     # Nombre (búsqueda)
            'last_name': 'icontains',      # Apellido (búsqueda)
            'full_name': 'icontains',      # Nombre completo (búsqueda)
            'identity_document': 'exact',  # Documento de identidad
            'gender': 'exact',              # Género
            'date_of_birth': 'range',      # Fecha de nacimiento (usa _from/_to)
            'is_active': 'exact',          # Si está activo
            'email': 'icontains',          # Email (búsqueda)
        },
        'clinical_records': {
            'status': 'exact',              # Estado (active, closed, archived)
            'patient': 'exact',             # ID del paciente
            'created_at': 'range',          # Fecha de creación (usa _from/_to)
            'is_archived': 'exact',         # Si está archivado
            'chief_complaint': 'icontains', # Motivo de consulta (búsqueda)
        },
        'users': {
            'first_name': 'icontains',     # Nombre (búsqueda)
            'last_name': 'icontains',      # Apellido (búsqueda)
            'full_name': 'icontains',      # Nombre completo (búsqueda)
            'email': 'icontains',          # Email (búsqueda)
            'is_active': 'exact',          # Si está activo
            'created_at': 'range',         # Fecha de creación (usa _from/_to)
            'role': 'exact',               # Rol del usuario
        },
        'audit_logs': {
            'action': 'exact',              # Tipo de acción
            'user': 'exact',                # ID del usuario
            'model_name': 'exact',          # Modelo afectado
            'created_at': 'range',          # Fecha (usa _from/_to)
            'ip_address': 'exact',          # IP de origen
        },
    }
    
    # Mapeo de tipos de campo a operadores permitidos
    FIELD_TYPE_OPERATORS = {
        'CharField': ['exact', 'icontains', 'startswith', 'endswith'],
        'TextField': ['exact', 'icontains'],
        'IntegerField': ['exact', 'lt', 'lte', 'gt', 'gte', 'in'],
        'BigIntegerField': ['exact', 'lt', 'lte', 'gt', 'gte', 'in'],
        'DateField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
        'DateTimeField': ['exact', 'lt', 'lte', 'gt', 'gte', 'range'],
        'BooleanField': ['exact'],
        'DecimalField': ['exact', 'lt', 'lte', 'gt', 'gte'],
        'ForeignKey': ['exact'],
        'ManyToOneRel': ['exact'],
    }
    
    def __init__(self, model_name: str):
        """
        Inicializa el parser para un modelo específico
        
        Args:
            model_name: Nombre del modelo ('documents', 'patients', etc.)
            
        Raises:
            QBEParseError: Si el modelo no está en la whitelist
        """
        if model_name not in self.ALLOWED_MODELS:
            raise QBEParseError(
                f"Modelo '{model_name}' no permitido. "
                f"Modelos permitidos: {list(self.ALLOWED_MODELS.keys())}"
            )
        
        self.model_name = model_name
        self.allowed_fields = self.ALLOWED_FIELDS.get(model_name, {})
        self.model_class = self._get_model_class(model_name)
        self.field_info = self._build_field_info()
    
    def _get_model_class(self, model_name: str) -> type:
        """Obtiene la clase del modelo de Django"""
        from django.apps import apps
        
        model_path = self.ALLOWED_MODELS[model_name]
        # El path es ej: 'apps.documents.ClinicalDocument'
        # Necesitamos separar en: app_label='documents', model_name='ClinicalDocument'
        parts = model_path.rsplit('.', 1)  # Separar por el último punto
        app_label = parts[0].split('.')[-1]  # Obtener la segunda parte (apps.DOCUMENTS)
        model = parts[1]  # Obtener el nombre del modelo
        
        try:
            return apps.get_model(app_label, model)
        except LookupError as e:
            raise QBEParseError(f"No se pudo cargar modelo {model_path}: {e}")
    
    def _build_field_info(self) -> dict:
        """Construye un diccionario con información de cada campo"""
        field_info = {}
        
        for field in self.model_class._meta.get_fields():
            if field.name in self.allowed_fields:
                field_info[field.name] = {
                    'field_object': field,
                    'field_type': type(field).__name__,
                    'default_operator': self.allowed_fields[field.name],
                }
        
        return field_info
    
    def validate_example(self, example: dict) -> tuple[bool, list]:
        """
        Valida que el ejemplo contenga solo campos permitidos
        
        Args:
            example: Diccionario con los criterios de búsqueda
            
        Returns:
            (válido, lista_de_errores)
        """
        errors = []
        
        if not isinstance(example, dict):
            errors.append("El ejemplo debe ser un diccionario")
            return False, errors
        
        if not example:
            errors.append("El ejemplo no puede estar vacío")
            return False, errors
        
        # Verificar cada campo
        for field_name in example.keys():
            # Remover sufijos _from, _to, _operator
            base_field = field_name
            for suffix in ['_from', '_to', '_operator', '_value']:
                if field_name.endswith(suffix):
                    base_field = field_name[:-len(suffix)]
                    break
            
            if base_field not in self.allowed_fields:
                errors.append(
                    f"Campo '{base_field}' no permitido. "
                    f"Campos permitidos: {list(self.allowed_fields.keys())}"
                )
        
        return len(errors) == 0, errors
    
    def get_field_type(self, field_name: str) -> str:
        """
        Retorna el tipo Django de un campo
        
        Args:
            field_name: Nombre del campo
            
        Returns:
            Tipo del campo (ej: 'CharField', 'DateField')
            
        Raises:
            InvalidFieldError: Si el campo no existe
        """
        if field_name not in self.field_info:
            raise InvalidFieldError(f"Campo '{field_name}' no permitido")
        
        return self.field_info[field_name]['field_type']
    
    def parse_example(self, example: dict, safe_mode: bool = True) -> Q:
        """
        Convierte un ejemplo JSON en un objeto Q de Django para filtros
        
        Args:
            example: Diccionario con criterios. Ej:
                {
                    'specialty': 'Cardiología',                    # eq exacto
                    'doctor_name': 'Juan',                          # icontains
                    'created_at_from': '2025-10-01',               # rango
                    'created_at_to': '2025-10-31',
                    'document_type__icontains': 'Consulta',        # override operator
                    'is_active': True                              # boolean exacto
                }
            safe_mode: Si True, solo permite operadores whitelistados
            
        Returns:
            Objeto Q() listo para usar en .filter()
            
        Raises:
            QBEParseError: Si hay errores de validación
        """
        valid, errors = self.validate_example(example)
        if not valid:
            raise QBEParseError(f"Validación fallida: {'; '.join(errors)}")
        
        q_object = Q()
        processed_fields = set()
        
        for key, value in example.items():
            if value is None or (isinstance(value, str) and value.strip() == ''):
                # Ignorar valores None o strings vacíos
                continue
            
            # Procesar campo
            field_name, operator = self._parse_field_key(key)
            
            # Saltar campos ya procesados (ej. created_at_from y created_at_to)
            if field_name in processed_fields:
                continue
            
            # Manejar rangos especialmente
            if self.allowed_fields[field_name] == 'range':
                q_part = self._build_range_filter(field_name, example)
                if q_part:
                    q_object &= q_part
                processed_fields.add(field_name)
            else:
                # Validar operador
                field_type = self.get_field_type(field_name)
                allowed_operators = self.FIELD_TYPE_OPERATORS.get(field_type, [])
                
                if operator not in allowed_operators:
                    if safe_mode:
                        logger.warning(
                            f"Operador '{operator}' no permitido para {field_type}. "
                            f"Usando '{allowed_operators[0]}'"
                        )
                        operator = allowed_operators[0]
                    else:
                        raise InvalidOperatorError(
                            f"Operador '{operator}' no permitido para {field_type}"
                        )
                
                # Construir filtro
                filter_key = f"{field_name}__{operator}" if operator != 'exact' else field_name
                q_object &= Q(**{filter_key: value})
        
        return q_object
    
    def _parse_field_key(self, key: str) -> tuple[str, str]:
        """
        Parsea una clave del ejemplo y extrae nombre del campo y operador
        
        Formatos soportados:
        - 'specialty' -> ('specialty', 'exact')
        - 'doctor_name__icontains' -> ('doctor_name', 'icontains')
        - 'created_at_from' -> ('created_at', 'from')
        - 'status_operator' -> NOT SUPPORTED (usa sufijos __op)
        
        Returns:
            (field_name, operator)
        """
        # Detectar si tiene operador explícito con __
        if '__' in key:
            parts = key.rsplit('__', 1)
            field_name = parts[0]
            operator = parts[1]
        else:
            # Detectar sufijos especiales
            if key.endswith('_from'):
                field_name = key[:-5]  # Remover '_from'
                operator = 'from'
            elif key.endswith('_to'):
                field_name = key[:-3]  # Remover '_to'
                operator = 'to'
            else:
                field_name = key
                operator = 'exact'
        
        # Validar que el campo base existe
        base_field = field_name
        if base_field not in self.allowed_fields:
            raise InvalidFieldError(f"Campo '{base_field}' no permitido")
        
        # Usar el operador por defecto del campo si no se especificó
        if operator == 'exact':
            operator = self.allowed_fields[base_field]
        
        return base_field, operator
    
    def _build_range_filter(self, field_name: str, example: dict) -> Q:
        """
        Construye un filtro de rango para campos tipo DateField
        
        Busca en el ejemplo las claves field_name_from y field_name_to
        """
        from_key = f"{field_name}_from"
        to_key = f"{field_name}_to"
        
        from_value = example.get(from_key)
        to_value = example.get(to_key)
        
        q_object = Q()
        
        if from_value:
            q_object &= Q(**{f"{field_name}__gte": from_value})
        
        if to_value:
            q_object &= Q(**{f"{field_name}__lte": to_value})
        
        return q_object if q_object else Q()
    
    def get_supported_fields(self) -> dict:
        """Retorna lista de campos soportados para este modelo"""
        return dict(self.allowed_fields)
    
    def get_filter_spec(self, example: dict) -> dict:
        """
        Construye una "spec" JSON amigable del filtro para reusar
        
        Útil para guardar filtros predefinidos o mostrar al usuario
        qué filtro se aplicó.
        
        Ejemplo retorno:
        {
            'model': 'documents',
            'filters': [
                {
                    'field': 'specialty',
                    'operator': 'exact',
                    'value': 'Cardiología'
                },
                {
                    'field': 'created_at',
                    'operator': 'range',
                    'value': {
                        'from': '2025-10-01',
                        'to': '2025-10-31'
                    }
                }
            ]
        }
        """
        spec = {
            'model': self.model_name,
            'filters': []
        }
        
        processed = set()
        
        for key, value in example.items():
            if value is None or (isinstance(value, str) and value.strip() == ''):
                continue
            
            field_name, operator = self._parse_field_key(key)
            
            if field_name in processed:
                continue
            
            if operator in ['from', 'to']:
                # Ya fue procesado como rango
                continue
            
            # Si es rango, agregar con datos from/to
            if self.allowed_fields[field_name] == 'range':
                from_key = f"{field_name}_from"
                to_key = f"{field_name}_to"
                filter_item = {
                    'field': field_name,
                    'operator': 'range',
                    'value': {
                        'from': example.get(from_key),
                        'to': example.get(to_key)
                    }
                }
                processed.add(field_name)
            else:
                filter_item = {
                    'field': field_name,
                    'operator': operator,
                    'value': value
                }
            
            spec['filters'].append(filter_item)
        
        return spec
