# 🎯 NEXT STEPS - US-3 BÚSQUEDA AVANZADA

## 📌 Status Actual

**Sprint 2:** 40% Completado (2/6 User Stories)

### ✅ Completadas
- **US-1:** Sistema de Notificaciones (100%)
- **US-2:** RBAC y Permisos Dinámicos (100%)

### 🔄 Próxima: US-3
- **US-3:** Búsqueda Avanzada (Planeado)

---

## 📋 US-3: BÚSQUEDA AVANZADA

### 🎯 Objetivo
Implementar un sistema de búsqueda avanzada con filtros, paginación y ordenamiento para todos los recursos principales (pacientes, historias clínicas, documentos).

### 📊 Estimación
- **Backend:** 6-7 horas
- **Frontend:** 6-7 horas
- **Testing:** 3-4 horas
- **Total:** 15-18 horas

### ✨ Características

#### Backend
1. **Filtros Avanzados**
   - Búsqueda por texto (nombre, email, ID, etc.)
   - Filtros por fecha (created_at, updated_at)
   - Filtros por estado (activo, inactivo)
   - Filtros multi-select

2. **Paginación Optimizada**
   - Cursor-based pagination
   - Offset-limit pagination
   - Page size configurable
   - Total count

3. **Ordenamiento**
   - Múltiples campos
   - Ascendente/descendente
   - Campos ordenables configurables

4. **Búsqueda de Texto Completo**
   - PostgreSQL full-text search
   - Ranking de resultados
   - Soporte de acentos

#### Frontend
1. **Componentes de Búsqueda**
   - SearchBar con autocomplete
   - FilterPanel con múltiples opciones
   - SortSelector
   - PaginationControls

2. **UX Mejorada**
   - Real-time search
   - Filtros predefinidos
   - Saved searches
   - Search history

3. **Performance**
   - Debounce en búsqueda
   - Lazy loading
   - Caching de resultados

---

## 🚀 ROADMAP TÉCNICO

### Fase 1: Backend Filters (Día 1)
```
├── Crear FilterBackend customizado
├── Implementar SearchFilter
├── Implementar OrderingFilter
├── Crear FilterSchema para cada modelo
└── Tests unitarios
```

### Fase 2: Backend Pagination (Día 2)
```
├── Implementar cursor-based pagination
├── Implementar offset-limit pagination
├── Agregar validaciones
├── Tests de paginación
└── Documentación
```

### Fase 3: Frontend SearchBar (Día 3)
```
├── Crear componente SearchBar
├── Integrar con API
├── Debounce implementation
├── Autocomplete
└── Tests de componentes
```

### Fase 4: Frontend FilterPanel (Día 3-4)
```
├── Crear componente FilterPanel
├── Crear FilterOptions
├── Manejar múltiples filtros
├── Persist filters en URL
└── Tests
```

### Fase 5: Optimizaciones (Día 4)
```
├── Caching de resultados
├── Lazy loading
├── Performance tuning
├── SEO optimizations
└── E2E tests
```

---

## 📝 ARCHIVOS A MODIFICAR/CREAR

### Backend

#### Nuevos Archivos
```
apps/core/
├── filters.py          # Filtros customizados
├── search.py           # Full-text search logic
└── pagination.py       # Paginación customizada

apps/patients/
├── filters.py          # Filters específicos para pacientes
└── tests/
    └── test_filters.py # Tests de filtros
```

#### Archivos a Modificar
```
apps/patients/
├── views.py            # Agregar filter_backends
├── serializers.py      # Serializers para búsqueda
└── urls.py             # Rutas nuevas

apps/clinical_records/
├── views.py            # Filtros
└── urls.py             # Rutas

apps/documents/
├── views.py            # Filtros
└── urls.py             # Rutas
```

### Frontend

#### Nuevos Archivos
```
src/shared/components/search/
├── SearchBar.tsx
├── FilterPanel.tsx
├── SortSelector.tsx
├── PaginationControls.tsx
└── index.ts

src/hooks/
├── useSearch.ts
├── useFilter.ts
├── useSort.ts
└── usePagination.ts

src/modules/patients/components/
├── PatientsSearchPage.tsx
└── PatientsFilters.tsx
```

#### Archivos a Modificar
```
src/modules/patients/
├── pages/PatientsPage.tsx
├── services/patients.service.ts
└── hooks/usePatients.ts
```

---

## 🔌 API ENDPOINTS (US-3)

### Búsqueda de Pacientes
```
GET /api/patients/
  ?search=john
  &status=active
  &date_from=2025-01-01
  &date_to=2025-01-31
  &ordering=-created_at
  &page=1
  &page_size=20
```

**Respuesta:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/patients/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john@example.com",
      "status": "active"
    }
  ]
}
```

### Búsqueda de Historias Clínicas
```
GET /api/clinical-records/
  ?search=diabetes
  &patient_id=uuid
  &date_from=2025-01-01
  &ordering=-updated_at
  &page=1
```

### Búsqueda de Documentos
```
GET /api/documents/
  ?search=prescription
  &type=pdf
  &clinical_record=uuid
  &signed=true
  &ordering=-created_at
```

---

## 💡 IMPLEMENTACIÓN RÁPIDA

### Backend Quick Setup

1. **Crear FilterBackend:**
```python
# apps/core/filters.py

from django_filters import FilterSet, CharFilter, DateFilter, ChoiceFilter
from rest_framework.filters import SearchFilter, OrderingFilter

class PatientFilterSet(FilterSet):
    search = CharFilter(field_name='first_name', lookup_expr='icontains')
    date_from = DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = DateFilter(field_name='created_at', lookup_expr='lte')
    status = ChoiceFilter(choices=[('active', 'Active'), ('inactive', 'Inactive')])
    
    class Meta:
        model = Patient
        fields = ['search', 'status', 'date_from', 'date_to']
```

2. **Agregar a ViewSet:**
```python
# apps/patients/views.py

from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class PatientViewSet(ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['first_name', 'last_name', 'email', 'identification']
    ordering_fields = ['created_at', 'updated_at', 'first_name']
    ordering = ['-created_at']
```

### Frontend Quick Setup

1. **Crear Hook useSearch:**
```typescript
// src/hooks/useSearch.ts

import { useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

export const useSearch = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const search = searchParams.get('search') || '';
  const page = parseInt(searchParams.get('page') || '1', 10);
  
  const setSearch = useCallback((value: string) => {
    setSearchParams(prev => {
      prev.set('search', value);
      prev.set('page', '1');
      return prev;
    });
  }, [setSearchParams]);
  
  return { search, page, setSearch };
};
```

2. **Usar en Componente:**
```typescript
// src/modules/patients/pages/PatientsPage.tsx

export const PatientsPage = () => {
  const { search, setSearch } = useSearch();
  const [patients, setPatients] = useState([]);
  
  useEffect(() => {
    const fetchPatients = async () => {
      const response = await patientsService.search({
        search,
        page: 1
      });
      setPatients(response.results);
    };
    
    fetchPatients();
  }, [search]);
  
  return (
    <div>
      <SearchBar value={search} onChange={setSearch} />
      <PatientsList patients={patients} />
    </div>
  );
};
```

---

## 🧪 TESTING PLAN

### Backend Tests
```python
# apps/patients/tests/test_filters.py

def test_patient_search_by_name():
    """Buscar pacientes por nombre"""
    Patient.objects.create(first_name='John', ...)
    response = client.get('/api/patients/?search=John')
    assert response.status_code == 200
    assert len(response.data['results']) == 1

def test_patient_filter_by_status():
    """Filtrar por estado"""
    response = client.get('/api/patients/?status=active')
    assert response.status_code == 200

def test_patient_pagination():
    """Verificar paginación"""
    # Crear 25 pacientes
    response = client.get('/api/patients/?page=1&page_size=10')
    assert len(response.data['results']) == 10
    assert response.data['next'] is not None

def test_patient_ordering():
    """Verificar ordenamiento"""
    response = client.get('/api/patients/?ordering=-created_at')
    assert response.status_code == 200
```

### Frontend Tests
```typescript
// src/modules/patients/__tests__/useSearch.test.ts

test('should search patients', async () => {
  const { result } = renderHook(() => useSearch());
  
  act(() => {
    result.current.setSearch('John');
  });
  
  expect(result.current.search).toBe('John');
});

test('should paginate', async () => {
  const { result } = renderHook(() => usePagination());
  
  act(() => {
    result.current.goToPage(2);
  });
  
  expect(result.current.page).toBe(2);
});
```

---

## 📊 DEFINICIÓN DE LISTO (DoD)

- [ ] Filtros backend implementados y testeados
- [ ] Paginación funciona correctamente
- [ ] Ordenamiento múltiple implementado
- [ ] SearchBar frontend creado y funcional
- [ ] FilterPanel implementado
- [ ] Búsqueda en tiempo real funciona
- [ ] URL persist filters
- [ ] Autocomplete funciona
- [ ] Tests unitarios: 90% coverage
- [ ] Tests E2E ejecutados y pasados
- [ ] Documentación actualizada
- [ ] Sin errores en consola
- [ ] Performance aceptable (<500ms)
- [ ] Mobile responsive
- [ ] Accesibilidad WCAG 2.1

---

## 🎓 RECURSOS ÚTILES

### Django Filters
- [Documentation](https://django-filter.readthedocs.io/)
- [GitHub](https://github.com/carltongibson/django-filter)

### PostgreSQL Full-Text Search
- [Django Docs](https://docs.djangoproject.com/en/4.2/ref/contrib/postgres/search/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/current/textsearch.html)

### React Search
- [Use Debounce Hook](https://github.com/xnimorz/use-debounce)
- [Use URL Search Params](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)

---

## 📅 TIMELINE

| Fase | Duración | Inicio | Fin |
|------|----------|--------|-----|
| Planning | 2 horas | Hoy | Hoy |
| Backend Implementation | 6 horas | Mañana | Mañana |
| Frontend Implementation | 6 horas | Pasado mañana | Pasado mañana |
| Testing & QA | 3 horas | Day 4 | Day 4 |
| Documentation | 2 horas | Day 5 | Day 5 |
| **Total** | **19 horas** | **Hoy** | **Día 5** |

---

## 🚀 PRÓXIMAS USER STORIES

Después de US-3 (Búsqueda Avanzada):

### US-4: Reportes Avanzados (15-18 horas)
- Generación de reportes PDF/Excel
- Filtros avanzados en reportes
- Plantillas personalizadas
- Scheduling de reportes

### US-5: Exportación de Datos (8-10 horas)
- Export a Excel, CSV, PDF
- Batch export
- Scheduled exports
- Download management

### US-6: Analytics Dashboard (12-15 horas)
- Dashboard de estadísticas
- Gráficos interactivos
- Real-time metrics
- Custom dashboards

---

## 💬 PREGUNTAS FRECUENTES

**¿Por qué cursor-based pagination?**
- Mejor performance con datasets grandes
- Protege contra cambios durante paginación

**¿Cómo manejo 1M+ de registros?**
- Índices en campos filtrados
- Caching de resultados
- Elastic Search (futuro)

**¿Debo usar Elastic Search?**
- No es necesario para inicio
- PostgreSQL full-text search es suficiente
- Migrar a Elastic en US-7+

---

**Status:** 🟡 Planeado para próxima iteración  
**Dependencias:** US-2 (RBAC) ✅  
**Bloqueadores:** Ninguno  
**Prioridad:** Alta  
**Complejidad:** Media  

---

**Documento creado:** Noviembre 2025  
**Versión:** 1.0.0  
**Próxima revisión:** Al iniciar US-3
