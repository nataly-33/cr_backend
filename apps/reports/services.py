"""
AI Analysis Service para manejar análisis de reportes con IA
"""
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional

from apps.reports.llm_adapter import LLMManager
from apps.reports.models import AIAnalysis, ReportExecution


class AIAnalysisService:
    """Servicio para análisis de reportes con IA"""
    
    def __init__(self):
        self.llm_manager = LLMManager()
    
    def analyze_report(
        self, 
        execution: ReportExecution, 
        analysis: Optional[AIAnalysis] = None
    ) -> AIAnalysis:
        """
        Analizar un reporte con IA
        
        Args:
            execution: ReportExecution a analizar
            analysis: AIAnalysis existente (opcional)
            
        Returns:
            AIAnalysis actualizado
        """
        try:
            # Crear si no existe
            if not analysis:
                analysis, _ = AIAnalysis.objects.get_or_create(
                    report_execution=execution
                )
            
            # Obtener datos del reporte
            report_data = self._get_report_data(execution)
            
            # Generar análisis con LLM
            analysis_text = self.llm_manager.analyze(report_data)
            
            # Parsear respuesta
            parsed = self._parse_analysis(analysis_text)
            
            # Guardar en base de datos
            analysis.analysis = parsed['analysis']
            analysis.insights = parsed['insights']
            analysis.key_findings = parsed['key_findings']
            analysis.confidence_score = parsed.get('confidence_score', 0.85)
            analysis.status = 'completed'
            analysis.error_message = None
            analysis.save()
            
            return analysis
            
        except Exception as e:
            if analysis:
                analysis.status = 'failed'
                analysis.error_message = str(e)
                analysis.save()
            raise
    
    def generate_summary(
        self, 
        execution: ReportExecution, 
        max_length: int = 500
    ) -> Dict[str, Any]:
        """
        Generar resumen con IA
        
        Args:
            execution: ReportExecution
            max_length: Máxima longitud del resumen
            
        Returns:
            Dict con datos del resumen
        """
        try:
            # Obtener datos del reporte
            report_data = self._get_report_data(execution)
            
            # Generar resumen con LLM
            summary_text = self.llm_manager.summarize(report_data, max_length)
            
            # Extraer puntos clave
            key_points = self._extract_key_points(summary_text)
            
            return {
                'id': str(execution.id),
                'summary': summary_text,
                'key_points': key_points,
                'length': len(summary_text.split()),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Error generando resumen: {str(e)}")
    
    def get_recommendations(
        self, 
        execution: ReportExecution
    ) -> List[Dict[str, Any]]:
        """
        Obtener recomendaciones con IA
        
        Args:
            execution: ReportExecution
            
        Returns:
            Lista de recomendaciones
        """
        try:
            # Obtener datos del reporte
            report_data = self._get_report_data(execution)
            
            # Generar recomendaciones con LLM
            recommendations_text = self.llm_manager.get_recommendations(report_data)
            
            # Parsear recomendaciones
            recommendations = self._parse_recommendations(recommendations_text)
            
            return recommendations
            
        except Exception as e:
            raise Exception(f"Error obteniendo recomendaciones: {str(e)}")
    
    def get_complete_insights(
        self, 
        execution: ReportExecution
    ) -> Dict[str, Any]:
        """
        Obtener insights completos (análisis + resumen + recomendaciones)
        
        Args:
            execution: ReportExecution
            
        Returns:
            Dict con todos los insights
        """
        try:
            # Obtener o crear análisis
            analysis, _ = AIAnalysis.objects.get_or_create(
                report_execution=execution
            )
            
            # Ejecutar análisis si no está completado
            if analysis.status == 'pending':
                analysis = self.analyze_report(execution, analysis)
            
            # Generar resumen
            summary = self.generate_summary(execution)
            
            # Obtener recomendaciones
            recommendations = self.get_recommendations(execution)
            
            # Serializar análisis
            analysis_data = self._serialize_analysis(analysis)
            
            return {
                'analysis': analysis_data,
                'summary': summary,
                'recommendations': recommendations,
                'status': 'completed',
                'message': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'analysis': None,
                'summary': None,
                'recommendations': None
            }
    
    # ============ Helper Methods ============
    
    def _get_report_data(self, execution: ReportExecution) -> str:
        """
        Extraer datos del reporte para análisis
        
        Args:
            execution: ReportExecution
            
        Returns:
            String con datos del reporte
        """
        # Este método debe ser implementado según tu estructura de datos
        # Por ahora retorna información básica del reporte
        
        report_info = f"""
        Report Type: {execution.template.report_type if execution.template else 'Unknown'}
        Format: {execution.output_format}
        Status: {execution.status}
        Generated: {execution.created_at}
        Rows: {execution.rows_returned or 'Unknown'}
        Parameters: {json.dumps(execution.parameters_used, indent=2)}
        """
        
        return report_info.strip()
    
    def _parse_analysis(self, text: str) -> Dict[str, Any]:
        """
        Parsear respuesta de análisis del LLM
        
        Args:
            text: Respuesta de LLM
            
        Returns:
            Dict con análisis parseado
        """
        return {
            'analysis': text,
            'insights': self._extract_insights(text),
            'key_findings': self._extract_key_findings(text),
            'confidence_score': 0.85
        }
    
    def _extract_insights(self, text: str) -> List[str]:
        """
        Extraer insights del texto
        
        Args:
            text: Texto de análisis
            
        Returns:
            Lista de insights
        """
        # Dividir por líneas y filtrar vacías
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Retornar primeras 5 líneas como insights
        return lines[:5] if len(lines) > 5 else lines
    
    def _extract_key_findings(self, text: str) -> List[str]:
        """
        Extraer hallazgos clave del texto
        
        Args:
            text: Texto de análisis
            
        Returns:
            Lista de hallazgos clave
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Retornar primeras 3 líneas como hallazgos clave
        return lines[:3] if len(lines) > 3 else lines
    
    def _extract_key_points(self, text: str) -> List[str]:
        """
        Extraer puntos clave del resumen
        
        Args:
            text: Texto de resumen
            
        Returns:
            Lista de puntos clave
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Retornar primeras 5 líneas como puntos clave
        return lines[:5] if len(lines) > 5 else lines
    
    def _parse_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """
        Parsear recomendaciones del LLM
        
        Args:
            text: Respuesta de LLM
            
        Returns:
            Lista de recomendaciones
        """
        try:
            # Intentar parsear como JSON
            data = json.loads(text)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
        
        # Si no es JSON, crear recomendaciones a partir del texto
        recommendations = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for idx, line in enumerate(lines[:5]):
            recommendations.append({
                'id': f"rec-{idx}",
                'recommendation': line,
                'priority': self._determine_priority(line),
                'category': 'general',
                'action_items': []
            })
        
        return recommendations
    
    def _determine_priority(self, text: str) -> str:
        """
        Determinar prioridad de una recomendación basada en keywords
        
        Args:
            text: Texto de recomendación
            
        Returns:
            Prioridad (critical, high, medium, low)
        """
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['crítico', 'urgente', 'inmediato', 'critical', 'urgent']):
            return 'critical'
        elif any(word in text_lower for word in ['importante', 'recomendado', 'important', 'recommend']):
            return 'high'
        elif any(word in text_lower for word in ['considerar', 'opcional', 'consider', 'optional']):
            return 'medium'
        else:
            return 'low'
    
    def _serialize_analysis(self, analysis: AIAnalysis) -> Dict[str, Any]:
        """
        Serializar modelo AIAnalysis
        
        Args:
            analysis: Instancia de AIAnalysis
            
        Returns:
            Dict serializado
        """
        return {
            'id': str(analysis.id),
            'report_id': str(analysis.report_execution_id),
            'analysis': analysis.analysis,
            'insights': analysis.insights,
            'key_findings': analysis.key_findings,
            'confidence_score': analysis.confidence_score,
            'generated_at': analysis.created_at.isoformat()
        }
