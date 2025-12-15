#!/usr/bin/env python3
"""
Ejemplo de código siguiendo Clean Architecture y principios SOLID.
Este archivo muestra cómo estructurar código de producción correctamente.

IMPORTANTE: Este es código de PRODUCCIÓN, NO test.
- NO hardcodear credenciales
- Seguir principios SOLID
- Documentar correctamente
- Manejar errores apropiadamente
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Protocol
from enum import Enum
import os
import logging

# Configurar logging (NO exponer información sensible)
logger = logging.getLogger(__name__)

# ============================================================================
# DOMAIN LAYER - Entidades y lógica de negocio pura
# ============================================================================

class RiskLevel(Enum):
    """Enum para niveles de riesgo."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class Product:
    """
    Entidad Product del dominio.
    
    Esta clase representa un producto en nuestro sistema.
    Es una entidad pura del dominio sin dependencias externas.
    """
    id: int
    name: str
    ean: str
    price: float
    stock: int
    risk_level: RiskLevel
    last_updated: datetime
    
    def __post_init__(self):
        """Validaciones de la entidad."""
        if self.price < 0:
            raise ValueError("Price cannot be negative")
        if self.stock < 0:
            raise ValueError("Stock cannot be negative")
    
    def is_low_stock(self, threshold: int = 10) -> bool:
        """
        Determina si el producto tiene stock bajo.
        
        Args:
            threshold: Umbral para considerar stock bajo
            
        Returns:
            True si el stock está por debajo del umbral
        """
        return self.stock < threshold
    
    def needs_reorder(self) -> bool:
        """
        Lógica de negocio: ¿Necesita reorden?
        
        Un producto necesita reorden si:
        - Tiene stock bajo Y
        - Su nivel de riesgo es MEDIUM o mayor
        """
        return self.is_low_stock() and self.risk_level.value >= RiskLevel.MEDIUM.value

# ============================================================================
# INTERFACES (Dependency Inversion Principle)
# ============================================================================

class ProductRepository(Protocol):
    """
    Interface para el repositorio de productos.
    
    Esta es una abstracción (Protocol) que define el contrato
    sin especificar la implementación (MySQL, MongoDB, etc).
    """
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Obtener producto por ID."""
        ...
    
    def get_all(self) -> List[Product]:
        """Obtener todos los productos."""
        ...
    
    def save(self, product: Product) -> Product:
        """Guardar o actualizar producto."""
        ...
    
    def delete(self, product_id: int) -> bool:
        """Eliminar producto."""
        ...

class NotificationService(Protocol):
    """Interface para servicio de notificaciones."""
    
    def send_notification(self, message: str, recipient: str) -> bool:
        """Enviar notificación."""
        ...

# ============================================================================
# USE CASES - Lógica de aplicación
# ============================================================================

class ProductStockAnalyzer:
    """
    Caso de uso: Analizar stock de productos.
    
    Single Responsibility: Solo analiza stock
    Dependency Injection: Recibe dependencias en constructor
    """
    
    def __init__(
        self,
        repository: ProductRepository,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Constructor con inyección de dependencias.
        
        Args:
            repository: Repositorio de productos (abstracción)
            notification_service: Servicio de notificaciones opcional
        """
        self.repository = repository
        self.notification_service = notification_service
        
        # Configuración desde variables de entorno (NUNCA hardcodeada)
        self.critical_threshold = int(os.getenv('STOCK_CRITICAL_THRESHOLD', '5'))
        self.notification_email = os.getenv('STOCK_ALERT_EMAIL', '')
    
    def analyze_all_products(self) -> dict:
        """
        Analiza el stock de todos los productos.
        
        Returns:
            Diccionario con estadísticas del análisis
        """
        try:
            products = self.repository.get_all()
            
            stats = {
                'total_products': len(products),
                'low_stock': [],
                'needs_reorder': [],
                'critical': []
            }
            
            for product in products:
                # Análisis de cada producto
                if product.is_low_stock():
                    stats['low_stock'].append(product.id)
                    
                    if product.stock < self.critical_threshold:
                        stats['critical'].append(product.id)
                        self._handle_critical_stock(product)
                
                if product.needs_reorder():
                    stats['needs_reorder'].append(product.id)
            
            logger.info(f"Stock analysis completed: {stats['total_products']} products analyzed")
            return stats
            
        except Exception as e:
            # Log error sin exponer detalles sensibles
            logger.error(f"Error analyzing stock: {str(e)[:100]}")
            raise
    
    def _handle_critical_stock(self, product: Product) -> None:
        """
        Maneja productos con stock crítico.
        
        Método privado que encapsula la lógica de manejo crítico.
        """
        if self.notification_service and self.notification_email:
            message = f"ALERTA: Producto {product.name} con stock crítico: {product.stock}"
            
            try:
                self.notification_service.send_notification(
                    message=message,
                    recipient=self.notification_email
                )
            except Exception as e:
                # No fallar si la notificación falla
                logger.warning(f"Could not send notification: {str(e)[:50]}")

class ReorderManager:
    """
    Caso de uso: Gestionar reordenes de productos.
    
    Open/Closed Principle: Abierto para extensión, cerrado para modificación
    """
    
    def __init__(self, repository: ProductRepository):
        """
        Constructor con inyección de dependencias.
        
        Args:
            repository: Repositorio de productos
        """
        self.repository = repository
        
        # Estrategias de reorden (extensible sin modificar la clase)
        self.reorder_strategies = {
            RiskLevel.LOW: self._standard_reorder,
            RiskLevel.MEDIUM: self._priority_reorder,
            RiskLevel.HIGH: self._urgent_reorder,
            RiskLevel.CRITICAL: self._emergency_reorder
        }
    
    def process_reorders(self) -> List[dict]:
        """
        Procesa todos los productos que necesitan reorden.
        
        Returns:
            Lista de órdenes de recompra generadas
        """
        products = self.repository.get_all()
        orders = []
        
        for product in products:
            if product.needs_reorder():
                order = self._create_reorder(product)
                if order:
                    orders.append(order)
        
        logger.info(f"Generated {len(orders)} reorder requests")
        return orders
    
    def _create_reorder(self, product: Product) -> Optional[dict]:
        """
        Crea una orden de recompra basada en el nivel de riesgo.
        
        Args:
            product: Producto a reordenar
            
        Returns:
            Diccionario con la orden o None si no aplica
        """
        strategy = self.reorder_strategies.get(product.risk_level)
        
        if strategy:
            return strategy(product)
        
        return None
    
    def _standard_reorder(self, product: Product) -> dict:
        """Estrategia de reorden estándar."""
        return {
            'product_id': product.id,
            'quantity': 100,
            'priority': 'normal',
            'estimated_days': 7
        }
    
    def _priority_reorder(self, product: Product) -> dict:
        """Estrategia de reorden prioritaria."""
        return {
            'product_id': product.id,
            'quantity': 200,
            'priority': 'high',
            'estimated_days': 3
        }
    
    def _urgent_reorder(self, product: Product) -> dict:
        """Estrategia de reorden urgente."""
        return {
            'product_id': product.id,
            'quantity': 300,
            'priority': 'urgent',
            'estimated_days': 1
        }
    
    def _emergency_reorder(self, product: Product) -> dict:
        """Estrategia de reorden de emergencia."""
        return {
            'product_id': product.id,
            'quantity': 500,
            'priority': 'emergency',
            'estimated_days': 0,
            'alert': True
        }

# ============================================================================
# SERVICIOS DEL DOMINIO
# ============================================================================

class RiskCalculator:
    """
    Servicio del dominio para calcular niveles de riesgo.
    
    Liskov Substitution: Puede ser reemplazado por cualquier
    implementación que respete el contrato.
    """
    
    @staticmethod
    def calculate_risk_level(
        stock: int,
        avg_sales: float,
        days_of_stock: int
    ) -> RiskLevel:
        """
        Calcula el nivel de riesgo basado en métricas.
        
        Args:
            stock: Stock actual
            avg_sales: Ventas promedio diarias
            days_of_stock: Días de stock restante
            
        Returns:
            Nivel de riesgo calculado
        """
        if stock == 0 or days_of_stock < 1:
            return RiskLevel.CRITICAL
        elif days_of_stock < 3:
            return RiskLevel.HIGH
        elif days_of_stock < 7:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

# ============================================================================
# VALUE OBJECTS
# ============================================================================

@dataclass(frozen=True)
class Money:
    """
    Value Object para representar dinero.
    
    Los Value Objects son inmutables y se comparan por valor.
    """
    amount: float
    currency: str = 'EUR'
    
    def __post_init__(self):
        """Validación del value object."""
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency is required")
    
    def add(self, other: 'Money') -> 'Money':
        """
        Suma dos cantidades de dinero.
        
        Args:
            other: Otra cantidad de dinero
            
        Returns:
            Nueva instancia con la suma
            
        Raises:
            ValueError: Si las monedas no coinciden
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        
        return Money(self.amount + other.amount, self.currency)

# ============================================================================
# EJEMPLO DE USO (con inyección de dependencias)
# ============================================================================

def main():
    """
    Ejemplo de cómo usar las clases con inyección de dependencias.
    
    NOTA: En producción real, esto vendría del contenedor de DI.
    """
    # Las implementaciones concretas se inyectan
    # repository = MySQLProductRepository()  # o MongoDBProductRepository()
    # notification = EmailNotificationService()  # o SlackNotificationService()
    
    # analyzer = ProductStockAnalyzer(
    #     repository=repository,
    #     notification_service=notification
    # )
    
    # stats = analyzer.analyze_all_products()
    # print(f"Analysis complete: {stats}")
    
    pass

if __name__ == '__main__':
    # En producción, nunca ejecutar directamente
    # Este código debe ser invocado por el framework/contenedor
    main()

"""
RESUMEN DE BUENAS PRÁCTICAS EN ESTE ARCHIVO:

1. ✅ SEGURIDAD:
   - NO hay credenciales hardcodeadas
   - Configuración desde variables de entorno
   - Logs sin información sensible

2. ✅ PRINCIPIOS SOLID:
   - Single Responsibility: Cada clase tiene una sola responsabilidad
   - Open/Closed: Extensible sin modificación (estrategias de reorden)
   - Liskov Substitution: Interfaces y abstracciones
   - Interface Segregation: Interfaces pequeñas y específicas
   - Dependency Inversion: Depende de abstracciones, no concreciones

3. ✅ CLEAN ARCHITECTURE:
   - Entidades puras del dominio (Product)
   - Casos de uso independientes (ProductStockAnalyzer)
   - Interfaces/Protocols para abstracciones
   - Value Objects inmutables (Money)

4. ✅ DOCUMENTACIÓN:
   - Docstrings completos
   - Type hints en todos los métodos
   - Comentarios donde agregan valor

5. ✅ MANEJO DE ERRORES:
   - Validaciones en constructores
   - Try/catch con logging apropiado
   - No silenciar errores críticos
"""
