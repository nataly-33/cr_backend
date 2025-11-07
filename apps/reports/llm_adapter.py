"""
Fase 5: IA Hook para Reportes

Módulo para integración con LLMs (OpenAI, Claude, local) para:
- Análisis automático de reportes
- Generación asistida de insights
- Resumen automático de datos
- Recomendaciones basadas en datos
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import json
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

# Imports opcionales para LLMs (con manejo de excepciones)
try:
    import openai
except ImportError:
    openai = None
    logger.debug("openai package no disponible. Instalar con: pip install openai")

try:
    import anthropic
except ImportError:
    anthropic = None
    logger.debug("anthropic package no disponible. Instalar con: pip install anthropic")


class LLMAdapter(ABC):
    """
    Adaptador base para modelos de lenguaje.
    Define la interfaz para interactuar con diferentes LLMs.
    """
    
    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """
        Inicializar adaptador LLM.
        
        Args:
            model_name: Nombre del modelo
            api_key: Clave API (si es necesaria)
        """
        self.model_name = model_name
        self.api_key = api_key
        self.last_response = None
        self.tokens_used = 0
    
    @abstractmethod
    def analyze_data(self, data: Dict[str, Any], context: str = "") -> str:
        """
        Analizar datos y generar insights.
        
        Args:
            data: Datos a analizar
            context: Contexto adicional
            
        Returns:
            str: Análisis generado por IA
        """
        pass
    
    @abstractmethod
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Generar resumen automático.
        
        Args:
            text: Texto a resumir
            max_length: Longitud máxima del resumen
            
        Returns:
            str: Resumen generado
        """
        pass
    
    @abstractmethod
    def generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """
        Generar recomendaciones basadas en análisis.
        
        Args:
            analytics: Datos de análisis
            
        Returns:
            list: Lista de recomendaciones
        """
        pass
    
    def is_available(self) -> bool:
        """
        Verificar si el adaptador está disponible.
        
        Returns:
            bool: True si está configurado correctamente
        """
        return bool(self.api_key or self.model_name)
    
    def _sanitize_input(self, text: str) -> str:
        """
        Sanitizar entrada para evitar inyecciones.
        
        Args:
            text: Texto a sanitizar
            
        Returns:
            str: Texto sanitizado
        """
        import re
        
        # Limitar longitud
        text = text[:10000]
        
        # Remover scripts y etiquetas peligrosas
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<iframe[^>]*>.*?</iframe>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'on\w+\s*=\s*["\']?.*?["\']', '', text, flags=re.IGNORECASE)
        
        return text.strip()


class OpenAIAdapter(LLMAdapter):
    """Adaptador para OpenAI GPT models"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        """
        Inicializar adaptador OpenAI.
        
        Args:
            api_key: Clave API de OpenAI
            model: Modelo a usar (gpt-3.5-turbo, gpt-4, etc)
        """
        super().__init__(model_name=model, api_key=api_key)
        self.base_url = "https://api.openai.com/v1"
        
        if openai:
            openai.api_key = api_key
            self.client = openai
        else:
            logger.warning("openai package no instalado. Instalar: pip install openai")
            self.client = None
    
    def is_available(self) -> bool:
        """
        Verificar si OpenAI adapter está disponible (requiere api_key).
        
        Returns:
            bool: True si tiene api_key válida
        """
        return bool(self.api_key and self.client is not None)
    
    def analyze_data(self, data: Dict[str, Any], context: str = "") -> str:
        """Analizar datos usando GPT"""
        if not self.client:
            return "Error: OpenAI no configurado"
        
        try:
            prompt = self._build_analysis_prompt(data, context)
            
            response = self.client.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de datos médicos. Proporciona insights claros y accionables."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            result = response['choices'][0]['message']['content']
            self.tokens_used += response['usage']['total_tokens']
            self.last_response = result
            
            logger.info(f"Análisis IA completado ({self.tokens_used} tokens)")
            return result
            
        except Exception as e:
            logger.error(f"Error en OpenAI: {str(e)}")
            return f"Error en análisis IA: {str(e)}"
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generar resumen usando GPT"""
        if not self.client:
            return text[:max_length]
        
        try:
            response = self.client.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": f"Resume el siguiente texto en máximo {max_length} caracteres. Sé conciso pero informativo."
                    },
                    {"role": "user", "content": self._sanitize_input(text)}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            result = response['choices'][0]['message']['content']
            self.tokens_used += response['usage']['total_tokens']
            return result
            
        except Exception as e:
            logger.error(f"Error en resumen: {str(e)}")
            return text[:max_length]
    
    def generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones usando GPT"""
        if not self.client:
            return []
        
        try:
            prompt = f"""
            Basado en estos datos de análisis, proporciona 3-5 recomendaciones 
            específicas y accionables para mejorar el sistema:
            
            {json.dumps(analytics, indent=2, default=str)}
            
            Formato: lista numerada, cada recomendación en una línea.
            """
            
            response = self.client.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un consultor experto en sistemas médicos. Proporciona recomendaciones prácticas."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            text = response['choices'][0]['message']['content']
            recommendations = [r.strip() for r in text.split('\n') if r.strip()]
            self.tokens_used += response['usage']['total_tokens']
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error en recomendaciones: {str(e)}")
            return []
    
    def _build_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Construir prompt para análisis"""
        return f"""
        Analiza los siguientes datos de reportes médicos y proporciona insights:
        
        {json.dumps(data, indent=2, default=str)}
        
        Contexto adicional: {context}
        
        Proporciona:
        1. Hallazgos principales
        2. Tendencias importantes
        3. Áreas de preocupación
        4. Oportunidades de mejora
        """


class ClaudeAdapter(LLMAdapter):
    """Adaptador para Anthropic Claude"""
    
    def __init__(self, api_key: str, model: str = "claude-2"):
        """
        Inicializar adaptador Claude.
        
        Args:
            api_key: Clave API de Anthropic
            model: Modelo a usar
        """
        super().__init__(model_name=model, api_key=api_key)
        
        if anthropic:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            logger.warning("anthropic package no instalado. Instalar: pip install anthropic")
            self.client = None
    
    def is_available(self) -> bool:
        """
        Verificar si Claude adapter está disponible (requiere api_key).
        
        Returns:
            bool: True si tiene api_key válida
        """
        return bool(self.api_key and self.client is not None)
    
    def analyze_data(self, data: Dict[str, Any], context: str = "") -> str:
        """Analizar datos usando Claude"""
        if not self.client:
            return "Error: Claude no configurado"
        
        try:
            prompt = self._build_analysis_prompt(data, context)
            
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = message.content[0].text
            self.tokens_used += message.usage.input_tokens + message.usage.output_tokens
            self.last_response = result
            
            logger.info(f"Análisis Claude completado ({self.tokens_used} tokens)")
            return result
            
        except Exception as e:
            logger.error(f"Error en Claude: {str(e)}")
            return f"Error en análisis IA: {str(e)}"
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generar resumen usando Claude"""
        if not self.client:
            return text[:max_length]
        
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": f"Resume en {max_length} caracteres: {self._sanitize_input(text)}"
                    }
                ]
            )
            
            result = message.content[0].text
            self.tokens_used += message.usage.input_tokens + message.usage.output_tokens
            return result
            
        except Exception as e:
            logger.error(f"Error en resumen: {str(e)}")
            return text[:max_length]
    
    def generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones usando Claude"""
        if not self.client:
            return []
        
        try:
            prompt = f"""
            Proporciona 3-5 recomendaciones basadas en estos datos:
            {json.dumps(analytics, indent=2, default=str)}
            
            Formato: líneas numeradas.
            """
            
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            text = message.content[0].text
            recommendations = [r.strip() for r in text.split('\n') if r.strip()]
            self.tokens_used += message.usage.input_tokens + message.usage.output_tokens
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error en recomendaciones: {str(e)}")
            return []
    
    def _build_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Construir prompt para análisis"""
        return f"""
        Analiza los siguientes datos de reportes médicos:
        
        {json.dumps(data, indent=2, default=str)}
        
        Contexto: {context}
        
        Proporciona hallazgos, tendencias, áreas de preocupación y mejoras.
        """


class LocalLLMAdapter(LLMAdapter):
    """Adaptador para modelos LLM locales (Ollama, LM Studio, etc)"""
    
    def __init__(self, model_name: str, base_url: str = "http://localhost:11434"):
        """
        Inicializar adaptador LLM local.
        
        Args:
            model_name: Nombre del modelo instalado localmente
            base_url: URL del servidor LLM (default: Ollama)
        """
        super().__init__(model_name=model_name)
        self.base_url = base_url
        
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.warning("requests package no instalado")
            self.requests = None
    
    def analyze_data(self, data: Dict[str, Any], context: str = "") -> str:
        """Analizar datos usando LLM local"""
        if not self.requests:
            return "Error: requests no disponible"
        
        try:
            prompt = self._build_analysis_prompt(data, context)
            
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json().get('response', '')
                logger.info(f"Análisis local completado")
                return result
            else:
                logger.error(f"Error LLM local: {response.status_code}")
                return "Error en análisis local"
                
        except Exception as e:
            logger.error(f"Error conectando LLM local: {str(e)}")
            return f"Error conectando a {self.base_url}"
    
    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generar resumen usando LLM local"""
        if not self.requests:
            return text[:max_length]
        
        try:
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": f"Resume en {max_length} caracteres:\n{self._sanitize_input(text)}",
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('response', text[:max_length])
            else:
                return text[:max_length]
                
        except Exception as e:
            logger.error(f"Error en resumen local: {str(e)}")
            return text[:max_length]
    
    def generate_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones usando LLM local"""
        if not self.requests:
            return []
        
        try:
            prompt = f"Recomendaciones basadas en:\n{json.dumps(analytics, indent=2, default=str)}"
            
            response = self.requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                text = response.json().get('response', '')
                recommendations = [r.strip() for r in text.split('\n') if r.strip()]
                return recommendations[:5]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error en recomendaciones local: {str(e)}")
            return []
    
    def _build_analysis_prompt(self, data: Dict[str, Any], context: str) -> str:
        """Construir prompt para análisis"""
        return f"""
        Analiza los siguientes datos de reportes médicos:
        
        {json.dumps(data, indent=2, default=str)}
        
        Contexto: {context}
        
        Proporciona hallazgos principales, tendencias y recomendaciones.
        """


class LLMManager:
    """
    Gestor centralizado de adaptadores LLM.
    Permite cambiar entre diferentes LLMs fácilmente.
    """
    
    _adapters = {}
    _current_adapter = None
    
    @classmethod
    def register_adapter(cls, name: str, adapter: LLMAdapter) -> None:
        """Registrar un adaptador LLM"""
        cls._adapters[name] = adapter
        logger.info(f"Adaptador LLM '{name}' registrado")
    
    @classmethod
    def set_current(cls, name: str) -> bool:
        """
        Establecer el adaptador actual.
        
        Returns:
            bool: True si fue establecido exitosamente
        """
        if name in cls._adapters and cls._adapters[name].is_available():
            cls._current_adapter = name
            logger.info(f"Adaptador LLM actual: {name}")
            return True
        else:
            logger.warning(f"Adaptador '{name}' no disponible")
            return False
    
    @classmethod
    def get_current(cls) -> Optional[LLMAdapter]:
        """Obtener adaptador actual"""
        if cls._current_adapter and cls._current_adapter in cls._adapters:
            return cls._adapters[cls._current_adapter]
        return None
    
    @classmethod
    def analyze(cls, data: Dict[str, Any], context: str = "") -> str:
        """Analizar datos usando adaptador actual"""
        adapter = cls.get_current()
        if not adapter:
            return "No hay adaptador LLM disponible"
        return adapter.analyze_data(data, context)
    
    @classmethod
    def summarize(cls, text: str, max_length: int = 500) -> str:
        """Resumir texto usando adaptador actual"""
        adapter = cls.get_current()
        if not adapter:
            return text[:max_length]
        return adapter.generate_summary(text, max_length)
    
    @classmethod
    def recommend(cls, analytics: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones usando adaptador actual"""
        adapter = cls.get_current()
        if not adapter:
            return []
        return adapter.generate_recommendations(analytics)
    
    @classmethod
    def get_available_adapters(cls) -> List[str]:
        """Obtener lista de adaptadores disponibles"""
        return [name for name, adapter in cls._adapters.items() if adapter.is_available()]
