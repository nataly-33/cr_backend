import boto3
import logging
from django.conf import settings
from .storage import S3Storage

logger = logging.getLogger(__name__)


class OCRService:
    """Servicio de OCR usando AWS Textract (opcional)"""

    def __init__(self):
        # Solo inicializar Textract si AWS está configurado
        self.use_textract = hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID
        
        if self.use_textract:
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_TEXTRACT_REGION', settings.AWS_S3_REGION_NAME)
            )
        else:
            self.textract_client = None

    def extract_text_from_s3(self, bucket, file_path):
        """
        Extrae texto de un documento en S3 usando AWS Textract
        
        Args:
            bucket: Nombre del bucket S3
            file_path: Ruta del archivo en S3
            
        Returns:
            dict con 'text', 'confidence' y 'job_id'
        """
        if not self.use_textract:
            logger.info("OCR not available (AWS not configured)")
            return {
                'text': '',
                'confidence': 0,
                'job_id': '',
                'success': False,
                'error': 'AWS Textract not configured'
            }
            
        try:
            # Para documentos simples (imágenes, PDFs de 1 página)
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': file_path
                    }
                }
            )

            # Extraer texto de los bloques
            text_blocks = []
            confidence_scores = []

            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block.get('Text', ''))
                    confidence_scores.append(block.get('Confidence', 0))

            full_text = '\n'.join(text_blocks)
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            logger.info(f"OCR completed for {file_path}. Confidence: {avg_confidence:.2f}%")

            return {
                'text': full_text,
                'confidence': round(avg_confidence, 2),
                'job_id': response.get('JobId', ''),
                'success': True
            }

        except Exception as e:
            logger.error(f"Error in OCR processing: {str(e)}")
            return {
                'text': '',
                'confidence': 0,
                'job_id': '',
                'success': False,
                'error': str(e)
            }

    def extract_text_async(self, bucket, file_path):
        """
        Inicia procesamiento asíncrono para documentos grandes (PDFs multipágina)
        
        Args:
            bucket: Nombre del bucket S3
            file_path: Ruta del archivo en S3
            
        Returns:
            Job ID de AWS Textract
        """
        try:
            response = self.textract_client.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': file_path
                    }
                }
            )

            job_id = response['JobId']
            logger.info(f"Async OCR job started: {job_id}")

            return job_id

        except Exception as e:
            logger.error(f"Error starting async OCR: {str(e)}")
            return None

    def get_async_result(self, job_id):
        """
        Obtiene el resultado de un job asíncrono de Textract
        
        Args:
            job_id: ID del job de Textract
            
        Returns:
            dict con el resultado o None si aún no está listo
        """
        try:
            response = self.textract_client.get_document_text_detection(JobId=job_id)

            status = response['JobStatus']

            if status == 'SUCCEEDED':
                # Extraer texto
                text_blocks = []
                confidence_scores = []

                for block in response.get('Blocks', []):
                    if block['BlockType'] == 'LINE':
                        text_blocks.append(block.get('Text', ''))
                        confidence_scores.append(block.get('Confidence', 0))

                full_text = '\n'.join(text_blocks)
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

                return {
                    'text': full_text,
                    'confidence': round(avg_confidence, 2),
                    'status': 'SUCCEEDED',
                    'success': True
                }

            elif status == 'FAILED':
                return {
                    'text': '',
                    'confidence': 0,
                    'status': 'FAILED',
                    'success': False,
                    'error': response.get('StatusMessage', 'Unknown error')
                }

            else:
                return {
                    'status': status,  # IN_PROGRESS
                    'success': False
                }

        except Exception as e:
            logger.error(f"Error getting async OCR result: {str(e)}")
            return {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }


class DocumentService:
    """Servicio para gestión de documentos"""

    def __init__(self):
        self.storage = S3Storage()
        self.ocr_service = OCRService()

    def upload_document(self, document_instance, file_obj):
        """
        Sube un documento a S3 y opcionalmente procesa OCR
        
        Args:
            document_instance: Instancia de ClinicalDocument
            file_obj: Archivo de Django
            
        Returns:
            bool indicando éxito
        """
        try:
            # Generar path único en S3
            file_extension = file_obj.name.split('.')[-1]
            file_path = f"documents/{document_instance.tenant_id}/{document_instance.id}.{file_extension}"

            # Subir a S3
            url = self.storage.upload_file(file_obj, file_path)

            if not url:
                return False

            # Actualizar documento
            document_instance.file_path = file_path
            document_instance.file_name = file_obj.name
            document_instance.file_size_bytes = file_obj.size
            document_instance.mime_type = file_obj.content_type

            # Calcular hash del archivo
            file_obj.seek(0)
            file_content = file_obj.read()
            document_instance.file_hash = document_instance.calculate_file_hash(file_content)

            document_instance.save()

            # Procesar OCR si es PDF o imagen
            if file_obj.content_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
                self.process_ocr_async(document_instance)

            return True

        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            return False

    def process_ocr_async(self, document_instance):
        """
        Procesa OCR de forma asíncrona
        Por ahora lo hace síncrono, más adelante usar Celery
        """
        # Solo procesar OCR si AWS está configurado
        if not self.ocr_service.use_textract:
            logger.info("OCR processing skipped (AWS not configured)")
            return
            
        try:
            bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            if not bucket:
                logger.info("OCR processing skipped (S3 bucket not configured)")
                return
                
            file_path = document_instance.file_path

            result = self.ocr_service.extract_text_from_s3(bucket, file_path)

            if result['success']:
                document_instance.ocr_text = result['text']
                document_instance.ocr_confidence = result['confidence']
                document_instance.ocr_processed = True
                document_instance.ocr_job_id = result['job_id']
                document_instance.save()

                logger.info(f"OCR processed successfully for document {document_instance.id}")

        except Exception as e:
            logger.error(f"Error processing OCR: {str(e)}")

    def log_access(self, document, user, access_type, request):
        """
        Registra un acceso al documento
        
        Args:
            document: Instancia de ClinicalDocument
            user: Usuario que accede
            access_type: Tipo de acceso (view, download, etc.)
            request: Request de Django
        """
        from .models import DocumentAccessLog

        # Obtener IP del request
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        DocumentAccessLog.objects.create(
            tenant=document.tenant,
            document=document,
            user=user,
            access_type=access_type,
            user_email=user.email,
            user_name=user.get_full_name(),
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )