"""
Servicio para parsear lenguaje natural a SQL usando IA
Soporta OpenAI y modelos locales con fallback automático
"""
import json
import logging
import re
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from django.conf import settings
from django.apps import apps

logger = logging.getLogger(__name__)


class NLPParserService:
    """
    Servicio principal para convertir lenguaje natural a SQL
    Con soporte para OpenAI y fallback local
    """
    
    # Mapeo de tablas disponibles
    AVAILABLE_TABLES = {
        'patient': {
            'model': 'patients.Patient',
            'fields': [
                'id', 'identity_document_type', 'identity_document',
                'first_name', 'last_name', 'date_of_birth', 'gender',
                'phone', 'email', 'address', 'city', 'created_at'
            ],
            'searchable': ['first_name', 'last_name', 'email', 'identity_document'],
            'aliases': ['paciente', 'pacientes', 'patient', 'patients']
        },
        'clinical_record': {
            'model': 'clinical_records.ClinicalRecord',
            'fields': [
                'id', 'record_number', 'status', 'blood_type',
                'allergies', 'current_medications', 'family_history',
                'social_history', 'created_at', 'patient_id'
            ],
            'joins': {
                'patient': 'patient__',
            },
            'searchable': ['record_number', 'status'],
            'aliases': ['historia', 'historias', 'historia clínica', 'historias clínicas', 
                       'clinical_record', 'clinical records']
        },
        'clinical_form': {
            'model': 'clinical_records.ClinicalForm',
            'fields': [
                'id', 'form_type', 'form_number', 'form_date',
                'doctor_name', 'doctor_specialty', 'doctor_license',
                'created_at', 'clinical_record_id', 'filled_by_id'
            ],
            'joins': {
                'clinical_record': 'clinical_record__',
                'patient': 'clinical_record__patient__',
            },
            'searchable': ['form_type', 'form_number', 'doctor_name'],
            'aliases': ['formulario', 'formularios', 'form', 'forms',
                       'triage', 'consulta', 'receta', 'lab_order', 
                       'orden de laboratorio', 'orden de imagenología', 'ordenes', 'órdenes',
                       'prescription', 'procedimiento', 'imaging_order']
        },
        'document': {
            'model': 'documents.ClinicalDocument',
            'fields': [
                'id', 'document_type', 'title', 'description',
                'document_date', 'specialty', 'doctor_name',
                'doctor_license', 'file_name', 'mime_type',
                'is_signed', 'created_at', 'clinical_record_id'
            ],
            'joins': {
                'clinical_record': 'clinical_record__',
                'patient': 'clinical_record__patient__',
            },
            'searchable': ['document_type', 'title', 'doctor_name'],
            'aliases': ['documento', 'documentos', 'document', 'documents']
        },
        'user': {
            'model': 'accounts.User',
            'fields': [
                'id', 'email', 'username', 'first_name', 'last_name',
                'phone', 'gender', 'birth_date', 'professional_id',
                'specialty', 'is_active', 'is_staff', 'created_at'
            ],
            'searchable': ['email', 'first_name', 'last_name', 'specialty'],
            'aliases': ['usuario', 'usuarios', 'user', 'users', 'doctor', 'doctores', 'personal', 'staff']
        },
    }
    
    def __init__(self, ai_provider='openai'):
        """
        Inicializar servicio NLP
        
        Args:
            ai_provider: 'openai' (recomendado) o 'local'
        """
        self.ai_provider = ai_provider
        self.client = None
        
        # Intentar inicializar proveedor solicitado
        if ai_provider == 'openai':
            self._init_openai()
        else:
            logger.info("Using local NLP parser (rule-based)")
    
    def _init_openai(self):
        """Inicializar cliente OpenAI"""
        try:
            import openai
            api_key = getattr(settings, 'OPENAI_API_KEY', None)
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized successfully")
            else:
                logger.warning("OPENAI_API_KEY not configured - will use local parser")
                self.ai_provider = 'local'
        except ImportError:
            logger.error("openai package not installed. Install with: pip install openai")
            self.ai_provider = 'local'
        except Exception as e:
            logger.error(f"OpenAI initialization error: {e}")
            self.ai_provider = 'local'
    
    def parse_query(self, query_text: str, language: str = 'es') -> Dict:
        """
        Parsear consulta en lenguaje natural a SQL
        
        Args:
            query_text: Texto de la consulta
            language: Idioma (es, en)
        
        Returns:
            {
                'sql': 'SELECT ...',
                'params': {...},
                'confidence': 0.95,
                'table': 'patient',
                'explanation': '...',
                'provider': 'bedrock'
            }
        """
        # Validar entrada
        if not query_text or not query_text.strip():
            return {
                'sql': '',
                'params': {},
                'confidence': 0.0,
                'table_name': None,
                'explanation': 'Consulta vacía',
                'provider': 'error',
                'error': 'La consulta no puede estar vacía'
            }
        
        max_length = getattr(settings, 'REPORTS_AI_MAX_QUERY_LENGTH', 5000)
        if len(query_text) > max_length:
            return {
                'sql': '',
                'params': {},
                'confidence': 0.0,
                'table_name': None,
                'explanation': 'Consulta demasiado larga',
                'provider': 'error',
                'error': f'La consulta no puede exceder {max_length} caracteres'
            }
        
        # Detectar los 3 reportes críticos predefinidos
        critical_report = self._detect_critical_report(query_text)
        if critical_report:
            return critical_report
        
        # Intentar parsing con OpenAI si está disponible
        if self.ai_provider == 'openai' and self.client:
            try:
                return self._parse_with_openai(query_text, language)
            except Exception as e:
                logger.warning(f"OpenAI parsing failed: {e}. Falling back to local parser")
                return self._parse_with_rules(query_text, language)
        else:
            return self._parse_with_rules(query_text, language)
    
    def _detect_critical_report(self, query_text: str) -> Optional[Dict]:
        """
        Detectar reportes de historias clínicas con flexible pattern matching
        Soporta variaciones: blood type, ordenamiento ASC/DESC, etc.
        """
        query_lower = query_text.lower()
        
        # PATRÓN 1: Historias clínicas con filtro (noviembre, blood type, etc) ordenadas por paciente
        if ('historia' in query_lower or 'historias' in query_lower or 'clinical' in query_lower or 'record' in query_lower):
            # Detectar si tiene ordenamiento
            has_desc = 'descend' in query_lower or ' desc' in query_lower
            order_dir = 'DESC' if has_desc else 'ASC'
            
            # Detectar filtro de mes
            month_filter = ''
            if 'noviembre' in query_lower or 'november' in query_lower:
                month_filter = "WHERE EXTRACT(MONTH FROM cr.created_at) = 11 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            elif 'octubre' in query_lower or 'october' in query_lower:
                month_filter = "WHERE EXTRACT(MONTH FROM cr.created_at) = 10 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            elif 'septiembre' in query_lower or 'september' in query_lower:
                month_filter = "WHERE EXTRACT(MONTH FROM cr.created_at) = 9 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            elif 'diciembre' in query_lower or 'december' in query_lower:
                month_filter = "WHERE EXTRACT(MONTH FROM cr.created_at) = 12 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            
            # Detectar filtro de blood type
            blood_filter = ''
            if 'ab' in query_lower:
                blood_filter = "WHERE cr.blood_type LIKE 'AB%'"
            elif 'o+' in query_lower or 'o-' in query_lower or ' o ' in query_lower:
                blood_filter = "WHERE cr.blood_type LIKE 'O%'"
            elif 'a+' in query_lower or 'a-' in query_lower:
                blood_filter = "WHERE cr.blood_type LIKE 'A%'"
            elif 'b+' in query_lower or 'b-' in query_lower:
                blood_filter = "WHERE cr.blood_type LIKE 'B%'"
            
            # Si no hay blood filter pero sí hay filtro de mes y es de historias
            if blood_filter and month_filter:
                # Combinar: blood type + mes (usar AND)
                final_filter = f"{month_filter.replace('WHERE', '')} AND {blood_filter.split('WHERE')[1]}"
                final_filter = f"WHERE {final_filter}"
            elif blood_filter:
                final_filter = blood_filter
            elif month_filter:
                final_filter = month_filter
            else:
                final_filter = ""
            
            # Solo generar si tiene algún filtro significativo
            if final_filter or ('noviembre' in query_lower or 'november' in query_lower):
                sql = f"""
SELECT 
    cr.id,
    cr.record_number,
    p.first_name,
    p.last_name,
    cr.blood_type,
    cr.status,
    cr.created_at
FROM clinical_record cr
JOIN patient p ON cr.patient_id = p.id
{final_filter}
ORDER BY p.first_name {order_dir}, p.last_name {order_dir}
                """
                
                return {
                    'sql': sql,
                    'params': {},
                    'confidence': 0.95,
                    'table_name': 'clinical_record',
                    'explanation': f'Reporte de historias clínicas ({order_dir})',
                    'provider': 'critical_report',
                    'estimated_rows': 500
                }
        
        # PATRÓN 2: Cantidad de visitas por pacientes (con mes flexible)
        if ('cantidad' in query_lower or 'count' in query_lower or 'número' in query_lower or 'cuántos' in query_lower or 'cuantos' in query_lower or 'cuántas' in query_lower or 'cuantas' in query_lower) and \
           ('visitas' in query_lower or 'formularios' in query_lower or 'forms' in query_lower or 'consultas' in query_lower or 'pacientes' in query_lower):
            
            # Detectar mes
            month_range = "cf.created_at >= '2025-11-01' AND cf.created_at < '2025-12-01'"
            if 'octubre' in query_lower or 'october' in query_lower:
                month_range = "cf.created_at >= '2025-10-01' AND cf.created_at < '2025-11-01'"
            elif 'septiembre' in query_lower or 'september' in query_lower:
                month_range = "cf.created_at >= '2025-09-01' AND cf.created_at < '2025-10-01'"
            elif 'diciembre' in query_lower or 'december' in query_lower:
                month_range = "cf.created_at >= '2025-12-01' AND cf.created_at < '2026-01-01'"
            
            # Detectar ordenamiento
            has_desc = 'descend' in query_lower or ' desc' in query_lower
            order_dir = 'DESC' if has_desc else 'ASC'
            
            sql = f"""
SELECT 
    p.id,
    p.first_name,
    p.last_name,
    COUNT(cf.id) as cantidad_formularios,
    MAX(cf.created_at) as ultima_visita
FROM patient p
LEFT JOIN clinical_record cr ON p.id = cr.patient_id
LEFT JOIN clinical_form cf ON cr.id = cf.clinical_record_id
    AND {month_range}
WHERE EXISTS (
    SELECT 1 FROM clinical_record cr2
    JOIN clinical_form cf2 ON cr2.id = cf2.clinical_record_id
    WHERE cr2.patient_id = p.id 
    AND {month_range}
)
GROUP BY p.id, p.first_name, p.last_name
ORDER BY p.first_name {order_dir}, p.last_name {order_dir}
            """
            
            return {
                'sql': sql,
                'params': {},
                'confidence': 0.95,
                'table_name': 'patient',
                'explanation': 'Cantidad de formularios por paciente',
                'provider': 'critical_report',
                'estimated_rows': 800
            }
        
        return None
    
    def _parse_with_openai(self, query_text: str, language: str) -> Dict:
        """Parsear usando OpenAI GPT"""
        start_time = time.time()
        prompt = self._build_prompt(query_text, language)
        
        try:
            model = getattr(settings, 'OPENAI_MODEL', 'gpt-4-mini')
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un experto en SQL y bases de datos médicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            parsing_time = int((time.time() - start_time) * 1000)
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Validar estructura mínima
                if 'sql' not in result:
                    result['sql'] = ''
                if 'params' not in result:
                    result['params'] = {}
                if 'confidence' not in result:
                    result['confidence'] = 0.85
                if 'table_name' not in result:
                    result['table_name'] = None
                if 'explanation' not in result:
                    result['explanation'] = 'Query generada por OpenAI'
                if 'estimated_rows' not in result:
                    result['estimated_rows'] = 100
                
                result['provider'] = 'openai'
                result['parsing_time_ms'] = parsing_time
                
                logger.info(f"OpenAI query parsed successfully ({parsing_time}ms)")
                return result
            else:
                raise ValueError("Could not extract JSON from OpenAI response")
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in OpenAI response: {e}")
            raise ValueError("Invalid JSON in OpenAI response")
        except Exception as e:
            logger.error(f"Error in OpenAI parsing: {e}")
            raise
    
    
    def _build_prompt(self, query_text: str, language: str) -> str:
        """Construir prompt optimizado para OpenAI"""
        schema_description = self._get_schema_description()
        
        # Lenguaje del prompt
        if language == 'es':
            lang_instructions = """
IDIOMA: Español

INSTRUCCIONES:
1. Genera una consulta SQL válida y segura (SOLO SELECT, NO DELETE/DROP/UPDATE)
2. Usa los nombres de tabla y campos EXACTOS del esquema
3. Aplica filtros apropiados basados en el texto de la consulta
4. Si el usuario no especifica límite, usa máximo 100 filas
5. Usa JOINs inteligentemente si se necesitan datos de múltiples tablas
6. Maneja fechas correctamente (formato YYYY-MM-DD)
7. Limpia y valida todos los parámetros contra SQL injection
8. Retorna SOLO JSON válido sin explicación adicional
"""
        else:
            lang_instructions = """
LANGUAGE: English

INSTRUCTIONS:
1. Generate safe, valid SQL query (SELECT ONLY, NO DELETE/DROP/UPDATE)
2. Use EXACT table and field names from schema
3. Apply appropriate filters based on query text
4. If no limit specified, use maximum 100 rows
5. Use JOINs intelligently if data from multiple tables needed
6. Handle dates correctly (format YYYY-MM-DD)
7. Clean and validate all parameters against SQL injection
8. Return ONLY valid JSON without additional explanation
"""
        
        prompt = f"""You are an expert SQL generator for healthcare systems. Convert natural language queries to safe, efficient SQL.

DATABASE SCHEMA:
{schema_description}

USER QUERY:
"{query_text}"

{lang_instructions}

RESPOND WITH ONLY THIS JSON STRUCTURE:
{{
    "sql": "SELECT ... FROM ...",
    "params": {{}},
    "confidence": 0.95,
    "table_name": "patient",
    "explanation": "Query explanation in {language}",
    "estimated_rows": 100
}}

Remember: ONLY SELECT queries. ONLY JSON in response. NO EXPLANATIONS OUTSIDE JSON."""
        
        return prompt
    
    
    def _get_schema_description(self) -> str:
        """Obtener descripción concisa del esquema de BD"""
        desc = []
        for table_name, table_info in self.AVAILABLE_TABLES.items():
            fields_str = ', '.join(table_info['fields'][:8])  # Primeros 8 campos
            if len(table_info['fields']) > 8:
                fields_str += f", ..."
            aliases_str = ', '.join(table_info['aliases'][:3])  # Primeros 3 alias
            
            desc.append(f"TABLE: {table_name}")
            desc.append(f"  Fields: {fields_str}")
            desc.append(f"  Aliases: {aliases_str}")
            if 'joins' in table_info:
                desc.append(f"  Can JOIN with: {', '.join(table_info['joins'].keys())}")
            
        return '\n'.join(desc)
    
    def _call_openai(self, prompt: str) -> Dict:
        """Llamar a OpenAI GPT con manejo de errores"""
        try:
            model = getattr(settings, 'OPENAI_MODEL', 'gpt-4-mini')
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Eres un experto en SQL y bases de datos médicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000,
            )
            
            content = response.choices[0].message.content
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Validar estructura mínima
                if 'sql' not in result:
                    result['sql'] = ''
                if 'params' not in result:
                    result['params'] = {}
                if 'confidence' not in result:
                    result['confidence'] = 0.85
                if 'table_name' not in result:
                    result['table_name'] = None
                if 'explanation' not in result:
                    result['explanation'] = 'Query generada por OpenAI'
                if 'estimated_rows' not in result:
                    result['estimated_rows'] = 100
                
                return result
            else:
                raise ValueError("No se pudo extraer JSON de la respuesta de OpenAI")
        
        except Exception as e:
            logger.error(f"OpenAI parsing error: {e}")
            raise
    
    def _parse_with_rules(self, query_text: str, language: str) -> Dict:
        """
        Parsear usando reglas heurísticas (fallback cuando no hay IA)
        Más robusto y confiable que la versión anterior
        """
        query_lower = query_text.lower()
        
        # 1. Detectar tabla principal
        table_name = self._detect_table(query_lower)
        if not table_name:
            return {
                'sql': '',
                'params': {},
                'confidence': 0.0,
                'table_name': None,
                'explanation': 'No se pudo determinar qué tabla consultar',
                'provider': 'local',
                'error': 'Tabla no identificada'
            }
        
        table_info = self.AVAILABLE_TABLES[table_name]
        
        # 2. Detectar campos a seleccionar
        fields = self._detect_fields(query_lower, table_info)
        
        # 3. Detectar filtros (fechas, valores, etc.)
        filters, params = self._detect_filters(query_lower, table_info)
        
        # 4. Detectar límite
        limit = self._detect_limit(query_lower)
        
        # 5. Construir SQL
        model_name = table_info['model']
        app_label, model_class_name = model_name.split('.')
        table_db_name = self._get_db_table_name(app_label, model_class_name)
        
        select_clause = ', '.join(fields) if fields else '*'
        sql_parts = [f"SELECT {select_clause} FROM {table_db_name}"]
        
        if filters:
            sql_parts.append(f"WHERE {' AND '.join(filters)}")
        
        sql_parts.append(f"ORDER BY created_at DESC")
        sql_parts.append(f"LIMIT {limit}")
        
        sql = ' '.join(sql_parts)
        
        return {
            'sql': sql,
            'params': params,
            'confidence': 0.6,  # Confianza menor para parser local
            'table_name': table_name,
            'explanation': f'Consulta a tabla {table_name} con {len(filters)} filtros',
            'estimated_rows': limit,
            'provider': 'local'
        }
    
    def _detect_table(self, query_lower: str) -> Optional[str]:
        """Detectar tabla a partir de alias en el texto"""
        for table_name, table_info in self.AVAILABLE_TABLES.items():
            for alias in table_info['aliases']:
                if alias.lower() in query_lower:
                    return table_name
        return None
    
    def _detect_fields(self, query_lower: str, table_info: Dict) -> List[str]:
        """Detectar campos mencionados en el query"""
        detected_fields = []
        
        for field in table_info['fields']:
            field_clean = field.replace('_', ' ')
            if field in query_lower or field_clean in query_lower:
                detected_fields.append(field)
        
        if not detected_fields:
            defaults = {
                'patient': ['id', 'first_name', 'last_name', 'email', 'identity_document', 'created_at'],
                'clinical_record': ['id', 'record_number', 'status', 'blood_type', 'created_at'],
                'clinical_form': ['id', 'form_type', 'form_number', 'form_date', 'doctor_name', 'created_at'],
                'document': ['id', 'document_type', 'title', 'document_date', 'doctor_name', 'created_at'],
                'user': ['id', 'email', 'first_name', 'last_name', 'specialty', 'created_at'],
            }
            model_key = table_info.get('model', '').split('.')[-1].lower()
            return defaults.get(model_key, ['*'])
        
        return detected_fields
    
    def _detect_filters(self, query_lower: str, table_info: Dict) -> Tuple[List[str], Dict]:
        """Detectar filtros con mejor soporte de operadores, status y booleanos"""
        filters = []
        params = {}
        
        # Filtros de fecha
        date_filters, date_params = self._extract_date_filters(query_lower)
        filters.extend(date_filters)
        params.update(date_params)
        
        # Filtros de status/estado
        if 'pendiente' in query_lower or 'pending' in query_lower:
            filters.append("status = %(status)s")
            params['status'] = 'pending'
        elif 'completado' in query_lower or 'completed' in query_lower:
            filters.append("status = %(status)s")
            params['status'] = 'completed'
        elif 'activo' in query_lower or 'active' in query_lower:
            filters.append("is_active = true")
        
        # Filtros booleanos
        if 'sin firma' in query_lower or 'no firmado' in query_lower:
            filters.append("is_signed = false")
        elif 'firmado' in query_lower or 'con firma' in query_lower:
            filters.append("is_signed = true")
        
        if 'email verificado' in query_lower or 'verificado' in query_lower:
            filters.append("email_verified = true")
        
        if 'staff' in query_lower or 'personal médico' in query_lower or 'médico' in query_lower:
            if table_info.get('model') == 'accounts.User':
                filters.append("is_staff = true")
        
        # Filtros de especialidad
        specialty_match = re.search(r'especialidad\s+(\w+)', query_lower)
        if specialty_match:
            specialty = specialty_match.group(1).capitalize()
            filters.append("specialty LIKE %(specialty)s")
            params['specialty'] = f"%{specialty}%"
        
        # Filtros por nombre/apellido (búsqueda flexible)
        name_match = re.search(r'(Dr\.|doctor|doctora)\s+(\w+)', query_lower)
        if name_match:
            name = name_match.group(2).capitalize()
            # Buscar en doctor_name o first_name/last_name según tabla
            if 'doctor_name' in table_info.get('fields', []):
                filters.append("doctor_name LIKE %(doctor_name)s")
                params['doctor_name'] = f"%{name}%"
            elif 'first_name' in table_info.get('fields', []):
                filters.append("(first_name LIKE %(name)s OR last_name LIKE %(name)s)")
                params['name'] = f"%{name}%"
        
        # Filtros de tipo de formulario
        form_type_match = re.search(r'(lab_order|triage|prescription|consulta|receta|orden|imaging|imagenología)', query_lower)
        if form_type_match and 'form_type' in table_info.get('fields', []):
            form_type_map = {
                'lab_order': 'lab_order',
                'orden': 'lab_order',
                'triage': 'triage',
                'prescription': 'prescription',
                'receta': 'prescription',
                'consulta': 'consultation',
                'imaging': 'imaging_order',
                'imagenología': 'imaging_order',
                'imagenologia': 'imaging_order'
            }
            form_type = form_type_map.get(form_type_match.group(1), form_type_match.group(1))
            filters.append("form_type = %(form_type)s")
            params['form_type'] = form_type
        
        # Filtros de tipo de documento
        doc_type_match = re.search(r'(historia|informe|orden|receta)', query_lower)
        if doc_type_match and 'document_type' in table_info.get('fields', []):
            doc_type_map = {
                'historia': 'Historia Clínica',
                'informe': 'Informe',
                'orden': 'Orden',
                'receta': 'Receta'
            }
            doc_type = doc_type_map.get(doc_type_match.group(1), doc_type_match.group(1).capitalize())
            filters.append("document_type LIKE %(document_type)s")
            params['document_type'] = f"%{doc_type}%"
        
        # Filtros de OCR
        if 'ocr' in query_lower:
            if 'exitoso' in query_lower or 'procesado' in query_lower or 'completed' in query_lower:
                filters.append("ocr_status = 'completed'")
        
        # Filtros genéricos de búsqueda en campos configurados
        for field in table_info.get('searchable', []):
            if field in ['doctor_name', 'first_name', 'last_name']:  # Ya manejados arriba
                continue
            pattern = rf"{field}[:\s]+([\w@.-]+)"
            match = re.search(pattern, query_lower)
            if match:
                value = match.group(1)
                filters.append(f"{field} LIKE %({field})s")
                params[field] = f"%{value}%"
        
        return filters, params
    
    def _extract_date_filters(self, query_lower: str) -> Tuple[List[str], Dict]:
        """Extraer filtros de fecha mejorado"""
        filters = []
        params = {}
        
        months_es = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }
        
        months_en = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        
        all_months = {**months_es, **months_en}
        year_match = re.search(r'(20\d{2})', query_lower)
        year = year_match.group(1) if year_match else str(datetime.now().year)
        
        # Rango entre meses
        range_match = re.search(r'entre\s+(\w+)\s+y\s+(\w+)', query_lower)
        if range_match:
            month_start = range_match.group(1)
            month_end = range_match.group(2)
            
            if month_start in all_months and month_end in all_months:
                date_from = f"{year}-{all_months[month_start]}-01"
                month_num = int(all_months[month_end])
                if month_num == 12:
                    date_to = f"{int(year)+1}-01-01"
                else:
                    date_to = f"{year}-{str(month_num+1).zfill(2)}-01"
                
                filters.append("created_at >= %(date_from)s")
                filters.append("created_at < %(date_to)s")
                params['date_from'] = date_from
                params['date_to'] = date_to
                return filters, params
        
        # Un mes específico
        for month_name, month_num in all_months.items():
            if f' {month_name} ' in f' {query_lower} ' or query_lower.endswith(month_name):
                date_from = f"{year}-{month_num}-01"
                month_num_int = int(month_num)
                if month_num_int == 12:
                    date_to = f"{int(year)+1}-01-01"
                else:
                    date_to = f"{year}-{str(month_num_int+1).zfill(2)}-01"
                
                filters.append("created_at >= %(date_from)s")
                filters.append("created_at < %(date_to)s")
                params['date_from'] = date_from
                params['date_to'] = date_to
                return filters, params
        
        # Fechas explícitas
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, query_lower)
        if dates:
            if len(dates) >= 2:
                filters.append("created_at >= %(date_from)s")
                filters.append("created_at <= %(date_to)s")
                params['date_from'] = dates[0]
                params['date_to'] = dates[1]
            elif len(dates) == 1:
                filters.append("created_at >= %(date_from)s")
                params['date_from'] = dates[0]
        
        return filters, params
    
    def _detect_limit(self, query_lower: str) -> int:
        """Detectar límite de resultados"""
        patterns = [
            r'máximo\s+(\d+)',
            r'limit\s+(\d+)',
            r'primeros?\s+(\d+)',
            r'top\s+(\d+)',
            r'primeras?\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                limit = int(match.group(1))
                max_rows = getattr(settings, 'REPORTS_AI_MAX_ROWS', 1000)
                return min(limit, max_rows)
        
        return 100
    
    def _get_db_table_name(self, app_label: str, model_name: str) -> str:
        """Obtener nombre de tabla en la BD"""
        try:
            model = apps.get_model(app_label, model_name)
            return model._meta.db_table
        except:
            return f"{app_label}_{model_name.lower()}"
    
    def validate_sql(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validar que el SQL sea seguro
        
        Returns:
            (is_valid, error_message)
        """
        if not sql:
            return False, "SQL vacío"
        
        sql_upper = sql.upper().strip()
        
        # 1. Solo permitir SELECT
        if not sql_upper.startswith('SELECT'):
            return False, "Solo se permiten consultas SELECT"
        
        # 2. Prohibir operaciones peligrosas (buscar como palabra completa, no en campos como created_at)
        dangerous_keywords = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b', r'\bALTER\b',
            r'\bCREATE\s+TABLE\b', r'\bCREATE\s+DATABASE\b', r'\bCREATE\s+INDEX\b',
            r'\bTRUNCATE\b', r'\bEXEC\b', r'\bEXECUTE\b'
        ]
        
        for pattern in dangerous_keywords:
            if re.search(pattern, sql_upper):
                keyword = pattern.replace(r'\b', '').replace(r'\s+', ' ')
                return False, f"Operación prohibida: {keyword}"
        
        # Prohibir comentarios SQL que puedan ocultar inyecciones
        if '--' in sql or '/*' in sql:
            return False, "No se permiten comentarios SQL"
        
        # 3. Validar múltiples queries
        if ';' in sql and not sql.rstrip().endswith(';'):
            return False, "No se permiten múltiples consultas"
        
        # 4. Límite de longitud
        max_length = getattr(settings, 'REPORTS_AI_MAX_QUERY_LENGTH', 5000)
        if len(sql) > max_length:
            return False, f"Consulta demasiado larga (máx {max_length} caracteres)"
        
        return True, None
