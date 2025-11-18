"""
Servicio de reportes dinámicos con Query Builder
"""
from typing import Dict, List, Any, Optional
from django.db.models import Q, Count, Sum, Avg, Max, Min, F, Value
from django.db.models.functions import Concat
from django.apps import apps
from datetime import datetime, timedelta
from django.utils import timezone

from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.documents.models import ClinicalDocument
from apps.accounts.models import User
from apps.audit.models import AuditLog
from .export_service import ReportExportService


class DynamicReportBuilder:
    """
    Constructor de reportes dinámicos con filtros seguros
    Evita inyección SQL usando ORM de Django
    """

    # Modelos permitidos para reportes
    ALLOWED_MODELS = {
        'patient': 'patients.Patient',
        'clinical_record': 'clinical_records.ClinicalRecord',
        'clinical_form': 'clinical_records.ClinicalForm',
        'document': 'documents.ClinicalDocument',
        'user': 'accounts.User',
        'audit_log': 'audit.AuditLog',
    }

    # Campos permitidos por modelo (EXACTOS del backend)
    ALLOWED_FIELDS = {
        'patient': [
            'identity_document_type', 'identity_document', 'first_name', 'last_name',
            'date_of_birth', 'gender', 'phone', 'email', 'address', 'city',
            'created_at', 'updated_at'
        ],
        'clinical_record': [
            'record_number', 'status', 'blood_type', 'family_history', 'social_history',
            'patient_name', 'patient_document', 'patient_email', 'created_by_name',
            'created_at', 'updated_at'
        ],
        'clinical_form': [
            'form_type', 'doctor_name', 'doctor_specialty', 'form_date',
            'clinical_record_number', 'patient_name', 'patient_document', 'filled_by_name',
            'created_at', 'updated_at'
        ],
        'document': [
            'document_type', 'title', 'description', 'document_date', 'specialty',
            'doctor_name', 'doctor_license', 'file_name', 'file_size_bytes',
            'mime_type', 'ocr_processed', 'ocr_confidence', 'ocr_status',
            'is_signed', 'is_locked', 'clinical_record_number', 'patient_name',
            'patient_document', 'created_by_name', 'created_at', 'updated_at'
        ],
        'user': [
            'email', 'username', 'first_name', 'last_name', 'phone', 'gender',
            'birth_date', 'professional_id', 'specialty', 'is_active', 'is_staff',
            'email_verified', 'tenant_name', 'created_at', 'updated_at'
        ],
        'audit_log': [
            'action_type', 'resource_type', 'resource_id', 'resource_name',
            'user_email', 'user_name', 'ip_address', 'user_agent', 'request_method',
            'request_path', 'response_status', 'timestamp'
        ],
    }
    
    # Definir relaciones y campos a anotar para cada modelo
    MODEL_RELATIONS = {
        'clinical_record': {
            'select_related': ['patient', 'created_by'],
            'annotations': {
                'patient_name': "Concat('patient__first_name', Value(' '), 'patient__last_name')",
                'patient_document': 'patient__identity_document',
                'patient_email': 'patient__email',
                'created_by_name': "Concat('created_by__first_name', Value(' '), 'created_by__last_name')",
            }
        },
        'clinical_form': {
            'select_related': ['clinical_record__patient', 'filled_by'],
            'annotations': {
                'clinical_record_number': 'clinical_record__record_number',
                'patient_name': "Concat('clinical_record__patient__first_name', Value(' '), 'clinical_record__patient__last_name')",
                'patient_document': 'clinical_record__patient__identity_document',
                'filled_by_name': "Concat('filled_by__first_name', Value(' '), 'filled_by__last_name')",
            }
        },
        'document': {
            'select_related': ['clinical_record__patient', 'created_by'],
            'annotations': {
                'clinical_record_number': 'clinical_record__record_number',
                'patient_name': "Concat('clinical_record__patient__first_name', Value(' '), 'clinical_record__patient__last_name')",
                'patient_document': 'clinical_record__patient__identity_document',
                'created_by_name': "Concat('created_by__first_name', Value(' '), 'created_by__last_name')",
            }
        },
        'user': {
            'select_related': ['tenant'],
            'annotations': {
                'tenant_name': 'tenant__name',
            }
        },
    }

    # Operadores permitidos
    ALLOWED_OPERATORS = {
        'equals': '',
        'contains': '__icontains',
        'starts_with': '__istartswith',
        'ends_with': '__iendswith',
        'gt': '__gt',
        'gte': '__gte',
        'lt': '__lt',
        'lte': '__lte',
        'in': '__in',
        'is_null': '__isnull',
    }

    # Agregaciones permitidas
    ALLOWED_AGGREGATIONS = ['count', 'sum', 'avg', 'max', 'min']

    def __init__(self, tenant):
        self.tenant = tenant
        self.export_service = ReportExportService()

    def build_query(
        self,
        model_name: str,
        filters: List[Dict[str, Any]] = None,
        fields: List[str] = None,
        order_by: str = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Construir y ejecutar query dinámica

        Args:
            model_name: Nombre del modelo ('patient', 'document', etc.)
            filters: Lista de filtros [{"field": "age", "operator": "gt", "value": 18}]
            fields: Campos a incluir en el resultado
            order_by: Campo para ordenar (-created_at)
            limit: Límite de registros

        Returns:
            Dict con datos y metadata del reporte
        """
        # Validar modelo
        if model_name not in self.ALLOWED_MODELS:
            raise ValueError(f"Modelo no permitido: {model_name}")

        # Obtener modelo
        model_path = self.ALLOWED_MODELS[model_name]
        app_label, model_class_name = model_path.split('.')
        Model = apps.get_model(app_label, model_class_name)

        # Iniciar queryset filtrado por tenant (si aplica)
        if hasattr(Model, 'tenant'):
            queryset = Model.objects.filter(tenant=self.tenant)
        else:
            # Algunos modelos no tienen tenant directo (como AuditLog)
            queryset = Model.objects.all()
            # Para AuditLog, filtrar por tenant manualmente
            if model_name == 'audit_log':
                queryset = queryset.filter(tenant=self.tenant)

        # Aplicar select_related y prefetch_related para optimizar queries con JOINs
        if model_name in self.MODEL_RELATIONS:
            relations = self.MODEL_RELATIONS[model_name]
            if 'select_related' in relations:
                queryset = queryset.select_related(*relations['select_related'])

        # Aplicar filtros
        if filters:
            q_objects = self._build_filters(model_name, filters)
            queryset = queryset.filter(q_objects)

        # Aplicar anotaciones para campos relacionados
        annotations = {}
        if model_name in self.MODEL_RELATIONS and 'annotations' in self.MODEL_RELATIONS[model_name]:
            for field_name, field_expr in self.MODEL_RELATIONS[model_name]['annotations'].items():
                # Evaluar la expresión para crear la anotación
                if 'Concat' in field_expr:
                    # Para Concat, necesitamos evaluar la expresión
                    annotations[field_name] = eval(field_expr)
                else:
                    # Para F() simple
                    annotations[field_name] = F(field_expr)
        
        if annotations:
            queryset = queryset.annotate(**annotations)

        # Seleccionar campos
        if fields:
            # Validar campos
            allowed = self.ALLOWED_FIELDS.get(model_name, [])
            fields = [f for f in fields if f in allowed]
            if fields:
                queryset = queryset.values(*fields)
        else:
            # Si no se especifican campos, incluir todos los permitidos
            all_fields = self.ALLOWED_FIELDS.get(model_name, [])
            queryset = queryset.values(*all_fields)

        # Ordenar
        if order_by:
            # Sanitizar campo de ordenamiento
            order_field = order_by.lstrip('-')
            if order_field in self.ALLOWED_FIELDS.get(model_name, []):
                queryset = queryset.order_by(order_by)

        # Limitar
        if limit and limit > 0:
            queryset = queryset[:min(limit, 10000)]  # Máximo 10000 registros

        # Ejecutar query
        data = list(queryset)

        # Convertir fechas y UUIDs a strings
        for item in data:
            for key, value in list(item.items()):
                if isinstance(value, datetime):
                    item[key] = value.isoformat()
                elif hasattr(value, 'hex'):  # UUID
                    item[key] = str(value)
                elif value is None:
                    item[key] = ''

        return {
            'model': model_name,
            'total_records': len(data),
            'data': data,
            'fields': fields or list(data[0].keys()) if data else [],
            'generated_at': timezone.now().isoformat(),
        }

    def _build_filters(self, model_name: str, filters: List[Dict[str, Any]]) -> Q:
        """
        Construir objetos Q de filtros de manera segura

        Args:
            model_name: Nombre del modelo
            filters: Lista de filtros

        Returns:
            Q object combinado
        """
        q_objects = Q()
        allowed_fields = self.ALLOWED_FIELDS.get(model_name, [])

        for filter_item in filters:
            field = filter_item.get('field')
            operator = filter_item.get('operator', 'equals')
            value = filter_item.get('value')

            # Validar campo
            if field not in allowed_fields:
                continue

            # Validar operador
            if operator not in self.ALLOWED_OPERATORS:
                continue

            # Construir lookup
            lookup = f"{field}{self.ALLOWED_OPERATORS[operator]}"

            # Aplicar filtro
            if operator == 'in' and isinstance(value, list):
                q_objects &= Q(**{lookup: value})
            elif operator == 'is_null':
                q_objects &= Q(**{lookup: bool(value)})
            else:
                q_objects &= Q(**{lookup: value})

        return q_objects

    def generate_aggregation_report(
        self,
        model_name: str,
        group_by: str,
        aggregations: List[Dict[str, str]],
        filters: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generar reporte con agregaciones (COUNT, SUM, AVG, etc.)

        Args:
            model_name: Nombre del modelo
            group_by: Campo para agrupar
            aggregations: [{"field": "age", "function": "avg"}]
            filters: Filtros opcionales

        Returns:
            Dict con datos agregados
        """
        # Validar modelo
        if model_name not in self.ALLOWED_MODELS:
            raise ValueError(f"Modelo no permitido: {model_name}")

        # Obtener modelo
        model_path = self.ALLOWED_MODELS[model_name]
        app_label, model_class_name = model_path.split('.')
        Model = apps.get_model(app_label, model_class_name)

        # Queryset base
        queryset = Model.objects.filter(tenant=self.tenant)

        # Aplicar filtros
        if filters:
            q_objects = self._build_filters(model_name, filters)
            queryset = queryset.filter(q_objects)

        # Validar group_by
        allowed_fields = self.ALLOWED_FIELDS.get(model_name, [])
        if group_by not in allowed_fields:
            raise ValueError(f"Campo no permitido: {group_by}")

        # Agrupar
        queryset = queryset.values(group_by)

        # Aplicar agregaciones
        agg_dict = {}
        for agg in aggregations:
            field = agg.get('field')
            function = agg.get('function', 'count').lower()

            if function not in self.ALLOWED_AGGREGATIONS:
                continue

            if field not in allowed_fields and function != 'count':
                continue

            # Mapear función
            agg_func = {
                'count': Count,
                'sum': Sum,
                'avg': Avg,
                'max': Max,
                'min': Min,
            }[function]

            # Agregar al dict
            key = f"{field}_{function}"
            if function == 'count':
                agg_dict[key] = Count('id')
            else:
                agg_dict[key] = agg_func(field)

        # Ejecutar agregación
        result = queryset.annotate(**agg_dict)

        # Convertir a lista
        data = list(result)

        return {
            'model': model_name,
            'group_by': group_by,
            'total_groups': len(data),
            'data': data,
            'generated_at': timezone.now().isoformat(),
        }

    def export_report(
        self,
        report_data: Dict[str, Any],
        format_type: str,
        title: str,
        metadata: Dict[str, Any] = None
    ) -> bytes:
        """
        Exportar reporte a PDF o Excel

        Args:
            report_data: Datos del reporte (output de build_query)
            format_type: 'pdf' o 'excel'
            title: Título del reporte
            metadata: Metadata adicional

        Returns:
            bytes del archivo generado
        """
        data = report_data.get('data', [])
        columns = report_data.get('fields', [])

        if format_type == 'pdf':
            return self.export_service.export_to_pdf(data, title, columns, metadata)
        elif format_type == 'excel':
            return self.export_service.export_to_excel(data, title, columns, metadata)
        elif format_type == 'csv':
            return self.export_service.export_to_csv(data, columns).encode('utf-8')
        else:
            raise ValueError(f"Formato no soportado: {format_type}")

    def get_predefined_reports(self) -> List[Dict[str, Any]]:
        """
        Obtener reportes predefinidos comunes

        Returns:
            Lista de configuraciones de reportes
        """
        return [
            {
                'id': 'patients_by_age',
                'name': 'Pacientes por Rango de Edad',
                'model': 'patient',
                'description': 'Distribución de pacientes por edad',
                'group_by': 'birth_date',
                'aggregations': [{'field': 'id', 'function': 'count'}]
            },
            {
                'id': 'patients_by_gender',
                'name': 'Pacientes por Género',
                'model': 'patient',
                'description': 'Distribución de pacientes por género',
                'group_by': 'gender',
                'aggregations': [{'field': 'id', 'function': 'count'}]
            },
            {
                'id': 'documents_by_type',
                'name': 'Documentos por Tipo',
                'model': 'document',
                'description': 'Cantidad de documentos por tipo',
                'group_by': 'document_type',
                'aggregations': [{'field': 'id', 'function': 'count'}]
            },
            {
                'id': 'patients_with_allergies',
                'name': 'Pacientes con Alergias',
                'model': 'clinical_record',
                'description': 'Lista de pacientes con alergias registradas',
                'filters': [{'field': 'allergies', 'operator': 'is_null', 'value': False}]
            },
        ]
