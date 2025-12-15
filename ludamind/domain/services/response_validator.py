#!/usr/bin/env python3
"""
Response Validator - Valida y corrige respuestas de GPT
Sistema de post-procesamiento robusto para garantizar respuestas válidas
"""

import json
import re
from typing import Dict, Any, Optional, List
from datetime import datetime


class ResponseValidator:
    """
    Valida y corrige respuestas de GPT para garantizar formato correcto.
    
    IMPORTANTE: Este validador NUNCA debe lanzar excepciones.
    Si no puede corregir, devuelve la respuesta original o un fallback seguro.
    """
    
    def __init__(self):
        self.validation_log = []
    
    def validate_and_fix(self, gpt_response: Any, original_query: str, mode: str) -> Dict[str, Any]:
        """
        Valida y corrige respuesta de GPT.
        
        Args:
            gpt_response: Respuesta de GPT (puede ser dict, str, etc.)
            original_query: Query original del usuario (para fallback)
            mode: Modo activo (pharmacy, product, partner, conversational)
        
        Returns:
            Dict con estructura válida garantizada
        """
        issues = []
        
        try:
            # 1. Convertir a dict si no lo es
            if not isinstance(gpt_response, dict):
                issues.append("not_dict")
                gpt_response = self._try_parse_as_dict(gpt_response)
            
            # Si no pudimos convertir, usar fallback completo
            if not isinstance(gpt_response, dict):
                issues.append("failed_to_parse")
                return self._create_fallback_response(original_query, mode, issues)
            
            # 2. Verificar campos obligatorios
            if 'collection' not in gpt_response or not gpt_response['collection']:
                issues.append("missing_collection")
                gpt_response['collection'] = self._infer_collection(original_query, mode)
            
            if 'pipeline' not in gpt_response:
                issues.append("missing_pipeline")
                gpt_response['pipeline'] = []
            
            # 3. Validar que pipeline sea una lista
            if not isinstance(gpt_response.get('pipeline'), list):
                issues.append("invalid_pipeline_type")
                gpt_response['pipeline'] = self._try_fix_pipeline(gpt_response.get('pipeline'))
            
            # 4. Verificar si está truncado
            if self._is_truncated(gpt_response):
                issues.append("truncated_response")
                # Intentar reparar
                gpt_response = self._repair_truncated(gpt_response, original_query, mode)
            
            # 5. Asegurar explanation existe
            if 'explanation' not in gpt_response or not gpt_response['explanation']:
                gpt_response['explanation'] = f"Consulta sobre {gpt_response.get('collection', 'datos')}"
            
            # 6. Verificar que explanation no sea JSON (error común)
            if isinstance(gpt_response.get('explanation'), str):
                if gpt_response['explanation'].strip().startswith('{'):
                    issues.append("explanation_is_json")
                    # Intentar extraer pipeline de explanation
                    extracted = self._extract_pipeline_from_explanation(gpt_response['explanation'])
                    if extracted:
                        gpt_response['pipeline'] = extracted
                        gpt_response['explanation'] = "Query procesada correctamente"
            
            # 7. Añadir confidence si no existe
            if 'confidence' not in gpt_response:
                gpt_response['confidence'] = 0.8 if not issues else 0.6
            
            # 8. Log de issues (solo para debug, no bloquea)
            if issues:
                self._log_validation_issues(original_query, issues)
            
            return gpt_response
        
        except Exception as e:
            # Si TODO falla, devolver fallback seguro
            return self._create_fallback_response(original_query, mode, [f"exception: {str(e)}"])
    
    def _try_parse_as_dict(self, response: Any) -> Any:
        """Intenta parsear respuesta como dict"""
        try:
            if isinstance(response, str):
                # Limpiar markdown si existe
                response = self._clean_markdown(response)
                # Intentar parsear JSON
                return json.loads(response)
            return response
        except:
            return response
    
    def _clean_markdown(self, text: str) -> str:
        """Limpia bloques de markdown del texto"""
        # Remover ```json ... ```
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        text = re.sub(r'```', '', text)
        return text.strip()
    
    def _is_truncated(self, response: dict) -> bool:
        """Detecta si la respuesta está truncada"""
        try:
            # Si explanation es un JSON string que no cierra
            if 'explanation' in response:
                exp = str(response['explanation'])
                # Contar llaves
                open_braces = exp.count('{')
                close_braces = exp.count('}')
                if open_braces > close_braces and open_braces > 0:
                    return True
            
            # Si pipeline está vacío pero explanation sugiere que hay query
            if not response.get('pipeline') or len(response.get('pipeline', [])) == 0:
                exp = str(response.get('explanation', ''))
                # Si menciona pipeline, match, group, etc. pero no hay pipeline
                if any(word in exp.lower() for word in ['pipeline', '$match', '$group', 'aggregate']):
                    return True
            
            return False
        except:
            return False
    
    def _repair_truncated(self, response: dict, query: str, mode: str) -> dict:
        """Intenta reparar respuesta truncada"""
        try:
            # Si explanation tiene JSON, intentar extraerlo
            exp = str(response.get('explanation', ''))
            if '{' in exp:
                # Intentar encontrar y parsear el JSON
                pipeline = self._extract_pipeline_from_explanation(exp)
                if pipeline:
                    response['pipeline'] = pipeline
                    response['explanation'] = "Query procesada correctamente"
                    return response
            
            # Si no se pudo reparar, devolver con pipeline vacío pero válido
            if not response.get('pipeline'):
                response['pipeline'] = []
            
            return response
        except:
            return response
    
    def _extract_pipeline_from_explanation(self, text: str) -> Optional[List[dict]]:
        """Intenta extraer pipeline de un texto"""
        try:
            # Buscar "pipeline": [...]
            match = re.search(r'"pipeline"\s*:\s*(\[.*?\])', text, re.DOTALL)
            if match:
                pipeline_str = match.group(1)
                # Intentar parsear
                pipeline = json.loads(pipeline_str)
                if isinstance(pipeline, list):
                    return pipeline
            return None
        except:
            return None
    
    def _try_fix_pipeline(self, pipeline: Any) -> List[dict]:
        """Intenta convertir pipeline a lista válida"""
        if isinstance(pipeline, list):
            return pipeline
        if isinstance(pipeline, dict):
            return [pipeline]
        if isinstance(pipeline, str):
            try:
                parsed = json.loads(pipeline)
                if isinstance(parsed, list):
                    return parsed
                if isinstance(parsed, dict):
                    return [parsed]
            except:
                pass
        return []
    
    def _infer_collection(self, query: str, mode: str) -> str:
        """Infiere la colección basándose en el query y modo"""
        query_lower = query.lower()
        
        # Palabras clave por colección
        if any(word in query_lower for word in ['farmacia', 'pharmacy']):
            # Si pregunta por activas, es pharmacies; si por pedidos, es bookings
            if any(word in query_lower for word in ['activa', 'active', 'cuántas']):
                return 'pharmacies'
            return 'bookings'
        
        if any(word in query_lower for word in ['producto', 'product', 'item', 'stock', 'precio']):
            if 'stock' in query_lower or 'precio' in query_lower:
                return 'stockItems'
            return 'items'
        
        if any(word in query_lower for word in ['partner', 'canal', 'gmv', 'pedido']):
            return 'bookings'
        
        # Fallback por modo
        mode_collections = {
            'pharmacy': 'pharmacies',
            'product': 'items',
            'partner': 'bookings',
            'conversational': 'bookings'
        }
        return mode_collections.get(mode, 'bookings')
    
    def _create_fallback_response(self, query: str, mode: str, issues: List[str]) -> dict:
        """Crea respuesta de fallback segura"""
        return {
            'collection': self._infer_collection(query, mode),
            'pipeline': [],
            'explanation': f"No se pudo interpretar la consulta completamente. Por favor, reformula tu pregunta.",
            'confidence': 0.3,
            'error': 'validation_failed',
            'issues': issues
        }
    
    def _log_validation_issues(self, query: str, issues: List[str]):
        """Registra issues para análisis posterior"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'issues': issues
        }
        self.validation_log.append(log_entry)
        # Solo mantener últimos 100
        if len(self.validation_log) > 100:
            self.validation_log = self.validation_log[-100:]


# Instancia global para uso compartido
_validator_instance = None

def get_validator() -> ResponseValidator:
    """Obtiene instancia singleton del validador"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ResponseValidator()
    return _validator_instance

