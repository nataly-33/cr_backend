"""
Sistema de Filtros Dinámicos Reutilizables

Proporciona una clase DynamicFilter que aplica filtros arbitrarios
a querysets de Django de manera segura.
"""

from django.db.models import Q, F, Count, Sum, Avg, Max, Min, Case, When, Value
from django.db.models.functions import TruncDate, Extract
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class DynamicFilterError(Exception):
    """Excepción para errores en filtros dinámicos"""
    pass


class DynamicFilter:
    """
    Sistema de filtros dinámicos para querysets
    
    Permite aplicar filtros arbitrarios de manera segura sin usar raw SQL.
    
    Ejemplo uso:
    >>> from apps.documents.models import ClinicalDocument
    >>> qs = ClinicalDocument.objects.all()
    >>> 
    >>> filter_spec = {
    ...     'filters': [
    ...         {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'},
    ...         {'field': 'created_at', 'operator': 'gte', 'value': '2025-10-01'},
    ...     ],
    ...     'exclude': [
    ...         {'field': 'status', 'operator': 'eq', 'value': 'deleted'}
    ...     ],
    ...     'group_by': ['specialty'],
    ...     'order_by': ['created_at'],
    ...     'limit': 100
    ... }
    >>> 
    >>> result = DynamicFilter.apply(qs, filter_spec)
    >>> print(result.count())
    """
    
    # Mapeo de operadores a sufijos de Django ORM
    OPERATORS = {
        'eq': '',                  # exact match (no sufijo)
        'ne': 'ne',               # not equal (custom)
        'lt': '__lt',             # less than
        'lte': '__lte',           # less than or equal
        'gt': '__gt',             # greater than
        'gte': '__gte',           # greater than or equal
        'in': '__in',             # in list
        'contains': '__icontains', # contains (case-insensitive)
        'startswith': '__istartswith',
        'endswith': '__iendswith',
        'isnull': '__isnull',
        'regex': '__iregex',
        'range': 'range',         # between (custom)
    }
    
    @staticmethod
    def apply(queryset, filter_spec: dict):
        """
        Aplica filtros dinámicos a un queryset
        
        Args:
            queryset: Django QuerySet
            filter_spec: Diccionario con especificación de filtros
            
        Formato de filter_spec:
        {
            'filters': [
                {
                    'field': 'specialty',
                    'operator': 'eq',  # eq, ne, lt, lte, gt, gte, in, contains, range, etc.
                    'value': 'Cardiología'
                },
                {
                    'field': 'created_at',
                    'operator': 'gte',
                    'value': '2025-10-01'
                }
            ],
            'exclude': [  # Filtros para excluir (NOT)
                {
                    'field': 'status',
                    'operator': 'eq',
                    'value': 'deleted'
                }
            ],
            'group_by': ['specialty'],  # GROUP BY
            'order_by': ['-created_at'],  # ORDER BY (- para DESC)
            'distinct': True,  # DISTINCT
            'limit': 100,  # LIMIT
            'offset': 0    # OFFSET
        }
        
        Returns:
            QuerySet modificado
        """
        if not filter_spec:
            return queryset
        
        # Aplicar filtros positivos (AND)
        filters = filter_spec.get('filters', [])
        for f in filters:
            queryset = DynamicFilter._apply_single_filter(queryset, f, exclude=False)
        
        # Aplicar filtros negativos (NOT)
        excludes = filter_spec.get('exclude', [])
        for e in excludes:
            queryset = DynamicFilter._apply_single_filter(queryset, e, exclude=True)
        
        # Agrupación
        group_by = filter_spec.get('group_by')
        if group_by:
            queryset = queryset.values(*group_by).annotate(count=Count('id'))
        
        # Ordenamiento
        order_by = filter_spec.get('order_by')
        if order_by:
            queryset = queryset.order_by(*order_by)
        
        # Distinct
        if filter_spec.get('distinct', False):
            queryset = queryset.distinct()
        
        # Limit y Offset
        limit = filter_spec.get('limit')
        offset = filter_spec.get('offset', 0)
        
        if offset:
            queryset = queryset[offset:]
        
        if limit:
            if offset:
                queryset = queryset[:limit]
            else:
                queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def _apply_single_filter(queryset, filter_item: dict, exclude: bool = False):
        """
        Aplica un filtro individual
        
        Args:
            queryset: Django QuerySet
            filter_item: {'field': str, 'operator': str, 'value': Any}
            exclude: Si True, usa exclude() en lugar de filter()
        """
        field = filter_item.get('field')
        operator = filter_item.get('operator', 'eq')
        value = filter_item.get('value')
        
        if not field:
            raise DynamicFilterError("Filtro debe tener campo 'field'")
        
        if operator not in DynamicFilter.OPERATORS:
            raise DynamicFilterError(
                f"Operador '{operator}' no reconocido. "
                f"Operadores: {list(DynamicFilter.OPERATORS.keys())}"
            )
        
        # Construir la consulta Q
        q = DynamicFilter._build_q_object(field, operator, value)
        
        # Aplicar filtro o exclusión
        if exclude:
            queryset = queryset.exclude(q)
        else:
            queryset = queryset.filter(q)
        
        return queryset
    
    @staticmethod
    def _build_q_object(field: str, operator: str, value) -> Q:
        """Construye un objeto Q() seguro para Django ORM"""
        
        op_suffix = DynamicFilter.OPERATORS.get(operator, '')
        
        # Casos especiales
        if operator == 'ne':
            # not equal: usar exclude
            return ~Q(**{field: value})
        
        elif operator == 'range':
            # Entre dos valores
            if isinstance(value, dict):
                min_val = value.get('from') or value.get('min')
                max_val = value.get('to') or value.get('max')
                q = Q()
                if min_val:
                    q &= Q(**{f"{field}__gte": min_val})
                if max_val:
                    q &= Q(**{f"{field}__lte": max_val})
                return q
            else:
                raise DynamicFilterError(
                    f"range requiere dict con 'from'/'to' o 'min'/'max'"
                )
        
        elif operator == 'isnull':
            # IS NULL / IS NOT NULL
            return Q(**{f"{field}__isnull": value})
        
        else:
            # Operador normal con sufijo
            filter_key = f"{field}{op_suffix}" if op_suffix else field
            
            # Convertir valor si es necesario
            value = DynamicFilter._coerce_value(value, operator)
            
            return Q(**{filter_key: value})
    
    @staticmethod
    def _coerce_value(value, operator: str):
        """Convierte el valor al tipo correcto según el operador"""
        
        if value is None:
            return value
        
        # Para 'in', espera una lista
        if operator == 'in':
            if isinstance(value, str):
                # Si es string separado por comas, convertir a lista
                return [v.strip() for v in value.split(',')]
            elif not isinstance(value, (list, tuple)):
                return [value]
        
        # Para rangos, espera dict
        if operator == 'range':
            if not isinstance(value, dict):
                raise DynamicFilterError(
                    f"range requiere dict, recibido: {type(value)}"
                )
        
        # Para fechas, convertir string a date/datetime
        if operator in ['lt', 'lte', 'gt', 'gte', 'range']:
            if isinstance(value, str):
                try:
                    # Intentar parsear como fecha
                    return datetime.fromisoformat(value).date()
                except (ValueError, AttributeError):
                    # Si no es fecha válida, devolver como está
                    return value
        
        return value
    
    @staticmethod
    def get_aggregations(queryset, agg_spec: dict):
        """
        Aplica agregaciones al queryset
        
        Args:
            queryset: Django QuerySet
            agg_spec: {
                'count': 'id',  # COUNT(id)
                'sum': 'amount',  # SUM(amount)
                'avg': 'price',   # AVG(price)
                'max': 'created_at',  # MAX(created_at)
                'min': 'price'    # MIN(price)
            }
        
        Returns:
            Dict con resultados: {'count': N, 'sum': X, ...}
        """
        annotations = {}
        
        if agg_spec.get('count'):
            annotations['count'] = Count(agg_spec['count'])
        
        if agg_spec.get('sum'):
            annotations['sum'] = Sum(agg_spec['sum'])
        
        if agg_spec.get('avg'):
            annotations['avg'] = Avg(agg_spec['avg'])
        
        if agg_spec.get('max'):
            annotations['max'] = Max(agg_spec['max'])
        
        if agg_spec.get('min'):
            annotations['min'] = Min(agg_spec['min'])
        
        return queryset.aggregate(**annotations)
    
    @staticmethod
    def build_filter_from_dict(filters_dict: dict) -> list:
        """
        Convierte un diccionario simple en lista de filtros
        
        Ejemplo:
        >>> filters = {'specialty': 'Cardiología', 'status': 'active'}
        >>> filter_list = DynamicFilter.build_filter_from_dict(filters)
        >>> print(filter_list)
        [
            {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'},
            {'field': 'status', 'operator': 'eq', 'value': 'active'}
        ]
        """
        filter_list = []
        
        for field, value in filters_dict.items():
            if value is None:
                continue
            
            filter_list.append({
                'field': field,
                'operator': 'eq',
                'value': value
            })
        
        return filter_list
