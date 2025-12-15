#!/usr/bin/env python3
"""
Output Type Detector - Detecta si el usuario quiere lista o agregación
Sistema de desambiguación basado en keywords
"""

from typing import Literal


class OutputTypeDetector:
    """
    Detecta el tipo de output esperado por el usuario.
    
    REGLA DE DESAMBIGUACIÓN:
    - Si el usuario es EXPLÍCITO (usa keywords de detalle) → LISTA
    - Si el usuario es VAGO (sin keywords específicas) → AGREGACIÓN
    
    Esto mejora la UX devolviendo contadores rápidos por defecto.
    """
    
    # Keywords que indican que el usuario quiere LISTA con detalles
    LIST_KEYWORDS = [
        # Verbos de listado
        'lista', 'listame', 'listar',
        'muestra', 'muéstrame', 'mostrar',
        'ver', 'dame', 'dime',
        
        # Interrogativos de detalle
        'cuáles', 'cuál', 'qué',
        
        # Cuantificadores que implican lista
        'todos', 'todas',
        
        # Acciones de detalle
        'detalla', 'detalle', 'completo', 'completa'
    ]
    
    # Keywords que indican AGREGACIÓN (count/sum)
    AGGREGATION_KEYWORDS = [
        # Interrogativos de cantidad
        'cuántos', 'cuántas',
        
        # Operadores de agregación
        'total', 'cantidad', 'número',
        'suma', 'sumar',
        'promedio', 'media',
        'conteo', 'contar'
    ]
    
    def detect(self, query: str) -> Literal['list', 'aggregation']:
        """
        Detecta si el usuario quiere lista o agregación.
        
        Args:
            query: Query del usuario en lenguaje natural
        
        Returns:
            'list' si quiere detalles, 'aggregation' si quiere total
        
        Examples:
            >>> detector = OutputTypeDetector()
            >>> detector.detect("Farmacias en Madrid")
            'aggregation'  # Vago → count
            >>> detector.detect("Listame farmacias en Madrid")
            'list'  # Explícito → lista con detalles
        """
        query_lower = query.lower()
        
        # 1. Verificar keywords de LISTA (más específicas, tienen prioridad)
        for keyword in self.LIST_KEYWORDS:
            if keyword in query_lower:
                return 'list'
        
        # 2. Verificar keywords de AGREGACIÓN
        for keyword in self.AGGREGATION_KEYWORDS:
            if keyword in query_lower:
                return 'aggregation'
        
        # 3. Si no hay keywords explícitas → VAGO → AGREGACIÓN (regla por defecto)
        # Esto es mejor para UX: respuestas rápidas tipo "Hay 45 farmacias"
        return 'aggregation'
    
    def get_hint_for_gpt(self, output_type: Literal['list', 'aggregation']) -> str:
        """
        Genera hint para incluir en el prompt de GPT.
        
        Args:
            output_type: Tipo de output detectado
        
        Returns:
            Hint en español para GPT
        """
        if output_type == 'list':
            return """
**TIPO DE RESPUESTA ESPERADA: LISTA CON DETALLES**

El usuario quiere ver una LISTA con información detallada.

Por lo tanto:
- Usa $project para incluir campos relevantes (nombres, IDs, etc.)
- NO uses solo $count
- Incluye información identificable en cada resultado
- Si hay muchos resultados, limita a 20-50 con $limit

Ejemplo pipeline:
[
  {$match: {filtros}},
  {$project: {
    description: 1,
    contact.city: 1,
    active: 1
  }},
  {$limit: 50}
]
"""
        else:  # aggregation
            return """
**TIPO DE RESPUESTA ESPERADA: AGREGACIÓN (TOTAL)**

El usuario quiere un NÚMERO o TOTAL agregado.

Por lo tanto:
- Usa $count si solo quiere cantidad
- Usa $group + $sum para totales (GMV, pedidos, etc.)
- NO devuelvas listas largas
- Devuelve números o métricas agregadas

Ejemplo pipeline COUNT:
[
  {$match: {filtros}},
  {$count: "total"}
]

Ejemplo pipeline SUM:
[
  {$match: {filtros}},
  {$group: {
    _id: null,
    totalGMV: {$sum: ...},
    totalPedidos: {$sum: 1}
  }}
]
"""


# Instancia global
_detector_instance = None

def get_detector() -> OutputTypeDetector:
    """Obtiene instancia singleton del detector"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = OutputTypeDetector()
    return _detector_instance

