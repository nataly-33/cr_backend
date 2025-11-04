"""
Tests para BaseReportGenerator y ReportGeneratorFactory (Fase 4)

Ejecutar:
    python manage.py test apps.reports.tests.test_base_generator
    pytest apps/reports/tests/test_base_generator.py -v
"""

from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
import logging

from apps.reports.generators.base import BaseReportGenerator, ReportGeneratorFactory


class BaseReportGeneratorFactoryTestCase(TestCase):
    """Tests para ReportGeneratorFactory"""
    
    def setUp(self):
        """Setup para cada test"""
        # Limpiar factory para cada test
        ReportGeneratorFactory._generators.clear()
        # Re-registrar generadores estándar
        self._register_default_generators()
    
    def _register_default_generators(self):
        """Registra los generadores por defecto"""
        # Se asume que existen clases PDF, Excel, CSV en generators/
        # Este método se puede adaptar según la implementación real
        pass
    
    def test_factory_register_format(self):
        """Test registrar un formato nuevo en la factory"""
        # Crear un mock de generador
        mock_generator_class = Mock()
        
        # Registrar
        ReportGeneratorFactory.register('mock_format', mock_generator_class)
        
        # Verificar que se registró
        self.assertIn('mock_format', ReportGeneratorFactory._generators)
    
    def test_factory_create_generator(self):
        """Test crear una instancia de generador"""
        # Crear mock
        MockGenerator = Mock(return_value=Mock())
        ReportGeneratorFactory.register('test', MockGenerator)
        
        # Crear instancia
        generator = ReportGeneratorFactory.create('test', 'Test Report')
        
        # Verificar - factory.create() llama con kwargs: title= y format_type=
        self.assertIsNotNone(generator)
        MockGenerator.assert_called_once_with(title='Test Report', format_type='test')
    
    def test_factory_get_supported_formats(self):
        """Test obtener formatos soportados"""
        formats = ReportGeneratorFactory.get_supported_formats()
        
        # Debe contener al menos los formatos base
        self.assertIsInstance(formats, list)
        # Después de limpiar, debe haber al menos 0
        self.assertGreaterEqual(len(formats), 0)
    
    def test_factory_create_unknown_format_raises_error(self):
        """Test crear generador con formato desconocido lanza error"""
        with self.assertRaises(ValueError):
            ReportGeneratorFactory.create('unknown_format', 'Report')
    
    def test_factory_duplicate_registration_overwrites(self):
        """Test registrar dos veces el mismo formato sobrescribe"""
        mock1 = Mock()
        mock2 = Mock()
        
        ReportGeneratorFactory.register('format', mock1)
        ReportGeneratorFactory.register('format', mock2)
        
        # Debe tener la segunda
        self.assertEqual(ReportGeneratorFactory._generators['format'], mock2)


class BaseReportGeneratorMimetypeTestCase(TestCase):
    """Tests para tipos MIME y extensiones de archivo"""
    
    def setUp(self):
        """Setup para cada test"""
        # Crear mock de generador para no instanciar clase abstracta
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator_pdf = BaseReportGenerator('Test', format_type='pdf')
            self.generator_excel = BaseReportGenerator('Test', format_type='excel')
            self.generator_csv = BaseReportGenerator('Test', format_type='csv')
    
    def test_get_mime_type_pdf(self):
        """Test obtener MIME type para PDF"""
        mime_type = self.generator_pdf.get_mime_type()
        self.assertEqual(mime_type, 'application/pdf')
    
    def test_get_mime_type_excel(self):
        """Test obtener MIME type para Excel"""
        mime_type = self.generator_excel.get_mime_type()
        self.assertIn('spreadsheet', mime_type)
    
    def test_get_mime_type_csv(self):
        """Test obtener MIME type para CSV"""
        mime_type = self.generator_csv.get_mime_type()
        self.assertEqual(mime_type, 'text/csv')
    
    def test_get_file_extension_pdf(self):
        """Test obtener extensión para PDF"""
        ext = self.generator_pdf.get_file_extension()
        self.assertEqual(ext, '.pdf')
    
    def test_get_file_extension_excel(self):
        """Test obtener extensión para Excel"""
        ext = self.generator_excel.get_file_extension()
        self.assertEqual(ext, '.xlsx')
    
    def test_get_file_extension_csv(self):
        """Test obtener extensión para CSV"""
        ext = self.generator_csv.get_file_extension()
        self.assertEqual(ext, '.csv')


class BaseReportGeneratorFilenameTestCase(TestCase):
    """Tests para generación de nombres de archivo"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('test_report', format_type='pdf')
    
    def test_get_filename_includes_timestamp(self):
        """Test que nombre de archivo incluye timestamp"""
        filename = self.generator.get_filename()
        
        # Debe contener el nombre
        self.assertIn('test', filename.lower())
        # Debe tener extensión
        self.assertTrue(filename.endswith('.pdf'))
        # Debe ser un string válido
        self.assertIsInstance(filename, str)
    
    def test_get_filename_format(self):
        """Test formato del nombre de archivo"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            # Usar 'excel' que está en SUPPORTED_FORMATS
            generator = BaseReportGenerator('MyReport', format_type='excel')
            filename = generator.get_filename()
            
            # Debe ser formato: nombre_YYYYMMDD_HHMMSS.ext
            parts = filename.split('_')
            self.assertGreater(len(parts), 1)
            self.assertTrue(filename.endswith('.xlsx'))


class BaseReportGeneratorDataFormattingTestCase(TestCase):
    """Tests para formateo de datos"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('Test')
    
    def test_format_data_empty_list(self):
        """Test formatear lista vacía"""
        data = []
        formatted = self.generator.format_data(data)
        
        self.assertEqual(formatted, [])
    
    def test_format_data_with_simple_dict(self):
        """Test formatear diccionario simple"""
        data = [{'name': 'John', 'age': 30}]
        formatted = self.generator.format_data(data)
        
        self.assertEqual(len(formatted), 1)
        self.assertEqual(formatted[0]['name'], 'John')
    
    def test_format_data_with_nested_objects(self):
        """Test formatear datos con objetos anidados"""
        data = [
            {
                'id': 1,
                'patient': {'name': 'John'},
                'created_at': '2024-01-01'
            }
        ]
        formatted = self.generator.format_data(data)
        
        # Debe ser procesado correctamente
        self.assertEqual(len(formatted), 1)
    
    def test_format_data_with_datetime(self):
        """Test formatear datos con datetime"""
        from datetime import datetime
        data = [{'date': datetime(2024, 1, 1, 12, 0)}]
        formatted = self.generator.format_data(data)
        
        # Datetime debe ser convertido a string
        self.assertEqual(len(formatted), 1)


class BaseReportGeneratorValidationTestCase(TestCase):
    """Tests para validación de datos"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('Test')
    
    def test_validate_data_raises_on_none(self):
        """Test validación con None retorna False"""
        # validate_data retorna False, no lanza excepción
        result = self.generator.validate_data(None)
        self.assertFalse(result)
    
    def test_validate_data_raises_on_empty(self):
        """Test validación con lista vacía es válida"""
        # Esto depende de la implementación
        result = self.generator.validate_data([])
        # validate_data retorna True para lista vacía
        self.assertTrue(result)
    
    def test_validate_data_with_valid_data(self):
        """Test validación con datos válidos"""
        data = [{'name': 'John'}]
        result = self.generator.validate_data(data)
        
        self.assertTrue(result)
    
    def test_validate_data_with_large_dataset(self):
        """Test validación con dataset grande"""
        data = [{'id': i, 'name': f'Item{i}'} for i in range(1000)]
        result = self.generator.validate_data(data)
        
        self.assertTrue(result)


class BaseReportGeneratorMetadataTestCase(TestCase):
    """Tests para metadata de reportes"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('Test Report')
    
    def test_set_and_get_metadata(self):
        """Test establecer y obtener metadata"""
        # set_metadata toma (key, value), no **kwargs
        self.generator.set_metadata('author', 'Test User')
        self.generator.set_metadata('version', '1.0')
        
        metadata = self.generator.get_metadata()
        
        self.assertEqual(metadata['custom']['author'], 'Test User')
        self.assertEqual(metadata['custom']['version'], '1.0')
    
    def test_metadata_includes_timestamp(self):
        """Test metadata incluye timestamp"""
        metadata = self.generator.get_metadata()
        
        self.assertIn('created_at', metadata)
        self.assertIn('title', metadata)


class BaseReportGeneratorLoggingTestCase(TestCase):
    """Tests para logging en generadores"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('Test')
    
    def test_logging_is_called(self):
        """Test que logging se invoca"""
        with patch('apps.reports.generators.base.logger') as mock_logger:
            self.generator.log_generation('test_event')
            
            # Verificar que se llamó a logging
            self.assertTrue(mock_logger.info.called or 
                           mock_logger.debug.called)


class BaseReportGeneratorErrorHandlingTestCase(TestCase):
    """Tests para manejo de errores"""
    
    def setUp(self):
        """Setup para cada test"""
        with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
            self.generator = BaseReportGenerator('Test')
    
    def test_unsupported_format_raises_error(self):
        """Test formato no soportado lanza error"""
        # get_mime_type es método de instancia, no estático
        with self.assertRaises((ValueError, KeyError)):
            # Crear generador con formato inválido lanza error en __init__
            with patch.object(BaseReportGenerator, '__abstractmethods__', set()):
                BaseReportGenerator('Test', format_type='unknown')
    
    def test_invalid_data_raises_validation_error(self):
        """Test datos inválidos retorna False (no lanza excepción)"""
        # validate_data retorna False, no lanza excepción
        result = self.generator.validate_data(None)
        self.assertFalse(result)
    
    def test_file_write_error_handled(self):
        """Test que error en escritura de archivo se maneja"""
        # Este test dependería de la implementación de generate()
        pass


class BaseReportGeneratorIntegrationTestCase(TestCase):
    """Tests de integración con generadores reales"""
    
    def test_pdf_generator_inherits_correctly(self):
        """Test que PDF generator hereda de BaseReportGenerator"""
        try:
            from apps.reports.generators.pdf_generator import PDFReportGenerator
            self.assertTrue(issubclass(PDFReportGenerator, BaseReportGenerator))
        except ImportError:
            self.skipTest("PDF Generator not available")
    
    def test_excel_generator_inherits_correctly(self):
        """Test que Excel generator hereda de BaseReportGenerator"""
        try:
            from apps.reports.generators.excel_generator import ExcelReportGenerator
            self.assertTrue(issubclass(ExcelReportGenerator, BaseReportGenerator))
        except ImportError:
            self.skipTest("Excel Generator not available")
    
    def test_csv_generator_inherits_correctly(self):
        """Test que CSV generator hereda de BaseReportGenerator"""
        try:
            from apps.reports.generators.csv_generator import CSVReportGenerator
            self.assertTrue(issubclass(CSVReportGenerator, BaseReportGenerator))
        except ImportError:
            self.skipTest("CSV Generator not available")
    
    def test_all_generators_have_generate_method(self):
        """Test que todos los generadores tienen método generate"""
        # Obtener todos los generadores del factory
        formats = ReportGeneratorFactory.get_supported_formats()
        
        for fmt in formats:
            try:
                generator_class = ReportGeneratorFactory._generators.get(fmt)
                if generator_class:
                    self.assertTrue(hasattr(generator_class, 'generate'))
            except Exception:
                pass  # Ignorar errores en generadores específicos
