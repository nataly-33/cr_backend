"""
Vista simple para visualizar DICOM sin guardar en BD.
Solo para desarrollo/testing.
Usa cache en memoria con UUID para evitar problemas de sesiones con CORS/JWT.
"""
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import pydicom
from io import BytesIO
import uuid
import time

# Tiempo de expiración del cache en segundos (10 minutos)
CACHE_TIMEOUT = 600


@csrf_exempt
@require_http_methods(["POST"])
def upload_and_view_dicom(request):
    """
    Endpoint simple que recibe un archivo DICOM y devuelve su URL para visualización.
    No guarda nada en la base de datos. Usa cache temporal con UUID.
    """
    try:
        # Obtener el archivo
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'error': 'No se proporcionó archivo'}, status=400)

        # Leer el contenido
        file_content = uploaded_file.read()

        # Validar que es un DICOM válido y extraer metadata
        try:
            dcm = pydicom.dcmread(BytesIO(file_content))

            # Manejar valores que pueden ser listas (MultiValue)
            window_center = getattr(dcm, 'WindowCenter', 40)
            if hasattr(window_center, '__iter__') and not isinstance(window_center, str):
                window_center = float(list(window_center)[0])
            else:
                window_center = float(window_center) if window_center else 40

            window_width = getattr(dcm, 'WindowWidth', 400)
            if hasattr(window_width, '__iter__') and not isinstance(window_width, str):
                window_width = float(list(window_width)[0])
            else:
                window_width = float(window_width) if window_width else 400

            metadata = {
                'patient_name': str(getattr(dcm, 'PatientName', 'Desconocido')),
                'patient_id': str(getattr(dcm, 'PatientID', '')),
                'modality': str(getattr(dcm, 'Modality', 'OT')),
                'study_description': str(getattr(dcm, 'StudyDescription', '')),
                'series_description': str(getattr(dcm, 'SeriesDescription', '')),
                'rows': int(getattr(dcm, 'Rows', 0)),
                'columns': int(getattr(dcm, 'Columns', 0)),
                'window_center': window_center,
                'window_width': window_width,
            }
        except Exception as e:
            return JsonResponse({'error': f'Archivo DICOM inválido: {str(e)}'}, status=400)

        # Generar un UUID único para este archivo
        file_uuid = str(uuid.uuid4())

        # Guardar en cache (memoria)
        cache_key = f'temp_dicom_{file_uuid}'
        cache.set(cache_key, {
            'content': file_content,
            'filename': uploaded_file.name,
            'timestamp': time.time()
        }, CACHE_TIMEOUT)

        # Construir URL para el stream con el UUID
        stream_url = f'/api/dicom/temp/stream/{file_uuid}/'

        # Devolver JSON con la URL y metadata
        return JsonResponse({
            'stream_url': stream_url,
            'metadata': metadata,
            'filename': uploaded_file.name,
            'size': len(file_content),
            'file_id': file_uuid,
        })

    except Exception as e:
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def stream_temp_dicom(request, file_uuid):
    """
    Sirve el DICOM temporal desde cache usando UUID.
    """
    # Manejar preflight OPTIONS
    if request.method == 'OPTIONS':
        response = HttpResponse()
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response

    try:
        # Buscar en cache
        cache_key = f'temp_dicom_{file_uuid}'
        cached_data = cache.get(cache_key)

        if not cached_data:
            return HttpResponse('Archivo DICOM no encontrado o expirado', status=404)

        dicom_bytes = cached_data['content']

        response = HttpResponse(dicom_bytes, content_type='application/dicom')
        response['Content-Disposition'] = f'inline; filename="{cached_data.get("filename", "temp.dcm")}"'
        response['Content-Length'] = len(dicom_bytes)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'

        return response

    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)
