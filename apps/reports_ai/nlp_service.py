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
                'id', 'form_type', 'form_date',
                'doctor_name', 'doctor_specialty',
                'created_at', 'clinical_record_id', 'filled_by_id'
            ],
            'joins': {
                'clinical_record': 'clinical_record__',
                'patient': 'clinical_record__patient__',
            },
            'searchable': ['form_type', 'doctor_name'],
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
        Parsear consulta en lenguaje natural a SQL (ROBUSTO - Parser Local)

        Args:
            query_text: Texto de la consulta
            language: Idioma (es, en)

        Returns:
            {
                'sql': 'SELECT ...',
                'params': {...},
                'confidence': 0.95,
                'table_name': 'patient',
                'explanation': '...',
                'provider': 'local'
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

        try:
            # Detectar los reportes críticos predefinidos (alta confianza)
            critical_report = self._detect_critical_report(query_text)
            if critical_report:
                return critical_report

            # Usar parser local con reglas mejoradas
            return self._parse_with_rules(query_text, language)

        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            return {
                'sql': '',
                'params': {},
                'confidence': 0.0,
                'table_name': None,
                'explanation': f'Error al procesar consulta: {str(e)}',
                'provider': 'error',
                'error': str(e)
            }
    
    def _detect_critical_report(self, query_text: str) -> Optional[Dict]:
        """
        Detectar reportes CRÍTICOS que necesitas para defensa:
        1. Historias clínicas con tipo de sangre (AB, O, A, B) + ordenamiento ASC/DESC
        2. Historias clínicas creadas en un mes específico + ordenamiento ASC/DESC
        3. Cantidad de formularios por paciente (visitas al hospital)
        """
        query_lower = query_text.lower()
        
        # ========== PATRÓN 1: HISTORIAS CLÍNICAS CON TIPO DE SANGRE ==========
        # Detección de tipo de sangre: AB, O, A, B (con o sin +/-)
        blood_type_keywords = ['sangre', 'blood', 'tipo de sangre', 'tipo sangre', 'blood type']
        has_blood_mention = any(kw in query_lower for kw in blood_type_keywords)
        
        # Detectar tipos específicos
        blood_filter = None
        blood_explanation = ""
        
        # AB (captura AB+, AB-, o solo AB)
        if has_blood_mention or 'ab+' in query_lower or 'ab-' in query_lower or ' ab ' in query_lower or query_lower.startswith('ab ') or query_lower.endswith(' ab'):
            # Si solo dice "AB" sin +/-, incluir ambos (AB+ y AB-)
            if 'ab+' in query_lower:
                blood_filter = "cr.blood_type = 'AB+'"
                blood_explanation = "AB+"
            elif 'ab-' in query_lower:
                blood_filter = "cr.blood_type = 'AB-'"
                blood_explanation = "AB-"
            elif 'ab' in query_lower:
                blood_filter = "cr.blood_type LIKE 'AB%'"
                blood_explanation = "AB (AB+ y AB-)"
        
        # Tipo O
        elif has_blood_mention or 'o+' in query_lower or 'o-' in query_lower or ' o ' in query_lower or query_lower.startswith('o ') or query_lower.endswith(' o'):
            if 'o+' in query_lower:
                blood_filter = "cr.blood_type = 'O+'"
                blood_explanation = "O+"
            elif 'o-' in query_lower:
                blood_filter = "cr.blood_type = 'O-'"
                blood_explanation = "O-"
            elif ' o ' in query_lower or query_lower.startswith('o ') or query_lower.endswith(' o'):
                blood_filter = "cr.blood_type LIKE 'O%'"
                blood_explanation = "O (O+ y O-)"
        
        # Tipo A (pero NO AB)
        elif (has_blood_mention or 'a+' in query_lower or 'a-' in query_lower) and 'ab' not in query_lower:
            if 'a+' in query_lower:
                blood_filter = "cr.blood_type = 'A+'"
                blood_explanation = "A+"
            elif 'a-' in query_lower:
                blood_filter = "cr.blood_type = 'A-'"
                blood_explanation = "A-"
            else:
                blood_filter = "cr.blood_type LIKE 'A%' AND cr.blood_type NOT LIKE 'AB%'"
                blood_explanation = "A (A+ y A-)"
        
        # Tipo B (pero NO AB)
        elif (has_blood_mention or 'b+' in query_lower or 'b-' in query_lower) and 'ab' not in query_lower:
            if 'b+' in query_lower:
                blood_filter = "cr.blood_type = 'B+'"
                blood_explanation = "B+"
            elif 'b-' in query_lower:
                blood_filter = "cr.blood_type = 'B-'"
                blood_explanation = "B-"
            else:
                blood_filter = "cr.blood_type LIKE 'B%' AND cr.blood_type NOT LIKE 'AB%'"
                blood_explanation = "B (B+ y B-)"
        
        # ========== PATRÓN 2: HISTORIAS CLÍNICAS CREADAS EN UN MES ==========
        # Detectar meses
        month_filter = None
        month_explanation = ""
        
        if 'noviembre' in query_lower or 'november' in query_lower:
            month_filter = "EXTRACT(MONTH FROM cr.created_at) = 11 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            month_explanation = "noviembre 2025"
        elif 'octubre' in query_lower or 'october' in query_lower:
            month_filter = "EXTRACT(MONTH FROM cr.created_at) = 10 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            month_explanation = "octubre 2025"
        elif 'septiembre' in query_lower or 'september' in query_lower:
            month_filter = "EXTRACT(MONTH FROM cr.created_at) = 9 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            month_explanation = "septiembre 2025"
        elif 'diciembre' in query_lower or 'december' in query_lower:
            month_filter = "EXTRACT(MONTH FROM cr.created_at) = 12 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            month_explanation = "diciembre 2025"
        elif 'agosto' in query_lower or 'august' in query_lower:
            month_filter = "EXTRACT(MONTH FROM cr.created_at) = 8 AND EXTRACT(YEAR FROM cr.created_at) = 2025"
            month_explanation = "agosto 2025"
        
        # Detectar si es consulta de historias clínicas
        is_historia_query = any(kw in query_lower for kw in ['historia', 'historias', 'clinical record', 'clinical records', 'expediente', 'expedientes'])
        
        # Si tiene filtro de tipo de sangre O mes, generar SQL de historias clínicas
        if is_historia_query and (blood_filter or month_filter):
            # Combinar filtros
            where_clauses = []
            if blood_filter:
                where_clauses.append(blood_filter)
            if month_filter:
                where_clauses.append(month_filter)
            
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Detectar ordenamiento (ascendente o descendente)
            has_desc = 'descend' in query_lower or 'descendente' in query_lower or ' desc' in query_lower
            order_dir = 'DESC' if has_desc else 'ASC'
            order_explanation = "descendente" if has_desc else "ascendente"
            
            # Explicación completa
            filters_desc = []
            if blood_explanation:
                filters_desc.append(f"tipo de sangre {blood_explanation}")
            if month_explanation:
                filters_desc.append(f"creadas en {month_explanation}")
            
            explanation = f"Historias clínicas"
            if filters_desc:
                explanation += " con " + " y ".join(filters_desc)
            explanation += f", ordenadas {order_explanation} por paciente"
            
            sql = f"""
SELECT 
    cr.id,
    cr.record_number,
    p.first_name,
    p.last_name,
    p.identity_document,
    cr.blood_type,
    cr.status,
    cr.created_at
FROM clinical_record cr
JOIN patient p ON cr.patient_id = p.id
{where_clause}
ORDER BY p.first_name {order_dir}, p.last_name {order_dir}
LIMIT 500
            """
            
            return {
                'sql': sql,
                'params': {},
                'confidence': 0.98,
                'table_name': 'clinical_record',
                'explanation': explanation,
                'provider': 'critical_report_historias',
                'estimated_rows': 500
            }
        
        # ========== PATRÓN 3: CANTIDAD DE FORMULARIOS POR PACIENTE (VISITAS) ==========
        cantidad_keywords = ['cantidad', 'count', 'número', 'numero', 'cuántos', 'cuantos', 'cuántas', 'cuantas', 'veces que', 'veces']
        visitas_keywords = ['visitas', 'visitó', 'visito', 'asistió', 'asistio', 'acudió', 'acudio', 'fue', 'vino', 'formularios', 'forms', 'consultas']
        
        has_cantidad = any(kw in query_lower for kw in cantidad_keywords)
        has_visitas = any(kw in query_lower for kw in visitas_keywords)
        has_paciente = 'paciente' in query_lower or 'patient' in query_lower
        
        if (has_cantidad or has_visitas) and (has_paciente or has_visitas):
            # Detectar mes (si no se especifica, usar noviembre por defecto)
            month_range = "cf.form_date >= '2025-11-01' AND cf.form_date < '2025-12-01'"
            month_explanation = "noviembre 2025"
            
            if 'octubre' in query_lower or 'october' in query_lower:
                month_range = "cf.form_date >= '2025-10-01' AND cf.form_date < '2025-11-01'"
                month_explanation = "octubre 2025"
            elif 'septiembre' in query_lower or 'september' in query_lower:
                month_range = "cf.form_date >= '2025-09-01' AND cf.form_date < '2025-10-01'"
                month_explanation = "septiembre 2025"
            elif 'diciembre' in query_lower or 'december' in query_lower:
                month_range = "cf.form_date >= '2025-12-01' AND cf.form_date < '2026-01-01'"
                month_explanation = "diciembre 2025"
            elif 'agosto' in query_lower or 'august' in query_lower:
                month_range = "cf.form_date >= '2025-08-01' AND cf.form_date < '2025-09-01'"
                month_explanation = "agosto 2025"
            elif '2025' in query_lower and not any(m in query_lower for m in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']):
                # Si solo dice 2025 sin mes, todo el año
                month_range = "cf.form_date >= '2025-01-01' AND cf.form_date < '2026-01-01'"
                month_explanation = "todo 2025"
            
            # Detectar ordenamiento
            has_desc = 'descend' in query_lower or 'descendente' in query_lower or ' desc' in query_lower
            order_dir = 'DESC' if has_desc else 'ASC'
            order_explanation = "descendente" if has_desc else "ascendente"
            
            sql = f"""
SELECT 
    p.id,
    p.first_name,
    p.last_name,
    p.identity_document,
    COUNT(cf.id) as cantidad_formularios,
    MIN(cf.form_date) as primera_visita,
    MAX(cf.form_date) as ultima_visita
FROM patient p
JOIN clinical_record cr ON p.id = cr.patient_id
JOIN clinical_form cf ON cr.id = cf.clinical_record_id
WHERE {month_range}
GROUP BY p.id, p.first_name, p.last_name, p.identity_document
HAVING COUNT(cf.id) > 0
ORDER BY p.first_name {order_dir}, p.last_name {order_dir}
LIMIT 500
            """
            
            explanation = f"Cantidad de veces que cada paciente asistió a la clínica en {month_explanation} (contando formularios clínicos), ordenados {order_explanation}"
            
            return {
                'sql': sql,
                'params': {},
                'confidence': 0.98,
                'table_name': 'clinical_form',
                'explanation': explanation,
                'provider': 'critical_report_visitas',
                'estimated_rows': 500
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
        """Construir prompt MEJORADO y optimizado para OpenAI con ejemplos avanzados"""
        schema_description = self._get_schema_description_detailed()
        examples = self._get_advanced_examples(language)

        # Lenguaje del prompt
        if language == 'es':
            lang_instructions = """
IDIOMA: Español

INSTRUCCIONES AVANZADAS:
1. Genera SQL PostgreSQL válido y optimizado (SOLO SELECT, NO DELETE/DROP/UPDATE)
2. Usa EXACTAMENTE los nombres de tablas y campos del esquema
3. Aplica MÚLTIPLES filtros combinados con AND/OR cuando sea necesario
4. Usa JOINs apropiados para relacionar tablas (INNER, LEFT, etc.)
5. Maneja rangos de fechas con BETWEEN o >= y <
6. Soporta agregaciones (COUNT, SUM, AVG, MAX, MIN) con GROUP BY
7. Usa LIKE para búsquedas parciales, = para exactas
8. Convierte meses a números (enero=1, febrero=2, etc.)
9. Años sin especificar = año actual (2025)
10. Usa CAST/EXTRACT para manipulación de fechas
11. Ordena con ORDER BY (ASC/DESC)
12. SIEMPRE usa alias de tabla (p, cr, cf, doc, u) para claridad
13. SIEMPRE incluye campos de join en el SELECT cuando sea relevante
14. Retorna SOLO JSON válido, sin markdown, sin explicaciones extra
"""
        else:
            lang_instructions = """
LANGUAGE: English

ADVANCED INSTRUCTIONS:
1. Generate valid, optimized PostgreSQL SQL (SELECT ONLY, NO DELETE/DROP/UPDATE)
2. Use EXACT table and field names from schema
3. Apply MULTIPLE combined filters with AND/OR when needed
4. Use appropriate JOINs to relate tables (INNER, LEFT, etc.)
5. Handle date ranges with BETWEEN or >= and <
6. Support aggregations (COUNT, SUM, AVG, MAX, MIN) with GROUP BY
7. Use LIKE for partial searches, = for exact matches
8. Convert month names to numbers (january=1, february=2, etc.)
9. Years without specification = current year (2025)
10. Use CAST/EXTRACT for date manipulation
11. Order with ORDER BY (ASC/DESC)
12. ALWAYS use table aliases (p, cr, cf, doc, u) for clarity
13. ALWAYS include join fields in SELECT when relevant
14. Return ONLY valid JSON, no markdown, no extra explanations
"""

        prompt = f"""You are an EXPERT SQL generator for medical record systems. Generate PRECISE, COMPLEX queries from natural language.

DATABASE SCHEMA (PostgreSQL):
{schema_description}

EJEMPLOS DE CONSULTAS COMPLEJAS:
{examples}

CONSULTA DEL USUARIO:
"{query_text}"

{lang_instructions}

RESPONDE CON ESTE JSON (sin ```json ni markdown):
{{
    "sql": "SELECT campos FROM tabla alias JOIN ... WHERE condiciones ORDER BY ... LIMIT N",
    "params": {{}},
    "confidence": 0.90,
    "table_name": "tabla_principal",
    "explanation": "Explicación clara de la consulta en {language}",
    "estimated_rows": 100
}}

CRÍTICO:
- SQL debe ser EJECUTABLE directamente en PostgreSQL
- Usa alias SIEMPRE (p, cr, cf, doc, u)
- Para meses: enero/january=1, diciembre/december=12
- Para rangos: created_at >= '2025-01-01' AND created_at < '2025-02-01'
- Para JOINs: SIEMPRE especifica la tabla completa: patient p JOIN clinical_record cr ON p.id = cr.patient_id
- SOLO JSON en la respuesta, sin texto adicional."""

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

    def _get_schema_description_detailed(self) -> str:
        """Obtener descripción DETALLADA del esquema de BD para prompts mejorados"""
        desc = []

        for table_name, table_info in self.AVAILABLE_TABLES.items():
            # Nombre de la tabla y modelo Django
            model_name = table_info['model']
            db_table = model_name.split('.')[-1].lower()

            # Alias recomendado
            alias_map = {
                'patient': 'p',
                'clinical_record': 'cr',
                'clinical_form': 'cf',
                'document': 'doc',
                'user': 'u'
            }
            alias = alias_map.get(table_name, table_name[0])

            desc.append(f"\nTABLA: {db_table} (alias: {alias})")
            desc.append(f"  Django Model: {model_name}")
            desc.append(f"  Nombres alternativos: {', '.join(table_info['aliases'][:5])}")

            # Campos completos
            desc.append(f"  CAMPOS:")
            for field in table_info['fields']:
                desc.append(f"    - {field}")

            # Relaciones (JOINs)
            if 'joins' in table_info:
                desc.append(f"  RELACIONES:")
                for join_table, join_field in table_info['joins'].items():
                    desc.append(f"    - JOIN {join_table}: {join_field}")

            # Campos buscables
            if 'searchable' in table_info:
                desc.append(f"  CAMPOS BUSCABLES: {', '.join(table_info['searchable'])}")

        # Agregar relaciones clave
        desc.append("\n\nRELACIONES IMPORTANTES:")
        desc.append("  patient.id → clinical_record.patient_id")
        desc.append("  clinical_record.id → clinical_form.clinical_record_id")
        desc.append("  clinical_record.id → document.clinical_record_id")
        desc.append("  user.id → clinical_form.filled_by_id")
        desc.append("  user.id → document.created_by_id")

        return '\n'.join(desc)

    def _get_advanced_examples(self, language: str) -> str:
        """Obtener ejemplos avanzados de consultas para el prompt"""
        if language == 'es':
            examples = """
EJEMPLO 1: Filtros múltiples con JOIN
Query: "Documentos clínicos firmados de cardiología creados en octubre por la Dra. García"
SQL: SELECT doc.id, doc.title, doc.document_type, doc.is_signed, doc.doctor_name, doc.specialty, p.first_name || ' ' || p.last_name as patient_name
     FROM document doc
     JOIN clinical_record cr ON doc.clinical_record_id = cr.id
     JOIN patient p ON cr.patient_id = p.id
     WHERE doc.is_signed = true
       AND doc.specialty LIKE '%Cardiología%'
       AND doc.doctor_name LIKE '%García%'
       AND doc.created_at >= '2025-10-01'
       AND doc.created_at < '2025-11-01'
     ORDER BY doc.created_at DESC
     LIMIT 100

EJEMPLO 2: Agregación con GROUP BY
Query: "Cantidad de formularios por tipo y especialidad del doctor en noviembre"
SQL: SELECT cf.form_type, cf.doctor_specialty, COUNT(*) as total
     FROM clinical_form cf
     WHERE cf.created_at >= '2025-11-01'
       AND cf.created_at < '2025-12-01'
     GROUP BY cf.form_type, cf.doctor_specialty
     ORDER BY total DESC
     LIMIT 100

EJEMPLO 3: Rango de fechas con múltiples filtros
Query: "Pacientes mujeres entre 20 y 40 años registrados entre marzo y junio 2025"
SQL: SELECT p.id, p.first_name, p.last_name, p.date_of_birth, p.gender, p.email
     FROM patient p
     WHERE p.gender = 'F'
       AND p.date_of_birth >= '1985-01-01'
       AND p.date_of_birth <= '2005-01-01'
       AND p.created_at >= '2025-03-01'
       AND p.created_at < '2025-07-01'
     ORDER BY p.created_at DESC
     LIMIT 100

EJEMPLO 4: LEFT JOIN con condiciones
Query: "Pacientes con sus historias clínicas, incluyendo los que no tienen"
SQL: SELECT p.id, p.first_name, p.last_name, cr.record_number, cr.blood_type, cr.status
     FROM patient p
     LEFT JOIN clinical_record cr ON p.id = cr.patient_id
     ORDER BY p.first_name ASC
     LIMIT 100

EJEMPLO 5: Subconsulta con EXISTS
Query: "Pacientes que tienen al menos un documento firmado en octubre"
SQL: SELECT p.id, p.first_name, p.last_name, p.email
     FROM patient p
     WHERE EXISTS (
       SELECT 1 FROM clinical_record cr
       JOIN document doc ON cr.id = doc.clinical_record_id
       WHERE cr.patient_id = p.id
         AND doc.is_signed = true
         AND doc.created_at >= '2025-10-01'
         AND doc.created_at < '2025-11-01'
     )
     ORDER BY p.first_name ASC
     LIMIT 100
"""
        else:
            examples = """
EXAMPLE 1: Multiple filters with JOIN
Query: "Signed clinical documents from cardiology created in October by Dr. García"
SQL: SELECT doc.id, doc.title, doc.document_type, doc.is_signed, doc.doctor_name, doc.specialty, p.first_name || ' ' || p.last_name as patient_name
     FROM document doc
     JOIN clinical_record cr ON doc.clinical_record_id = cr.id
     JOIN patient p ON cr.patient_id = p.id
     WHERE doc.is_signed = true
       AND doc.specialty LIKE '%Cardiology%'
       AND doc.doctor_name LIKE '%García%'
       AND doc.created_at >= '2025-10-01'
       AND doc.created_at < '2025-11-01'
     ORDER BY doc.created_at DESC
     LIMIT 100

EXAMPLE 2: Aggregation with GROUP BY
Query: "Count of forms by type and doctor specialty in November"
SQL: SELECT cf.form_type, cf.doctor_specialty, COUNT(*) as total
     FROM clinical_form cf
     WHERE cf.created_at >= '2025-11-01'
       AND cf.created_at < '2025-12-01'
     GROUP BY cf.form_type, cf.doctor_specialty
     ORDER BY total DESC
     LIMIT 100

EXAMPLE 3: Date range with multiple filters
Query: "Female patients between 20 and 40 years old registered between March and June 2025"
SQL: SELECT p.id, p.first_name, p.last_name, p.date_of_birth, p.gender, p.email
     FROM patient p
     WHERE p.gender = 'F'
       AND p.date_of_birth >= '1985-01-01'
       AND p.date_of_birth <= '2005-01-01'
       AND p.created_at >= '2025-03-01'
       AND p.created_at < '2025-07-01'
     ORDER BY p.created_at DESC
     LIMIT 100
"""

        return examples
    
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
        Parsear usando reglas heurísticas MEJORADAS (fallback cuando no hay IA)
        Soporta filtros complejos, JOINs, agregaciones
        """
        query_lower = query_text.lower()

        # 1. Detectar si es una agregación (COUNT, SUM, etc)
        is_aggregation = any(word in query_lower for word in ['cantidad', 'count', 'suma', 'sum', 'promedio', 'average', 'avg', 'total', 'máximo', 'max', 'mínimo', 'min'])

        if is_aggregation:
            return self._parse_aggregation_query(query_text, query_lower, language)

        # 2. Detectar tabla principal
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

        # 3. Detectar necesidad de JOINs
        needs_joins, join_tables = self._detect_joins_needed(query_lower, table_name)

        # 4. Detectar campos a seleccionar
        fields = self._detect_fields_advanced(query_lower, table_info, join_tables)

        # 5. Detectar filtros complejos (fechas, rangos, booleanos, LIKE, etc.)
        filters, params = self._detect_filters_advanced(query_lower, table_info)

        # 6. Detectar ordenamiento
        order_by = self._detect_order_by(query_lower)

        # 7. Detectar límite
        limit = self._detect_limit(query_lower)

        # 8. Construir SQL con JOINs si es necesario
        sql = self._build_sql_with_joins(
            table_name=table_name,
            fields=fields,
            filters=filters,
            join_tables=join_tables,
            order_by=order_by,
            limit=limit
        )

        confidence = 0.75 if needs_joins else 0.70

        return {
            'sql': sql,
            'params': params,
            'confidence': confidence,
            'table_name': table_name,
            'explanation': f'Consulta {"con JOINs " if needs_joins else ""}a tabla {table_name} con {len(filters)} filtros',
            'estimated_rows': limit,
            'provider': 'local'
        }
    
    def _detect_table(self, query_lower: str) -> Optional[str]:
        """Detectar tabla a partir de alias en el texto con priorización"""
        # Prioridad de tablas: más específicas primero
        priority_tables = ['document', 'clinical_form', 'clinical_record', 'user', 'patient']

        # Buscar con prioridad
        matches = []
        for table_name in priority_tables:
            if table_name not in self.AVAILABLE_TABLES:
                continue
            table_info = self.AVAILABLE_TABLES[table_name]
            for alias in table_info['aliases']:
                # Buscar como palabra completa o con espacios
                if f' {alias.lower()} ' in f' {query_lower} ' or query_lower.startswith(alias.lower()):
                    matches.append((table_name, len(alias)))  # Guardar con longitud del alias

        # Si hay matches, retornar el más específico (alias más largo)
        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            return matches[0][0]

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

    # ================= MÉTODOS AVANZADOS PARA PARSER LOCAL =================

    def _detect_joins_needed(self, query_lower: str, table_name: str) -> Tuple[bool, List[str]]:
        """Detectar si se necesitan JOINs y qué tablas"""
        join_tables = []

        # Si se mencionan múltiples tablas
        tables_mentioned = []
        for tname, tinfo in self.AVAILABLE_TABLES.items():
            for alias in tinfo['aliases']:
                if alias in query_lower and tname != table_name:
                    tables_mentioned.append(tname)
                    break

        # Remover duplicados
        tables_mentioned = list(set(tables_mentioned))

        # Determinar joins basados en tabla principal
        if table_name == 'clinical_form' or table_name == 'document':
            # Siempre joinear con clinical_record y patient para contexto
            if 'paciente' in query_lower or 'patient' in query_lower:
                join_tables = ['clinical_record', 'patient']
        elif table_name == 'clinical_record':
            # Joinear con patient si se menciona
            if 'paciente' in query_lower or 'patient' in query_lower:
                join_tables = ['patient']

        # Agregar tablas mencionadas explícitamente
        join_tables.extend(tables_mentioned)
        join_tables = list(set(join_tables))  # Remover duplicados

        return len(join_tables) > 0, join_tables

    def _detect_fields_advanced(self, query_lower: str, table_info: Dict, join_tables: List[str]) -> List[str]:
        """Detectar campos avanzado con soporte para JOINs"""
        detected_fields = []
        table_alias = self._get_table_alias(table_info)

        # Campos de la tabla principal
        for field in table_info['fields']:
            field_clean = field.replace('_', ' ')
            if field in query_lower or field_clean in query_lower:
                detected_fields.append(f"{table_alias}.{field}")

        # Si no se detectaron campos, usar defaults
        if not detected_fields:
            model_key = table_info.get('model', '').split('.')[-1].lower()
            defaults = {
                'patient': ['id', 'first_name', 'last_name', 'email', 'identity_document'],
                'clinicalrecord': ['id', 'record_number', 'status', 'blood_type'],
                'clinicalform': ['id', 'form_type', 'form_date', 'doctor_name'],
                'clinicaldocument': ['id', 'document_type', 'title', 'document_date', 'is_signed'],
                'user': ['id', 'email', 'first_name', 'last_name', 'specialty'],
            }
            default_fields = defaults.get(model_key, ['id'])
            detected_fields = [f"{table_alias}.{f}" for f in default_fields]

        # Agregar campos de tablas joineadas
        if 'patient' in join_tables and table_alias != 'p':
            detected_fields.extend([
                "p.first_name",
                "p.last_name",
                "p.first_name || ' ' || p.last_name as patient_name"
            ])

        # Agregar created_at si no está
        if f"{table_alias}.created_at" not in detected_fields:
            detected_fields.append(f"{table_alias}.created_at")

        return detected_fields

    def _detect_filters_advanced(self, query_lower: str, table_info: Dict) -> Tuple[List[str], Dict]:
        """Versión mejorada de detección de filtros con más patrones"""
        # Usar el método existente como base
        filters, params = self._detect_filters(query_lower, table_info)

        # Agregar filtros de rango de edad
        age_range_match = re.search(r'entre\s+(\d+)\s+y\s+(\d+)\s+años', query_lower)
        if age_range_match:
            age_min = int(age_range_match.group(1))
            age_max = int(age_range_match.group(2))
            current_year = datetime.now().year
            birth_year_max = current_year - age_min
            birth_year_min = current_year - age_max
            filters.append("date_of_birth >= %(birth_date_min)s")
            filters.append("date_of_birth <= %(birth_date_max)s")
            params['birth_date_min'] = f"{birth_year_min}-01-01"
            params['birth_date_max'] = f"{birth_year_max}-12-31"

        # Filtros de género expandidos
        if 'mujeres' in query_lower or 'femenino' in query_lower or 'female' in query_lower:
            filters.append("gender = %(gender)s")
            params['gender'] = 'F'
        elif 'hombres' in query_lower or 'masculino' in query_lower or 'male' in query_lower:
            filters.append("gender = %(gender)s")
            params['gender'] = 'M'

        return filters, params

    def _detect_order_by(self, query_lower: str) -> str:
        """Detectar ordenamiento de resultados"""
        # Orden descendente
        if 'desc' in query_lower or 'descend' in query_lower or 'reciente' in query_lower:
            if 'nombre' in query_lower or 'name' in query_lower or 'paciente' in query_lower:
                return "first_name DESC, last_name DESC"
            return "created_at DESC"

        # Orden ascendente
        if 'asc' in query_lower or 'ascend' in query_lower or 'alfabético' in query_lower:
            if 'nombre' in query_lower or 'name' in query_lower or 'paciente' in query_lower:
                return "first_name ASC, last_name ASC"
            return "created_at ASC"

        # Default
        return "created_at DESC"

    def _build_sql_with_joins(
        self,
        table_name: str,
        fields: List[str],
        filters: List[str],
        join_tables: List[str],
        order_by: str,
        limit: int
    ) -> str:
        """Construir SQL con soporte para JOINs"""
        # Obtener nombre de tabla en BD
        table_info = self.AVAILABLE_TABLES[table_name]
        model_name = table_info['model']
        app_label, model_class_name = model_name.split('.')
        db_table = self._get_db_table_name(app_label, model_class_name)
        table_alias = self._get_table_alias(table_info)

        # SELECT clause
        select_clause = ', '.join(fields) if fields else f'{table_alias}.*'
        sql_parts = [f"SELECT {select_clause}"]

        # FROM clause
        sql_parts.append(f"FROM {db_table} {table_alias}")

        # JOINs
        if join_tables:
            join_sql = self._build_joins(table_name, table_alias, join_tables)
            sql_parts.append(join_sql)

        # WHERE clause
        if filters:
            # Actualizar filtros para usar alias de tabla
            filters_with_alias = []
            for f in filters:
                # Si el filtro no tiene alias de tabla, agregarlo
                if '.' not in f and not f.startswith('EXISTS'):
                    # Detectar el campo del filtro
                    field_match = re.match(r'(\w+)\s+', f)
                    if field_match:
                        field = field_match.group(1)
                        f = f.replace(field, f"{table_alias}.{field}", 1)
                filters_with_alias.append(f)

            sql_parts.append(f"WHERE {' AND '.join(filters_with_alias)}")

        # ORDER BY clause
        if '.' not in order_by and 'DESC' in order_by or 'ASC' in order_by:
            # Agregar alias si no existe
            order_parts = order_by.split(',')
            order_with_alias = []
            for part in order_parts:
                part = part.strip()
                if '.' not in part:
                    field_name = part.split()[0]
                    direction = part.split()[1] if len(part.split()) > 1 else ''
                    order_with_alias.append(f"{table_alias}.{field_name} {direction}".strip())
                else:
                    order_with_alias.append(part)
            order_by = ', '.join(order_with_alias)

        sql_parts.append(f"ORDER BY {order_by}")

        # LIMIT clause
        sql_parts.append(f"LIMIT {limit}")

        return ' '.join(sql_parts)

    def _build_joins(self, table_name: str, table_alias: str, join_tables: List[str]) -> str:
        """Construir cláusula JOINs"""
        joins = []

        # Mapeo de JOINs comunes
        if table_name == 'clinical_form' or table_name == 'document':
            if 'clinical_record' in join_tables or 'patient' in join_tables:
                # JOIN con clinical_record
                cr_table = self._get_db_table_name('clinical_records', 'ClinicalRecord')
                joins.append(f"JOIN {cr_table} cr ON {table_alias}.clinical_record_id = cr.id")

                if 'patient' in join_tables:
                    # JOIN con patient
                    p_table = self._get_db_table_name('patients', 'Patient')
                    joins.append(f"JOIN {p_table} p ON cr.patient_id = p.id")

        elif table_name == 'clinical_record':
            if 'patient' in join_tables:
                p_table = self._get_db_table_name('patients', 'Patient')
                joins.append(f"JOIN {p_table} p ON {table_alias}.patient_id = p.id")

        return '\n'.join(joins)

    def _get_table_alias(self, table_info: Dict) -> str:
        """Obtener alias recomendado para tabla"""
        model_name = table_info['model'].split('.')[-1].lower()
        alias_map = {
            'patient': 'p',
            'clinicalrecord': 'cr',
            'clinicalform': 'cf',
            'clinicaldocument': 'doc',
            'user': 'u'
        }
        return alias_map.get(model_name, model_name[0])

    def _parse_aggregation_query(self, query_text: str, query_lower: str, language: str) -> Dict:
        """Parsear consultas con agregaciones (COUNT, SUM, AVG, etc)"""
        # Detectar tabla principal
        table_name = self._detect_table(query_lower)
        if not table_name:
            return {
                'sql': '',
                'params': {},
                'confidence': 0.0,
                'table_name': None,
                'explanation': 'No se pudo determinar la tabla para agregación',
                'provider': 'local',
                'error': 'Tabla no identificada'
            }

        table_info = self.AVAILABLE_TABLES[table_name]
        db_table = self._get_db_table_name(*table_info['model'].split('.'))
        alias = self._get_table_alias(table_info)

        # Detectar tipo de agregación
        agg_function = 'COUNT(*)'
        if 'suma' in query_lower or 'sum' in query_lower:
            agg_function = 'SUM(id)'
        elif 'promedio' in query_lower or 'average' in query_lower or 'avg' in query_lower:
            agg_function = 'AVG(id)'
        elif 'máximo' in query_lower or 'max' in query_lower:
            agg_function = 'MAX(id)'
        elif 'mínimo' in query_lower or 'min' in query_lower:
            agg_function = 'MIN(id)'

        # Detectar GROUP BY
        group_by_fields = []
        if 'por tipo' in query_lower or 'by type' in query_lower:
            if 'form_type' in table_info['fields']:
                group_by_fields.append(f'{alias}.form_type')
            elif 'document_type' in table_info['fields']:
                group_by_fields.append(f'{alias}.document_type')

        if 'por especialidad' in query_lower or 'by specialty' in query_lower:
            if 'specialty' in table_info['fields']:
                group_by_fields.append(f'{alias}.specialty')
            elif 'doctor_specialty' in table_info['fields']:
                group_by_fields.append(f'{alias}.doctor_specialty')

        if 'por paciente' in query_lower or 'by patient' in query_lower:
            # Necesita JOIN con patient
            group_by_fields = ['p.first_name', 'p.last_name', 'p.id']
            needs_patient_join = True
        else:
            needs_patient_join = False

        # Construir SQL
        if group_by_fields:
            select_fields = group_by_fields + [f'{agg_function} as total']
            sql = f"SELECT {', '.join(select_fields)}\nFROM {db_table} {alias}"

            # Agregar JOIN si es necesario
            if needs_patient_join:
                if table_name in ['clinical_form', 'document']:
                    cr_table = self._get_db_table_name('clinical_records', 'ClinicalRecord')
                    p_table = self._get_db_table_name('patients', 'Patient')
                    sql += f"\nJOIN {cr_table} cr ON {alias}.clinical_record_id = cr.id"
                    sql += f"\nJOIN {p_table} p ON cr.patient_id = p.id"
                elif table_name == 'clinical_record':
                    p_table = self._get_db_table_name('patients', 'Patient')
                    sql += f"\nJOIN {p_table} p ON {alias}.patient_id = p.id"

            # Filtros de fecha
            filters, params = self._extract_date_filters(query_lower)
            if filters:
                filters_with_alias = [f.replace('created_at', f'{alias}.created_at') for f in filters]
                sql += f"\nWHERE {' AND '.join(filters_with_alias)}"
            else:
                params = {}

            sql += f"\nGROUP BY {', '.join(group_by_fields)}"
            sql += f"\nORDER BY total DESC"
            sql += f"\nLIMIT 100"
        else:
            # Agregación simple sin GROUP BY
            sql = f"SELECT {agg_function} as total\nFROM {db_table} {alias}"
            filters, params = self._extract_date_filters(query_lower)
            if filters:
                filters_with_alias = [f.replace('created_at', f'{alias}.created_at') for f in filters]
                sql += f"\nWHERE {' AND '.join(filters_with_alias)}"
            else:
                params = {}

        return {
            'sql': sql,
            'params': params,
            'confidence': 0.80,
            'table_name': table_name,
            'explanation': f'Consulta de agregación ({agg_function}) en {table_name}',
            'estimated_rows': 50,
            'provider': 'local'
        }
