#!/usr/bin/env python3
"""
Servicio de contexto de consultas - Maneja los modos y el contexto de las sesiones.
Siguiendo Clean Architecture y principios SOLID.
"""

from typing import Dict, List, Optional, Protocol, Any
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict

from domain.entities.query_mode import (
    QueryMode, ModeContext, QuerySession, MODE_CONTEXTS, ModeSelector
)

logger = logging.getLogger(__name__)


class SessionRepository(Protocol):
    """
    Interfaz para el repositorio de sesiones (Dependency Inversion).
    """
    async def get(self, session_id: str) -> Optional[QuerySession]:
        """Obtiene una sesión por ID."""
        ...
    
    async def save(self, session: QuerySession) -> None:
        """Guarda o actualiza una sesión."""
        ...
    
    async def delete(self, session_id: str) -> None:
        """Elimina una sesión."""
        ...


class QueryEnhancer(Protocol):
    """
    Interfaz para mejorar queries con contexto adicional.
    """
    async def enhance(self, query: str, context: Dict[str, Any]) -> str:
        """Enriquece una query con contexto."""
        ...


@dataclass
class EnhancedQuery:
    """
    Query mejorada con contexto del modo.
    """
    original_query: str
    enhanced_query: str
    mode: QueryMode
    context: Dict[str, Any]
    entity_id: Optional[str]
    suggested_filters: Dict[str, Any]
    confidence: float  # 0.0 a 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {
            'original_query': self.original_query,
            'enhanced_query': self.enhanced_query,
            'mode': self.mode.value,
            'context': self.context,
            'entity_id': self.entity_id,
            'suggested_filters': self.suggested_filters,
            'confidence': self.confidence
        }


class QueryContextService:
    """
    Servicio principal para gestionar el contexto de las consultas.
    Single Responsibility: Gestionar contexto y modos de consulta.
    """
    
    def __init__(
        self,
        session_repository: Optional[SessionRepository] = None,
        query_enhancer: Optional[QueryEnhancer] = None
    ):
        """
        Constructor con inyección de dependencias.
        
        Args:
            session_repository: Repositorio de sesiones
            query_enhancer: Servicio de mejora de queries
        """
        self.session_repository = session_repository
        self.query_enhancer = query_enhancer
        self.active_sessions: Dict[str, QuerySession] = {}
        
    async def create_session(
        self,
        user_id: str,
        session_id: str,
        initial_mode: Optional[QueryMode] = None
    ) -> QuerySession:
        """
        Crea una nueva sesión de consulta.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
            initial_mode: Modo inicial (opcional)
            
        Returns:
            Nueva sesión creada
        """
        mode = initial_mode or QueryMode.CONVERSATIONAL
        mode_context = MODE_CONTEXTS[mode]
        
        session = QuerySession(
            session_id=session_id,
            user_id=user_id,
            current_mode=mode,
            mode_context=mode_context,
            started_at=datetime.now()
        )
        
        # Guardar en memoria y repositorio
        self.active_sessions[session_id] = session
        if self.session_repository:
            await self.session_repository.save(session)
        
        logger.info(f"Session created: {session_id} with mode {mode.value}")
        return session
    
    async def get_or_create_session(
        self,
        user_id: str,
        session_id: str
    ) -> QuerySession:
        """
        Obtiene una sesión existente o crea una nueva.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
            
        Returns:
            Sesión obtenida o creada
        """
        # Buscar en memoria primero
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Buscar en repositorio
        if self.session_repository:
            session = await self.session_repository.get(session_id)
            if session:
                self.active_sessions[session_id] = session
                return session
        
        # Crear nueva sesión
        return await self.create_session(user_id, session_id)
    
    async def change_mode(
        self,
        session_id: str,
        new_mode: QueryMode
    ) -> QuerySession:
        """
        Cambia el modo de una sesión.
        
        Args:
            session_id: ID de la sesión
            new_mode: Nuevo modo
            
        Returns:
            Sesión actualizada
            
        Raises:
            ValueError: Si la sesión no existe
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.update_mode(new_mode)
        
        # Guardar cambios
        if self.session_repository:
            await self.session_repository.save(session)
        
        logger.info(f"Session {session_id} mode changed to {new_mode.value}")
        return session
    
    async def enhance_query(
        self,
        query: str,
        session_id: str
    ) -> EnhancedQuery:
        """
        Mejora una consulta con el contexto del modo actual.
        
        Args:
            query: Consulta original
            session_id: ID de la sesión
            
        Returns:
            Consulta mejorada con contexto
        """
        session = await self.get_or_create_session("unknown", session_id)
        session.increment_queries()
        
        # Detectar si la query sugiere un cambio de modo
        suggested_mode = ModeSelector.suggest_mode(query)
        confidence = 0.8 if suggested_mode == session.current_mode else 0.5
        
        # Extraer ID de entidad si es posible
        entity_id = ModeSelector.extract_entity_id(query, session.current_mode)
        if entity_id:
            session.set_last_entity(entity_id)
            confidence += 0.2
        
        # Construir contexto
        context = session.get_context_for_ai()
        
        # Mejorar la query con contexto adicional
        enhanced = await self._build_enhanced_query(
            query, session, entity_id
        )
        
        # Construir filtros sugeridos
        filters = self._build_filters(session.current_mode, entity_id)
        
        return EnhancedQuery(
            original_query=query,
            enhanced_query=enhanced,
            mode=session.current_mode,
            context=context,
            entity_id=entity_id,
            suggested_filters=filters,
            confidence=min(confidence, 1.0)
        )
    
    async def _build_enhanced_query(
        self,
        query: str,
        session: QuerySession,
        entity_id: Optional[str]
    ) -> str:
        """
        Construye una query mejorada con contexto.
        
        Args:
            query: Query original
            session: Sesión actual
            entity_id: ID de entidad extraído
            
        Returns:
            Query mejorada
        """
        enhanced = query
        
        # Añadir contexto según el modo
        if session.current_mode == QueryMode.PHARMACY and entity_id:
            if "pharmacy" not in query.lower() and "farmacia" not in query.lower():
                enhanced = f"Para la farmacia {entity_id}: {query}"
                
        elif session.current_mode == QueryMode.PRODUCT and entity_id:
            if "producto" not in query.lower() and "product" not in query.lower():
                enhanced = f"Para el producto {entity_id}: {query}"
                
        elif session.current_mode == QueryMode.PARTNER:
            # Asegurar que el partner está claro
            if entity_id and entity_id not in query.lower():
                enhanced = f"Partner {entity_id}: {query}"
        
        # Si tenemos un enhancer externo, usarlo
        if self.query_enhancer:
            context = session.get_context_for_ai()
            enhanced = await self.query_enhancer.enhance(enhanced, context)
        
        return enhanced
    
    def _build_filters(
        self,
        mode: QueryMode,
        entity_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Construye filtros sugeridos basados en el modo.
        
        Args:
            mode: Modo actual
            entity_id: ID de entidad
            
        Returns:
            Diccionario de filtros
        """
        filters = MODE_CONTEXTS[mode].filters.copy()
        
        if entity_id:
            if mode == QueryMode.PHARMACY:
                filters['pharmacy_id'] = entity_id
            elif mode == QueryMode.PRODUCT:
                filters['product_id'] = entity_id
            elif mode == QueryMode.PARTNER:
                filters['partner'] = entity_id
        
        return filters
    
    def get_mode_suggestions(self, mode: QueryMode) -> Dict[str, Any]:
        """
        Obtiene las sugerencias para un modo específico.
        
        Args:
            mode: Modo para el que obtener sugerencias
            
        Returns:
            Diccionario con información del modo y sugerencias
        """
        context = MODE_CONTEXTS[mode]
        
        return {
            'mode': mode.value,
            'name': context.name,
            'description': context.description,
            'icon': context.icon,
            'suggestions': context.suggested_queries,
            'help_text': context.get_user_prompt()
        }
    
    def get_all_modes(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los modos disponibles.
        
        Returns:
            Lista con información de cada modo
        """
        return [
            {
                'value': mode.value,
                'name': context.name,
                'description': context.description,
                'icon': context.icon,
                'is_default': mode == QueryMode.CONVERSATIONAL
            }
            for mode, context in MODE_CONTEXTS.items()
        ]
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de una sesión.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Estadísticas de la sesión
        """
        if session_id not in self.active_sessions:
            return {'error': 'Session not found'}
        
        session = self.active_sessions[session_id]
        duration = datetime.now() - session.started_at
        
        return {
            'session_id': session_id,
            'user_id': session.user_id,
            'current_mode': session.current_mode.value,
            'query_count': session.query_count,
            'duration_seconds': duration.total_seconds(),
            'started_at': session.started_at.isoformat(),
            'last_entity_id': session.last_entity_id
        }
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Limpia sesiones antiguas.
        
        Args:
            max_age_hours: Edad máxima en horas
            
        Returns:
            Número de sesiones eliminadas
        """
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for session_id, session in self.active_sessions.items():
            if session.started_at < cutoff:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self.active_sessions[session_id]
            if self.session_repository:
                await self.session_repository.delete(session_id)
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old sessions")
        
        return len(to_remove)
