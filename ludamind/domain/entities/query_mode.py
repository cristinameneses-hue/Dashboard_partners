#!/usr/bin/env python3
"""
Entidad QueryMode - Define los modos de consulta del sistema.
Siguiendo Clean Architecture y principios SOLID.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from datetime import datetime


class QueryMode(Enum):
    """
    Enum que define los modos de consulta disponibles.
    """
    PHARMACY = "pharmacy"      # Consultas por farmacia
    PRODUCT = "product"        # Consultas por producto
    PARTNER = "partner"        # Consultas por partner/canal
    CONVERSATIONAL = "chat"    # Consultas abiertas/conversacionales


@dataclass
class ModeContext:
    """
    Contexto asociado a cada modo de consulta.
    Contiene la información necesaria para guiar al usuario y al modelo.
    """
    mode: QueryMode
    name: str
    description: str
    icon: str
    primary_key: str  # Campo clave para este modo
    database_hints: List[str]  # Bases de datos relevantes
    suggested_queries: List[str]  # Sugerencias para el usuario
    ai_context: str  # Contexto adicional para el modelo
    filters: Dict[str, Any]  # Filtros predefinidos para este modo
    
    def get_user_prompt(self) -> str:
        """
        Genera el prompt de ayuda para el usuario.
        """
        prompt = f"## {self.icon} Modo {self.name}\n\n"
        prompt += f"{self.description}\n\n"
        prompt += "### Ejemplos de consultas:\n"
        for i, suggestion in enumerate(self.suggested_queries[:5], 1):
            prompt += f"{i}. {suggestion}\n"
        return prompt
    
    def get_ai_context(self) -> str:
        """
        Genera el contexto adicional para el modelo de IA.
        """
        return f"""
Modo activo: {self.name}
Campo clave: {self.primary_key}
Contexto: {self.ai_context}
Bases de datos relevantes: {', '.join(self.database_hints)}
"""


# Definición de contextos para cada modo
MODE_CONTEXTS = {
    QueryMode.PHARMACY: ModeContext(
        mode=QueryMode.PHARMACY,
        name="Farmacias",
        description="Analiza datos específicos de farmacias individuales o grupos de farmacias",
        icon="🏥",
        primary_key="pharmacy_id",
        database_hints=["mongodb.pharmacies", "mongodb.bookings", "mongodb.users"],
        suggested_queries=[
            "¿Cuál es el estado de la farmacia 123?",
            "¿Cuántos pedidos tiene la farmacia 456 esta semana?",
            "¿Qué productos vende más la farmacia 789?",
            "Mostrar farmacias activas en Madrid",
            "¿Cuál es el GMV de la farmacia 234 este mes?",
            "Farmacias con más de 100 pedidos hoy",
            "Estado del stock en farmacia 567",
            "Usuarios activos de la farmacia 890"
        ],
        ai_context="El usuario está consultando datos específicos de farmacias. Busca campos como pharmacy_id, pharmacyId, pharmacy.name, pharmacy.address. Prioriza datos operacionales y de rendimiento por farmacia.",
        filters={"entity_type": "pharmacy", "active": True}
    ),
    
    QueryMode.PRODUCT: ModeContext(
        mode=QueryMode.PRODUCT,
        name="Productos",
        description="Consulta información sobre productos, medicamentos y su rendimiento",
        icon="💊",
        primary_key="id_farmaco",
        database_hints=["mysql.product_sales", "mongodb.items", "mongodb.stockItems"],
        suggested_queries=[
            "¿Cuántas unidades del producto 12345 se vendieron?",
            "Stock actual del código nacional 67890",
            "Top 10 productos más vendidos esta semana",
            "Productos en grupo de riesgo 3",
            "¿Qué farmacias tienen el producto 11111?",
            "Histórico de ventas del producto 22222",
            "Productos con stock crítico",
            "Precio actual del medicamento 33333",
            "Tendencia de ventas del producto 44444"
        ],
        ai_context="El usuario está consultando sobre productos/medicamentos. Busca campos como id_farmaco, codigo_nacional, product_id, item.ean, item.name. Enfócate en ventas, stock, precios y tendencias de productos.",
        filters={"entity_type": "product"}
    ),
    
    QueryMode.PARTNER: ModeContext(
        mode=QueryMode.PARTNER,
        name="Partners",
        description="Analiza el rendimiento de partners y canales de venta (Glovo, Uber, etc.)",
        icon="🤝",
        primary_key="thidUser.user",
        database_hints=["mongodb.bookings", "mongodb.payments"],
        suggested_queries=[
            "GMV total de Glovo esta semana",
            "¿Cuántos pedidos ha generado Uber hoy?",
            "Comparación de GMV entre Glovo y Uber",
            "Top farmacias por canal Glovo",
            "Tasa de conversión de Danone",
            "Pedidos de Carrefour del mes pasado",
            "¿Cuál partner genera más ingresos?",
            "Evolución mensual de pedidos por partner",
            "Comisiones pagadas a Glovo este mes"
        ],
        ai_context="El usuario está analizando partners/canales. Busca campos como creator, thidUser.user, channel, partner. Los partners principales son: Glovo, Uber, Danone, Hartmann, Carrefour. Enfócate en GMV, pedidos, conversiones y métricas por canal.",
        filters={"entity_type": "partner"}
    ),
    
    QueryMode.CONVERSATIONAL: ModeContext(
        mode=QueryMode.CONVERSATIONAL,
        name="Conversacional",
        description="Consultas abiertas y análisis complejos que cruzan múltiples dimensiones",
        icon="💬",
        primary_key="*",
        database_hints=["mysql.*", "mongodb.*"],
        suggested_queries=[
            "¿Cuál es el estado general del negocio?",
            "Resumen ejecutivo de esta semana",
            "¿Qué anomalías detectas en los datos?",
            "Tendencias principales del último mes",
            "Análisis comparativo año vs año anterior",
            "¿Qué oportunidades de mejora identificas?",
            "Dashboard de KPIs principales",
            "Predicción de ventas para próximo mes"
        ],
        ai_context="El usuario está haciendo consultas abiertas que pueden requerir análisis complejos, cruces de datos, o respuestas más narrativas. No hay restricciones de contexto, usa tu mejor criterio para interpretar y responder de manera útil.",
        filters={}
    )
}


@dataclass
class QuerySession:
    """
    Sesión de consulta que mantiene el modo y contexto actual.
    """
    session_id: str
    user_id: str
    current_mode: QueryMode
    mode_context: ModeContext
    started_at: datetime
    query_count: int = 0
    last_entity_id: Optional[str] = None  # Último ID consultado
    
    def update_mode(self, new_mode: QueryMode) -> None:
        """
        Cambia el modo de la sesión.
        
        Args:
            new_mode: Nuevo modo a establecer
        """
        self.current_mode = new_mode
        self.mode_context = MODE_CONTEXTS[new_mode]
        self.last_entity_id = None  # Reset al cambiar de modo
    
    def increment_queries(self) -> None:
        """Incrementa el contador de consultas."""
        self.query_count += 1
    
    def set_last_entity(self, entity_id: str) -> None:
        """
        Guarda el último ID de entidad consultado.
        Útil para consultas de seguimiento.
        
        Args:
            entity_id: ID de la entidad consultada
        """
        self.last_entity_id = entity_id
    
    def get_context_for_ai(self) -> Dict[str, Any]:
        """
        Obtiene el contexto completo para el modelo de IA.
        
        Returns:
            Diccionario con todo el contexto relevante
        """
        return {
            "mode": self.current_mode.value,
            "mode_name": self.mode_context.name,
            "primary_key": self.mode_context.primary_key,
            "ai_context": self.mode_context.ai_context,
            "database_hints": self.mode_context.database_hints,
            "filters": self.mode_context.filters,
            "last_entity_id": self.last_entity_id,
            "query_count": self.query_count
        }


class ModeSelector:
    """
    Servicio para selección automática de modo basado en la consulta.
    """
    
    # Keywords para detección automática de modo
    MODE_KEYWORDS = {
        QueryMode.PHARMACY: [
            'farmacia', 'pharmacy', 'pharmacy_id', 'pharmacyid',
            'sucursal', 'establecimiento', 'local'
        ],
        QueryMode.PRODUCT: [
            'producto', 'medicamento', 'medicina', 'fármaco',
            'id_farmaco', 'codigo_nacional', 'ean', 'stock',
            'inventario', 'precio'
        ],
        QueryMode.PARTNER: [
            'glovo', 'uber', 'danone', 'hartmann', 'carrefour',
            'partner', 'canal', 'channel', 'gmv', 'comisión',
            'thiduser', 'creator'
        ]
    }
    
    @classmethod
    def suggest_mode(cls, query: str) -> Optional[QueryMode]:
        """
        Sugiere un modo basado en el contenido de la consulta.
        
        Args:
            query: Texto de la consulta
            
        Returns:
            Modo sugerido o None si no hay coincidencia clara
        """
        query_lower = query.lower()
        
        # Contar coincidencias por modo
        mode_scores = {}
        
        for mode, keywords in cls.MODE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                mode_scores[mode] = score
        
        # Retornar el modo con mayor score
        if mode_scores:
            return max(mode_scores, key=mode_scores.get)
        
        # Default a conversacional si no hay coincidencias
        return QueryMode.CONVERSATIONAL
    
    @classmethod
    def extract_entity_id(cls, query: str, mode: QueryMode) -> Optional[str]:
        """
        Intenta extraer el ID de entidad relevante de la consulta.
        
        Args:
            query: Texto de la consulta
            mode: Modo actual
            
        Returns:
            ID extraído o None
        """
        import re
        
        if mode == QueryMode.PHARMACY:
            # Buscar pharmacy_id o números que parezcan IDs
            match = re.search(r'pharmacy[_\s]?(?:id)?[:\s]?(\d+)', query, re.IGNORECASE)
            if not match:
                match = re.search(r'farmacia[:\s]?(\d+)', query, re.IGNORECASE)
            if match:
                return match.group(1)
                
        elif mode == QueryMode.PRODUCT:
            # Buscar id_farmaco o codigo_nacional
            match = re.search(r'(?:id_farmaco|codigo_nacional|producto)[:\s]?(\w+)', query, re.IGNORECASE)
            if not match:
                # Buscar cualquier número de 5-8 dígitos
                match = re.search(r'\b(\d{5,8})\b', query)
            if match:
                return match.group(1)
                
        elif mode == QueryMode.PARTNER:
            # Extraer nombre del partner
            partners = ['glovo', 'uber', 'danone', 'hartmann', 'carrefour']
            query_lower = query.lower()
            for partner in partners:
                if partner in query_lower:
                    return partner
        
        return None
