"""
Tareas asíncronas de Celery para procesamiento de documentos
"""
from celery import shared_task
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_ocr(self, document_id):
    """
    Procesar OCR de un documento de forma asíncrona
    
    Args:
        document_id: UUID del documento a procesar
        
    Returns:
        dict con resultado del procesamiento
    """
    try:
        from .models import ClinicalDocument
        from .services import OCRService
        
        document = ClinicalDocument.objects.get(id=document_id)
        
        # Verificar que tenga archivo
        if not document.file_path:
            logger.warning(f"Document {document_id} no tiene archivo")
            return {
                'success': False,
                'error': 'No file path'
            }
        
        # Marcar como procesando
        document.ocr_status = 'processing'
        document.save(update_fields=['ocr_status'])
        
        # Ejecutar OCR
        ocr_service = OCRService()
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        
        # Determinar tipo de archivo
        file_extension = document.file_path.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            # Para PDFs, intentar procesamiento directo primero
            # Si es muy grande, usar método asíncrono
            logger.info(f"Processing PDF document {document_id}")
            result = ocr_service.extract_text_from_s3(bucket, document.file_path)
            
            if result['success']:
                document.ocr_text = result['text']
                document.ocr_confidence = result['confidence']
                document.ocr_processed = True
                document.ocr_job_id = result.get('job_id', '')
                document.ocr_status = 'completed'
                document.save()
                
                logger.info(f"OCR completado para documento {document_id}")
                return {
                    'success': True,
                    'text_length': len(result['text']),
                    'confidence': result['confidence']
                }
            else:
                # Si falla, marcar como fallido
                document.ocr_status = 'failed'
                document.save(update_fields=['ocr_status'])
                
                logger.error(f"OCR falló para documento {document_id}: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        else:
            # Imagen: procesamiento directo
            logger.info(f"Processing image document {document_id}")
            result = ocr_service.extract_text_from_s3(bucket, document.file_path)
            
            if result['success']:
                document.ocr_text = result['text']
                document.ocr_confidence = result['confidence']
                document.ocr_processed = True
                document.ocr_status = 'completed'
                document.save()
                
                logger.info(f"OCR completado para documento {document_id}")
                return {
                    'success': True,
                    'text_length': len(result['text']),
                    'confidence': result['confidence']
                }
            else:
                document.ocr_status = 'failed'
                document.save(update_fields=['ocr_status'])
                
                logger.error(f"OCR falló para documento {document_id}: {result.get('error')}")
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
        
    except Exception as e:
        logger.error(f"Error en tarea OCR para documento {document_id}: {str(e)}")
        
        # Intentar marcar como fallido
        try:
            from .models import ClinicalDocument
            document = ClinicalDocument.objects.get(id=document_id)
            document.ocr_status = 'failed'
            document.save(update_fields=['ocr_status'])
        except:
            pass
        
        # Reintentar la tarea
        raise self.retry(exc=e, countdown=60)  # Reintentar en 60 segundos


@shared_task
def check_async_ocr_jobs():
    """
    Tarea periódica para verificar el estado de jobs asíncronos de OCR
    (Para PDFs grandes que usan StartDocumentTextDetection)
    """
    from .models import ClinicalDocument
    from .services import OCRService
    
    # Buscar documentos con OCR en progreso asíncrono
    pending_docs = ClinicalDocument.objects.filter(
        ocr_status='async_processing',
        ocr_job_id__isnull=False
    )
    
    if not pending_docs.exists():
        logger.info("No hay jobs de OCR pendientes")
        return
    
    ocr_service = OCRService()
    
    for document in pending_docs:
        try:
            result = ocr_service.get_async_result(document.ocr_job_id)
            
            if result['status'] == 'SUCCEEDED':
                document.ocr_text = result['text']
                document.ocr_confidence = result['confidence']
                document.ocr_processed = True
                document.ocr_status = 'completed'
                document.save()
                
                logger.info(f"OCR asíncrono completado para documento {document.id}")
                
            elif result['status'] == 'FAILED':
                document.ocr_status = 'failed'
                document.save()
                
                logger.error(f"OCR asíncrono falló para documento {document.id}")
                
        except Exception as e:
            logger.error(f"Error verificando OCR job {document.ocr_job_id}: {str(e)}")


@shared_task(bind=True, max_retries=3)
def enhance_medical_image(self, image_id):
    """
    Mejorar calidad de una imagen médica usando CLAHE
    (Será implementado en Tarea 3 del ROADMAP)
    
    Args:
        image_id: UUID de la imagen a mejorar
    """
    try:
        from .models import MedicalImage
        
        image = MedicalImage.objects.get(id=image_id)
        
        # Marcar como procesando
        image.enhancement_status = 'processing'
        image.save(update_fields=['enhancement_status'])
        
        # TODO: Implementar mejora con CLAHE
        # Por ahora solo marcamos como pendiente
        logger.info(f"Image enhancement pendiente para imagen {image_id}")
        
        # Marcar como pendiente (será implementado después)
        image.enhancement_status = 'pending'
        image.save(update_fields=['enhancement_status'])
        
        return {
            'success': True,
            'message': 'Enhancement será implementado en Tarea 3'
        }
        
    except Exception as e:
        logger.error(f"Error en tarea de mejora de imagen {image_id}: {str(e)}")
        
        try:
            from .models import MedicalImage
            image = MedicalImage.objects.get(id=image_id)
            image.enhancement_status = 'failed'
            image.save(update_fields=['enhancement_status'])
        except:
            pass
        
        raise self.retry(exc=e, countdown=60)
