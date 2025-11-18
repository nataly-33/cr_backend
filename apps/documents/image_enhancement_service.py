"""
Servicio de mejora de imágenes médicas con CLAHE
CLAHE = Contrast Limited Adaptive Histogram Equalization
Incluye soporte para DICOM, color, y presets por modalidad
"""
import cv2
import numpy as np
import os
from PIL import Image
from django.conf import settings
from typing import Tuple, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Intentar importar pydicom (opcional)
try:
    import pydicom
    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    logger.warning("pydicom no disponible - soporte DICOM limitado")


class ImageEnhancementService:
    """
    Servicio para mejorar la calidad de imágenes médicas usando CLAHE
    Mejora el contraste y reduce el ruido en imágenes de documentos médicos
    Soporta: JPEG, PNG, TIFF, BMP, DICOM
    """

    # Presets por modalidad médica (buenas prácticas)
    MODALITY_PRESETS = {
        'xray': {  # Rayos X
            'clip_limit': 2.0,
            'tile_grid_size': (8, 8),
            'denoise': True,
            'sharpen': True,
            'description': 'Radiografías - Mayor contraste óseo'
        },
        'ct_scan': {  # Tomografía
            'clip_limit': 1.5,
            'tile_grid_size': (16, 16),
            'denoise': True,
            'sharpen': False,
            'description': 'Tomografías - Preservar detalles finos'
        },
        'mri': {  # Resonancia Magnética
            'clip_limit': 2.5,
            'tile_grid_size': (8, 8),
            'denoise': True,
            'sharpen': True,
            'description': 'Resonancias - Mejor contraste tejidos blandos'
        },
        'ultrasound': {  # Ecografía
            'clip_limit': 3.0,
            'tile_grid_size': (4, 4),
            'denoise': True,
            'sharpen': False,
            'description': 'Ecografías - Reducir ruido speckle'
        },
        'mammography': {  # Mamografía
            'clip_limit': 1.8,
            'tile_grid_size': (8, 8),
            'denoise': True,
            'sharpen': True,
            'description': 'Mamografías - Detectar microcalcificaciones'
        },
        'pet_scan': {  # PET Scan
            'clip_limit': 2.0,
            'tile_grid_size': (8, 8),
            'denoise': True,
            'sharpen': False,
            'description': 'PET - Preservar intensidades'
        },
        'default': {  # Genérico
            'clip_limit': 2.0,
            'tile_grid_size': (8, 8),
            'denoise': True,
            'sharpen': True,
            'description': 'Configuración estándar'
        }
    }

    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.dcm', '.dicom']

    def load_dicom_image(self, dicom_path: str) -> np.ndarray:
        """
        Cargar imagen DICOM y convertir a array numpy

        Args:
            dicom_path: Ruta al archivo DICOM

        Returns:
            np.ndarray: Imagen como array numpy normalizado a 0-255
        """
        if not DICOM_AVAILABLE:
            raise ImportError("pydicom no está instalado. Instala con: pip install pydicom")

        try:
            # Leer archivo DICOM
            dcm = pydicom.dcmread(dicom_path)

            # Obtener array de píxeles
            img_array = dcm.pixel_array.astype(float)

            # Normalizar a 0-255
            img_array = ((img_array - img_array.min()) / (img_array.max() - img_array.min()) * 255.0).astype(np.uint8)

            logger.info(f"DICOM cargado: {dicom_path}, shape: {img_array.shape}")
            return img_array

        except Exception as e:
            logger.error(f"Error cargando DICOM: {str(e)}")
            raise

    def get_preset_params(self, modality: str) -> Dict:
        """
        Obtener parámetros preset según modalidad médica

        Args:
            modality: Tipo de estudio (xray, ct_scan, mri, ultrasound, mammography, pet_scan)

        Returns:
            Dict: Parámetros recomendados
        """
        return self.MODALITY_PRESETS.get(modality.lower(), self.MODALITY_PRESETS['default'])

    def enhance_medical_image(
        self,
        image_path: str,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8),
        denoise: bool = True,
        sharpen: bool = True,
        preserve_color: bool = True  # NUEVO: mantener color si existe
    ) -> str:
        """
        Mejorar imagen médica con CLAHE + Denoise + Sharpen
        Soporta DICOM, JPEG, PNG, TIFF, BMP

        Args:
            image_path: Ruta de la imagen original
            clip_limit: Límite de contraste (2.0 recomendado para médicas)
            tile_grid_size: Tamaño de la rejilla (8x8 recomendado)
            denoise: Aplicar reducción de ruido
            sharpen: Aplicar sharpening
            preserve_color: Mantener información de color (si aplica)

        Returns:
            str: Ruta de la imagen mejorada
        """
        try:
            # Validar formato
            _, ext = os.path.splitext(image_path)
            if ext.lower() not in self.supported_formats:
                raise ValueError(f"Formato no soportado: {ext}")

            # Leer imagen según formato
            if ext.lower() in ['.dcm', '.dicom']:
                # DICOM
                img = self.load_dicom_image(image_path)
                if len(img.shape) == 2:
                    gray = img
                else:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            else:
                # Formatos estándar
                img = cv2.imread(image_path)
                if img is None:
                    raise ValueError(f"No se pudo leer la imagen: {image_path}")

                # Si tiene color y queremos preservarlo, usar método de color
                if preserve_color and len(img.shape) == 3:
                    return self.enhance_color_image(
                        image_path,
                        clip_limit=clip_limit,
                        tile_grid_size=tile_grid_size
                    )

                # Convertir a escala de grises
                if len(img.shape) == 3:
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    gray = img

            # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            enhanced = clahe.apply(gray)

            # 2. Denoise (reducir ruido)
            if denoise:
                enhanced = cv2.fastNlMeansDenoising(enhanced, h=10)

            # 3. Sharpen (aumentar nitidez)
            if sharpen:
                kernel = np.array([[-1, -1, -1],
                                 [-1,  9, -1],
                                 [-1, -1, -1]])
                enhanced = cv2.filter2D(enhanced, -1, kernel)

            # Guardar imagen mejorada (siempre como JPEG para compatibilidad)
            base_name, _ = os.path.splitext(image_path)
            enhanced_path = f"{base_name}_enhanced.jpg"

            # Guardar con alta calidad
            cv2.imwrite(enhanced_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])

            logger.info(f"Imagen mejorada exitosamente: {enhanced_path}")
            return enhanced_path

        except Exception as e:
            logger.error(f"Error mejorando imagen: {str(e)}")
            raise

    def enhance_color_image(
        self,
        image_path: str,
        clip_limit: float = 2.0,
        tile_grid_size: Tuple[int, int] = (8, 8)
    ) -> str:
        """
        Mejorar imagen a color preservando información cromática
        Aplica CLAHE solo al canal de luminancia (LAB color space)
        MANTIENE EL COLOR ORIGINAL - Esencial para ecografías, PET scans, etc.

        Args:
            image_path: Ruta de la imagen original
            clip_limit: Límite de contraste
            tile_grid_size: Tamaño de la rejilla

        Returns:
            str: Ruta de la imagen mejorada
        """
        try:
            # Leer imagen
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"No se pudo leer la imagen: {image_path}")

            # Convertir a LAB (Lightness, A, B)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)

            # Aplicar CLAHE solo al canal L (luminancia)
            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
            l_enhanced = clahe.apply(l)

            # Merge canales
            lab_enhanced = cv2.merge([l_enhanced, a, b])

            # Convertir de vuelta a BGR
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)

            # Guardar siempre como JPEG para consistencia
            base_name, _ = os.path.splitext(image_path)
            enhanced_path = f"{base_name}_enhanced.jpg"

            cv2.imwrite(enhanced_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 95])

            logger.info(f"Imagen a color mejorada: {enhanced_path}")
            return enhanced_path

        except Exception as e:
            logger.error(f"Error mejorando imagen a color: {str(e)}")
            raise

    def enhance_with_preset(
        self,
        image_path: str,
        modality: str,
        preserve_color: bool = True
    ) -> str:
        """
        Mejorar imagen usando preset específico para modalidad médica

        Args:
            image_path: Ruta de la imagen original
            modality: Tipo de estudio (xray, ct_scan, mri, ultrasound, mammography, pet_scan)
            preserve_color: Mantener color si existe

        Returns:
            str: Ruta de la imagen mejorada
        """
        # Obtener parámetros del preset
        params = self.get_preset_params(modality)

        logger.info(f"Aplicando preset '{modality}': {params['description']}")

        # Mejorar con parámetros del preset
        return self.enhance_medical_image(
            image_path=image_path,
            clip_limit=params['clip_limit'],
            tile_grid_size=params['tile_grid_size'],
            denoise=params['denoise'],
            sharpen=params['sharpen'],
            preserve_color=preserve_color
        )

    def auto_enhance(self, image_path: str, modality: Optional[str] = None) -> str:
        """
        Mejora automática - decide si usar escala de grises o color
        Si se especifica modalidad, usa preset recomendado

        Args:
            image_path: Ruta de la imagen
            modality: Tipo de estudio médico (opcional)

        Returns:
            str: Ruta de la imagen mejorada
        """
        # Si hay modalidad especificada, usar preset
        if modality:
            return self.enhance_with_preset(image_path, modality, preserve_color=True)

        # Leer imagen
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"No se pudo leer la imagen: {image_path}")

        # Detectar si es grayscale o color
        if len(img.shape) == 2 or (len(img.shape) == 3 and img.shape[2] == 1):
            # Grayscale
            return self.enhance_medical_image(image_path, preserve_color=False)
        else:
            # Color - verificar si realmente tiene color o es "fake" color
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            diff = cv2.absdiff(img[:, :, 0], gray_img)

            if np.mean(diff) < 10:  # Threshold para detectar "fake" color
                # Es prácticamente grayscale, usar enhance_medical_image
                return self.enhance_medical_image(image_path, preserve_color=False)
            else:
                # Tiene color real, preservarlo
                return self.enhance_color_image(image_path)

    def compare_images(
        self,
        original_path: str,
        enhanced_path: str
    ) -> dict:
        """
        Comparar imagen original vs mejorada (métricas)

        Args:
            original_path: Ruta de la imagen original
            enhanced_path: Ruta de la imagen mejorada

        Returns:
            dict: Métricas de comparación
        """
        try:
            # Leer imágenes
            original = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
            enhanced = cv2.imread(enhanced_path, cv2.IMREAD_GRAYSCALE)

            # Calcular métricas
            metrics = {
                'original_mean': float(np.mean(original)),
                'enhanced_mean': float(np.mean(enhanced)),
                'original_std': float(np.std(original)),
                'enhanced_std': float(np.std(enhanced)),
                'contrast_improvement': float(np.std(enhanced) / np.std(original)),
                'dynamic_range_original': int(np.ptp(original)),
                'dynamic_range_enhanced': int(np.ptp(enhanced)),
            }

            # PSNR (Peak Signal-to-Noise Ratio)
            mse = np.mean((original.astype(float) - enhanced.astype(float)) ** 2)
            if mse == 0:
                metrics['psnr'] = float('inf')
            else:
                max_pixel = 255.0
                metrics['psnr'] = float(20 * np.log10(max_pixel / np.sqrt(mse)))

            return metrics

        except Exception as e:
            logger.error(f"Error comparando imágenes: {str(e)}")
            return {}

    def batch_enhance(
        self,
        image_paths: list,
        use_auto: bool = True
    ) -> list:
        """
        Mejorar múltiples imágenes en lote

        Args:
            image_paths: Lista de rutas de imágenes
            use_auto: Usar auto_enhance (True) o enhance_medical_image (False)

        Returns:
            list: Lista de rutas de imágenes mejoradas
        """
        enhanced_paths = []

        for image_path in image_paths:
            try:
                if use_auto:
                    enhanced_path = self.auto_enhance(image_path)
                else:
                    enhanced_path = self.enhance_medical_image(image_path)

                enhanced_paths.append(enhanced_path)

            except Exception as e:
                logger.error(f"Error procesando {image_path}: {str(e)}")
                enhanced_paths.append(None)

        return enhanced_paths
