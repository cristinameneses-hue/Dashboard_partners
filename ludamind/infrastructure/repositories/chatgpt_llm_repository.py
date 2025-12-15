"""
ChatGPT LLM Repository Implementation

Specialized implementation for business team with ChatGPT.
Includes optimized system prompts and conversation management.
"""

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from datetime import datetime
import json
import time

from openai import AsyncOpenAI

from domain.repositories import LLMRepository
from domain.value_objects import DatabaseType, QuerySpec
from .openai_llm_repository import OpenAILLMRepository, ModelConfig

# Import LLM parser for robust response parsing
try:
    from infrastructure.llm import LLMResponseParser, ParseError
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    logger.warning("LLMResponseParser not available, using fallback parsing")


logger = logging.getLogger(__name__)


class ChatGPTBusinessConfig(ModelConfig):
    """Specialized configuration for ChatGPT business team."""

    def __init__(self):
        super().__init__(
            name="gpt-4",
            temperature=0.1,
            max_tokens=2000,
            input_cost_per_1k=0.03,  # GPT-4 pricing
            output_cost_per_1k=0.06
        )

        # Business-optimized system prompts
        self.query_generation_prompt = """
Eres un asistente experto en bases de datos para el equipo de negocio de LudaFarma.

Tu tarea es convertir preguntas en lenguaje natural a consultas de base de datos.

CONTEXTO DEL NEGOCIO:
- Somos una farmacia digital que opera con partners (Glovo, Uber, Danone, Hartmann, Carrefour)
- Tenemos dos sistemas de datos:
  * MySQL (trends): Datos analíticos, ventas, tendencias, predicciones, Z_Y scores
  * MongoDB (ludafarma): Datos operacionales, farmacias, usuarios, bookings, catálogo

REGLAS DE GENERACIÓN:
1. Si la pregunta es incompleta, genera una consulta con valores por defecto razonables
2. Para fechas sin especificar, usa los últimos 7 días
3. Para límites no especificados, usa 20 resultados
4. Identifica automáticamente el partner mencionado (Glovo, Uber, etc.)
5. Para GMV de partners, busca en bookings.creator
6. Para shortage/derivaciones, filtra por bookings con tipo específico

FORMATO DE RESPUESTA:
Devuelve un JSON con:
{
  "query": "la consulta SQL o MongoDB",
  "database": "mysql" o "mongodb",
  "explanation": "explicación de lo que hace la consulta",
  "assumptions": ["lista de suposiciones hechas"],
  "parameters": {}
}
"""

        self.answer_generation_prompt = """
Eres un asistente de análisis de datos para el equipo de negocio de LudaFarma.

Tu tarea es explicar los resultados de consultas de forma clara y accionable para decisiones de negocio.

REGLAS DE RESPUESTA:
1. Siempre responde en español
2. Sé conciso pero completo
3. Resalta los insights más importantes primero
4. Usa formato de moneda para valores monetarios (€)
5. Usa formato español para fechas (DD/MM/YYYY)
6. Si hay tendencias, menciónalas
7. Si hay anomalías o valores destacables, resáltalos
8. Proporciona contexto de negocio cuando sea relevante
9. Si los datos sugieren acciones, menciónalas

FORMATO PREFERIDO:
- Usa bullets para listas
- Usa **negrita** para valores importantes
- Agrupa información relacionada
- Termina con un resumen ejecutivo si hay muchos datos
"""


class ChatGPTLLMRepository(OpenAILLMRepository):
    """
    ChatGPT repository specialized for business team.

    Extends OpenAI repository with business-specific logic,
    intelligent defaults, and conversation management.
    """

    def __init__(self,
                 api_key: str,
                 organization: Optional[str] = None):
        """
        Initialize ChatGPT business repository.

        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
        """
        # Use business-specific configuration
        config = ChatGPTBusinessConfig()
        super().__init__(api_key, organization, config)

        # Business context
        self.business_context = self._load_business_context()

        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history_size = 10

        # Initialize LLM response parser
        self.response_parser = LLMResponseParser(log_attempts=False) if PARSER_AVAILABLE else None

    def _load_business_context(self) -> Dict[str, Any]:
        """Load business-specific context and rules."""
        return {
            'partners': {
                'glovo': {
                    'name': 'Glovo',
                    'type': 'delivery',
                    'identifier': 'glovo',
                    'commission': 0.30
                },
                'uber': {
                    'name': 'Uber',
                    'type': 'delivery',
                    'identifier': 'uber',
                    'commission': 0.28
                },
                'danone': {
                    'name': 'Danone',
                    'type': 'pharma',
                    'identifier': 'danone',
                    'commission': 0.15
                },
                'hartmann': {
                    'name': 'Hartmann',
                    'type': 'pharma',
                    'identifier': 'hartmann',
                    'commission': 0.18
                },
                'carrefour': {
                    'name': 'Carrefour',
                    'type': 'retail',
                    'identifier': 'carrefour',
                    'commission': 0.25
                }
            },
            'metrics': {
                'gmv': 'Gross Merchandise Value - Valor total de mercancías',
                'aov': 'Average Order Value - Valor promedio de pedido',
                'conversion': 'Tasa de conversión de visitas a compras',
                'shortage': 'Derivaciones entre farmacias por falta de stock',
                'z_y_score': 'Indicador de riesgo de producto (< -0.30 es crítico)'
            },
            'time_ranges': {
                'hoy': 'today',
                'ayer': 'yesterday',
                'esta_semana': 'current_week',
                'semana_pasada': 'last_week',
                'este_mes': 'current_month',
                'mes_pasado': 'last_month'
            },
            'default_values': {
                'limit': 20,
                'time_range': 'last_7_days',
                'sort': 'descending',
                'include_inactive': False
            }
        }

    async def generate_query(self,
                            question: str,
                            database_type: Optional[DatabaseType] = None,
                            context: Optional[Dict[str, Any]] = None) -> QuerySpec:
        """
        Generate a database query with intelligent defaults.

        Enhances the base implementation with business logic and
        automatic completion of missing information.

        Args:
            question: Natural language question (can be incomplete)
            database_type: Optional database type override
            context: Optional additional context

        Returns:
            QuerySpec with generated query
        """
        # Enhance question with business context
        enhanced_question = self._enhance_question(question)

        # Auto-detect database if not specified
        if not database_type:
            database_type = self._detect_database_type(enhanced_question)

        # Merge business context
        full_context = {
            **self.business_context,
            **(context or {})
        }

        # Add conversation history for context
        if self.conversation_history:
            full_context['history'] = self.conversation_history[-3:]  # Last 3 exchanges

        # Generate query with enhanced context
        query_spec = await super().generate_query(
            enhanced_question,
            database_type,
            full_context
        )

        # Post-process for business rules
        query_spec = self._apply_business_rules(query_spec, question)

        # Add to conversation history
        self._update_conversation_history(question, query_spec)

        return query_spec

    async def generate_answer_with_insights(self,
                                           question: str,
                                           results: List[Dict[str, Any]],
                                           query_spec: QuerySpec) -> str:
        """
        Generate answer with business insights.

        Args:
            question: Original question
            results: Query results
            query_spec: The executed query specification

        Returns:
            Natural language answer with insights
        """
        # Analyze results for insights
        insights = self._analyze_results_for_insights(results, query_spec)

        # Build enhanced context
        context = {
            'insights': insights,
            'query_type': query_spec.metadata.get('query_type', 'unknown'),
            'business_context': self.business_context,
            'format': 'business_report'
        }

        # Generate answer with insights
        answer = await self.generate_answer(question, results, context)

        # Add recommendations if applicable
        if insights.get('recommendations'):
            answer += "\n\n**Recomendaciones:**\n"
            for rec in insights['recommendations']:
                answer += f"• {rec}\n"

        return answer

    def _enhance_question(self, question: str) -> str:
        """
        Enhance incomplete questions with context.

        Args:
            question: Original question

        Returns:
            Enhanced question with context
        """
        question_lower = question.lower()
        enhancements = []

        # Check for partner mentions without time range
        has_partner = any(p in question_lower for p in self.business_context['partners'].keys())
        has_time = any(t in question_lower for t in ['hoy', 'ayer', 'semana', 'mes', 'año'])

        if has_partner and not has_time:
            enhancements.append("(últimos 7 días si no se especifica periodo)")

        # Check for metrics without specifics
        if 'gmv' in question_lower and 'partner' not in question_lower:
            if not any(p in question_lower for p in self.business_context['partners'].keys()):
                enhancements.append("(desglosado por partner)")

        # Check for vague requests
        if any(vague in question_lower for vague in ['dame', 'muéstrame', 'dime']):
            if not any(specific in question_lower for specific in ['gmv', 'ventas', 'usuarios', 'farmacias']):
                enhancements.append("(métricas principales)")

        if enhancements:
            return f"{question} {' '.join(enhancements)}"

        return question

    def _detect_database_type(self, question: str) -> DatabaseType:
        """
        Auto-detect appropriate database from question.

        Args:
            question: Question text

        Returns:
            Detected database type
        """
        question_lower = question.lower()

        # MySQL indicators
        mysql_keywords = [
            'ventas', 'vendidos', 'trends', 'tendencia',
            'z_y', 'z-score', 'riesgo', 'predicción',
            'análisis', 'histórico', 'evolución'
        ]

        # MongoDB indicators
        mongodb_keywords = [
            'farmacia', 'usuario', 'booking', 'catálogo',
            'stock', 'actual', 'ahora', 'disponible',
            'partner', 'gmv', 'glovo', 'uber', 'danone'
        ]

        mysql_score = sum(1 for kw in mysql_keywords if kw in question_lower)
        mongodb_score = sum(1 for kw in mongodb_keywords if kw in question_lower)

        # Default to MongoDB for operational queries
        if mysql_score > mongodb_score:
            return DatabaseType.MYSQL
        else:
            return DatabaseType.MONGODB

    def _apply_business_rules(self, query_spec: QuerySpec, original_question: str) -> QuerySpec:
        """
        Apply business-specific rules to query.

        Args:
            query_spec: Generated query specification
            original_question: Original question

        Returns:
            Modified query specification
        """
        question_lower = original_question.lower()

        # Partner GMV rules
        if 'gmv' in question_lower:
            for partner_key, partner_info in self.business_context['partners'].items():
                if partner_key in question_lower:
                    # Ensure creator filter for partner
                    if query_spec.database_type == DatabaseType.MONGODB:
                        if 'filter' in query_spec.parameters:
                            query_spec.parameters['filter']['creator'] = partner_info['identifier']
                        else:
                            query_spec.parameters['filter'] = {'creator': partner_info['identifier']}

        # Shortage/derivation rules
        if any(term in question_lower for term in ['shortage', 'derivación', 'derivaciones']):
            if query_spec.database_type == DatabaseType.MONGODB:
                query_spec.parameters.setdefault('filter', {})['type'] = 'derivation'

        # Apply default limits if not specified
        if 'limit' not in query_spec.options:
            query_spec.options['limit'] = self.business_context['default_values']['limit']

        return query_spec

    def _analyze_results_for_insights(self,
                                      results: List[Dict[str, Any]],
                                      query_spec: QuerySpec) -> Dict[str, Any]:
        """
        Analyze results for business insights with robust error handling.

        Args:
            results: Query results
            query_spec: Query specification

        Returns:
            Dictionary with insights and recommendations
        """
        # Initialize default insights structure
        insights = {
            'summary': {},
            'trends': [],
            'anomalies': [],
            'recommendations': []
        }

        # Guard 1: Check if results is empty or None
        if not results:
            logger.debug("No results to analyze for insights")
            return insights

        # Guard 2: Ensure results is a list
        if not isinstance(results, list):
            logger.warning(f"Results is not a list, got {type(results)}, converting")
            results = [results] if isinstance(results, dict) else []
            if not results:
                return insights

        # Guard 3: Filter out non-dict items
        dict_results = [r for r in results if isinstance(r, dict)]
        if len(dict_results) < len(results):
            logger.warning(f"Filtered out {len(results) - len(dict_results)} non-dict results")

        if not dict_results:
            logger.debug("No valid dict results after filtering")
            return insights

        results = dict_results

        try:
            # Analyze numeric trends with error handling
            numeric_fields = []
            try:
                # Safely detect numeric fields
                if results and len(results) > 0:
                    first_result = results[0]
                    numeric_fields = [
                        k for k in first_result.keys()
                        if isinstance(first_result.get(k), (int, float))
                        and not isinstance(first_result.get(k), bool)  # Exclude booleans
                    ]
            except (AttributeError, TypeError) as e:
                logger.warning(f"Error detecting numeric fields: {e}")

            for field in numeric_fields:
                try:
                    # Safely extract numeric values
                    values = []
                    for r in results:
                        val = r.get(field)
                        if val is not None and isinstance(val, (int, float)):
                            # Check for NaN and Infinity
                            if not (val != val or val == float('inf') or val == float('-inf')):
                                values.append(val)

                    if not values:
                        continue

                    # Calculate statistics safely
                    try:
                        min_val = min(values)
                        max_val = max(values)
                        avg_val = sum(values) / len(values)
                        total_val = sum(values)

                        insights['summary'][field] = {
                            'min': min_val,
                            'max': max_val,
                            'avg': avg_val,
                            'total': total_val
                        }

                        # Detect anomalies (values > 2 std dev from mean)
                        if len(values) > 3:
                            try:
                                variance = sum((x - avg_val) ** 2 for x in values) / len(values)
                                std_dev = variance ** 0.5

                                # Avoid division by zero
                                if std_dev > 0:
                                    for i, val in enumerate(values):
                                        deviation = abs(val - avg_val)
                                        if deviation > 2 * std_dev:
                                            insights['anomalies'].append({
                                                'field': field,
                                                'value': val,
                                                'index': i,
                                                'deviation': deviation / std_dev
                                            })
                            except (ValueError, ZeroDivisionError, OverflowError) as e:
                                logger.warning(f"Error calculating anomalies for {field}: {e}")

                    except (ValueError, TypeError, ZeroDivisionError) as e:
                        logger.warning(f"Error calculating statistics for {field}: {e}")

                except Exception as e:
                    logger.warning(f"Error analyzing field {field}: {e}")
                    continue

            # Generate recommendations based on data
            try:
                query_str = str(query_spec.query).lower() if query_spec and query_spec.query else ""

                if 'gmv' in query_str:
                    try:
                        gmv_total = insights['summary'].get('gmv', {}).get('total', 0)
                        if isinstance(gmv_total, (int, float)) and gmv_total < 10000:
                            insights['recommendations'].append(
                                "El GMV está por debajo del objetivo. Considera promociones o campañas."
                            )
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not generate GMV recommendation: {e}")

                if 'z_y' in query_str:
                    try:
                        critical_products = [
                            r for r in results
                            if isinstance(r.get('z_y_score'), (int, float))
                            and r.get('z_y_score', 0) < -0.30
                        ]
                        if critical_products:
                            insights['recommendations'].append(
                                f"Hay {len(critical_products)} productos en riesgo crítico. "
                                "Requieren atención inmediata."
                            )
                    except (TypeError, AttributeError) as e:
                        logger.debug(f"Could not generate Z_Y recommendation: {e}")

            except Exception as e:
                logger.warning(f"Error generating recommendations: {e}")

        except Exception as e:
            # Catch-all: never let analysis crash the caller
            logger.error(f"Unexpected error in insights analysis: {e}", exc_info=True)

        return insights

    def _update_conversation_history(self, question: str, query_spec: QuerySpec):
        """Update conversation history for context."""
        self.conversation_history.append({
            'role': 'user',
            'content': question,
            'timestamp': datetime.now().isoformat()
        })

        self.conversation_history.append({
            'role': 'assistant',
            'content': f"Generated query for {query_spec.database_type.value}",
            'query': query_spec.query,
            'timestamp': datetime.now().isoformat()
        })

        # Maintain size limit
        if len(self.conversation_history) > self.max_history_size * 2:
            self.conversation_history = self.conversation_history[-self.max_history_size:]

    async def suggest_followup_questions(self,
                                        results: List[Dict[str, Any]],
                                        original_question: str) -> List[str]:
        """
        Suggest follow-up questions based on results.

        Args:
            results: Query results
            original_question: Original question

        Returns:
            List of suggested follow-up questions
        """
        if not results:
            return ["¿Quieres buscar en otro periodo de tiempo?"]

        suggestions = []

        # Analyze what was queried
        if 'gmv' in original_question.lower():
            suggestions.extend([
                "¿Cómo se compara con el mes anterior?",
                "¿Cuáles son los productos más vendidos en este GMV?",
                "¿Qué farmacia tuvo mejor rendimiento?"
            ])

        if any(p in original_question.lower() for p in self.business_context['partners'].keys()):
            suggestions.extend([
                "¿Cómo se compara con otros partners?",
                "¿Cuál es la tendencia mensual?",
                "¿Qué productos prefiere este partner?"
            ])

        return suggestions[:3]  # Return top 3 suggestions

    def __repr__(self) -> str:
        """String representation."""
        return f"ChatGPTLLMRepository(model='{self.config.name}', business_optimized=True)"