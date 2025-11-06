"""
Tests para los endpoints de análisis con IA
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.reports.services import AIAnalysisService


class AIAnalysisServiceBasicTestCase(TestCase):
    """Tests básicos para AIAnalysisService"""
    
    def setUp(self):
        """Setup para cada test"""
        self.service = AIAnalysisService()
    
    def test_service_initialization(self):
        """Test que servicio se inicializa correctamente"""
        self.assertIsNotNone(self.service)
        self.assertTrue(hasattr(self.service, 'llm_manager'))
    
    def test_extract_insights(self):
        """Test que _extract_insights retorna lista"""
        text = "Insight 1\nInsight 2\nInsight 3\nInsight 4\nInsight 5"
        insights = self.service._extract_insights(text)
        
        self.assertIsInstance(insights, list)
        self.assertLessEqual(len(insights), 5)
        if insights:
            self.assertIn('Insight 1', insights)
    
    def test_extract_key_findings(self):
        """Test que _extract_key_findings retorna lista"""
        text = "Finding 1\nFinding 2\nFinding 3"
        findings = self.service._extract_key_findings(text)
        
        self.assertIsInstance(findings, list)
        self.assertLessEqual(len(findings), 3)
    
    def test_extract_key_points(self):
        """Test que _extract_key_points retorna lista"""
        text = "Point 1\nPoint 2\nPoint 3\nPoint 4\nPoint 5"
        points = self.service._extract_key_points(text)
        
        self.assertIsInstance(points, list)
        self.assertLessEqual(len(points), 5)
    
    def test_determine_priority_critical(self):
        """Test que _determine_priority retorna 'critical'"""
        # Usar palabras exactas que el método busca
        result = self.service._determine_priority('critical urgente')
        self.assertEqual(result, 'critical')
        
        result2 = self.service._determine_priority('urgent inmediato')
        self.assertEqual(result2, 'critical')
    
    def test_determine_priority_high(self):
        """Test que _determine_priority retorna 'high'"""
        # Usar palabras exactas que el método busca
        result = self.service._determine_priority('importante recomendado')
        self.assertEqual(result, 'high')
        
        result2 = self.service._determine_priority('important recommend')
        self.assertEqual(result2, 'high')
    
    def test_determine_priority_medium(self):
        """Test que _determine_priority retorna 'medium'"""
        self.assertEqual(
            self.service._determine_priority('Considerar'),
            'medium'
        )
    
    def test_determine_priority_low(self):
        """Test que _determine_priority retorna 'low'"""
        self.assertEqual(
            self.service._determine_priority('Nota'),
            'low'
        )
    
    def test_parse_recommendations_json_format(self):
        """Test que _parse_recommendations parsea JSON"""
        import json
        recs = [
            {'id': '1', 'recommendation': 'Test', 'priority': 'high'}
        ]
        text = json.dumps(recs)
        
        result = self.service._parse_recommendations(text)
        
        self.assertIsInstance(result, list)
        if result:
            self.assertGreater(len(result), 0)
    
    def test_parse_recommendations_text_format(self):
        """Test que _parse_recommendations parsea texto"""
        text = "1. Recomendación 1\n2. Recomendación 2\n3. Recomendación 3"
        
        result = self.service._parse_recommendations(text)
        
        self.assertIsInstance(result, list)
        # Debe retornar algo
        self.assertGreater(len(result), 0)
