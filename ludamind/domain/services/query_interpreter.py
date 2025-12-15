#!/usr/bin/env python3
"""
Query Interpreter - Usa GPT con mapeo semántico para interpretar queries.
Convierte lenguaje natural en queries MongoDB optimizadas.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.knowledge.semantic_mapping import (
    find_field_mappings,
    suggest_aggregation_pattern,
    build_context_for_llm,
    get_context_for_mode,
    BUSINESS_CONTEXT
)

# Importar nuevos módulos de validación (con fallback seguro)
try:
    from domain.services.response_validator import get_validator
    from domain.services.output_type_detector import get_detector
    VALIDATION_AVAILABLE = True
except ImportError:
    VALIDATION_AVAILABLE = False
    print("Warning: Validation modules not available, using fallback mode")


class QueryInterpreter:
    """
    Interpreta queries en lenguaje natural y las convierte en queries MongoDB.
    Usa GPT con contexto semántico enriquecido.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Inicializa el intérprete.
        
        Args:
            openai_api_key: API key de OpenAI (opcional, lee de env si no se proporciona)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Inicializar validadores (con fallback seguro)
        if VALIDATION_AVAILABLE:
            try:
                self.validator = get_validator()
                self.output_detector = get_detector()
                self.validation_enabled = True
            except Exception as e:
                print(f"Warning: Could not initialize validators: {e}")
                self.validation_enabled = False
        else:
            self.validation_enabled = False
        
        # Importar OpenAI si está disponible
        try:
            import openai
            self.openai = openai
            if self.api_key:
                self.openai.api_key = self.api_key
                self.available = True
            else:
                self.available = False
        except ImportError:
            self.available = False
    
    def interpret_query(self, query: str, mode: str = "conversational") -> Dict[str, Any]:
        """
        Interpreta una query usando GPT con contexto semántico.
        
        Args:
            query: Query del usuario en lenguaje natural
            mode: Modo activo (pharmacy, product, partner, conversational)
            
        Returns:
            Dict con interpretación estructurada:
            {
                "collection": str,
                "pipeline": list,
                "explanation": str,
                "confidence": float
            }
        """
        # NUEVO: Detectar tipo de output esperado (si validación disponible)
        output_type = 'aggregation'  # Default seguro
        if self.validation_enabled:
            try:
                output_type = self.output_detector.detect(query)
            except Exception as e:
                print(f"Warning: Output detection failed: {e}")
                output_type = 'aggregation'
        
        # Construir contexto semántico
        semantic_context = build_context_for_llm(query)
        
        # Construir prompt para GPT (ahora con hint de output type)
        system_prompt = self._build_system_prompt(mode, output_type)
        user_prompt = self._build_user_prompt(query, semantic_context)
        
        if not self.available:
            # Fallback sin GPT
            return self._fallback_interpretation(query, mode)
        
        try:
            # Llamar a GPT (sintaxis OpenAI v1.0+)
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Baja temperatura para respuestas más deterministas
                max_tokens=1000
            )
            
            # Parsear respuesta
            result = response.choices[0].message.content
            
            # Intentar parsear JSON si GPT lo devuelve
            interpretation = None
            
            # LIMPIEZA: Eliminar comentarios JavaScript que GPT a veces incluye
            import re
            def clean_json_response(text):
                """Limpia JSON de GPT eliminando comentarios y arreglando formato"""
                # Eliminar comentarios de una línea //
                text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)
                # Eliminar comentarios de bloque /* */
                text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
                # Eliminar espacios extra antes de comas/corchetes/llaves
                text = re.sub(r'\s+,', ',', text)
                text = re.sub(r'\s+}', '}', text)
                text = re.sub(r'\s+]', ']', text)
                return text
            
            cleaned_result = clean_json_response(result)
            
            try:
                # Primero intentar JSON directo con resultado limpio
                interpretation = json.loads(cleaned_result)
                
                # Verificar estructura y extraer pipeline si está anidado
                if interpretation and 'explanation' in interpretation:
                    # A veces GPT mete el pipeline dentro de explanation como JSON string
                    if isinstance(interpretation['explanation'], str) and '{' in interpretation['explanation']:
                        try:
                            # Intentar extraer JSON anidado
                            import re
                            nested_json = re.search(r'\{[^}]*"pipeline"[^}]*\}', interpretation['explanation'], re.DOTALL)
                            if nested_json:
                                nested = json.loads(nested_json.group())
                                if 'pipeline' in nested and nested['pipeline']:
                                    interpretation['pipeline'] = nested['pipeline']
                                    interpretation['collection'] = nested.get('collection', 'bookings')
                        except:
                            pass
                            
            except json.JSONDecodeError:
                # Si falla el parse directo, buscar JSON en diferentes formatos
                import re
                
                # Buscar JSON en markdown
                json_match = re.search(r'```json\s*(\{.*?\})\s*```', result, re.DOTALL)
                if json_match:
                    try:
                        interpretation = json.loads(json_match.group(1))
                    except:
                        pass
                
                # Buscar objeto JSON simple
                if not interpretation:
                    json_match = re.search(r'(\{[^{}]*"collection"[^{}]*\})', result, re.DOTALL)
                    if json_match:
                        try:
                            interpretation = json.loads(json_match.group(1))
                        except:
                            pass
            
            # Si no se pudo parsear o falta pipeline, usar fallback
            if not interpretation or not interpretation.get('pipeline'):
                interpretation = {
                    "collection": self._detect_collection(query, mode),
                    "pipeline": [],
                    "explanation": result[:500] if isinstance(result, str) else str(result)[:500],
                    "confidence": 0.5
                }
            
            # NUEVO: Validar y corregir respuesta (si validación disponible)
            if self.validation_enabled:
                try:
                    interpretation = self.validator.validate_and_fix(interpretation, query, mode)
                except Exception as e:
                    # Si falla validación, usar resultado sin validar (fallback seguro)
                    print(f"Warning: Validation failed: {e}, using unvalidated response")
            
            return interpretation
        
        except Exception as e:
            print(f"Error calling GPT: {e}")
            return self._fallback_interpretation(query, mode)
    
    def _build_system_prompt(self, mode: str, output_type: str = 'aggregation') -> str:
        """
        Construye el system prompt para GPT.
        
        Args:
            mode: Modo activo
            output_type: Tipo de output esperado ('list' o 'aggregation')
        """
        
        # NUEVO: Obtener hint de output type (si validación disponible)
        output_hint = ""
        if self.validation_enabled:
            try:
                output_hint = self.output_detector.get_hint_for_gpt(output_type)
            except Exception:
                output_hint = ""
        
        return f"""Eres un asistente experto en MongoDB para Luda Mind, un sistema farmacéutico.
{output_hint}

Tu tarea es interpretar queries en lenguaje natural en español y convertirlas en agregaciones MongoDB.

**Modo activo:** {mode}

**Bases de datos disponibles:**
- MongoDB: Operaciones, farmacias, pedidos, productos, partners (USAR PRINCIPALMENTE)
- MySQL: Solo para sell in / sell out (NO usar para queries normales)

**Contexto de Negocio:**
{get_context_for_mode(mode)}

**REGLAS ESPECIALES PARA FARMACIAS EN PARTNERS:**

Para determinar si una farmacia está "activa en [partner]":

PARTNERS CON TAGS (usar campo pharmacies.tags):
- Glovo: {{tags: "GLOVO"}} o {{tags: {{$in: ["GLOVO"]}}}}
- Glovo-OTC: {{tags: {{$in: ["GLOVO-OTC_2H", "GLOVO-OTC_48H"]}}}}
- Amazon: {{tags: {{$in: ["AMAZON_2H", "AMAZON_48H"]}}}}
- Carrefour: {{tags: {{$in: ["CARREFOUR_2H", "CARREFOUR_48H"]}}}}
- Danone: {{tags: {{$in: ["DANONE_2H", "DANONE_48H"]}}}}
- Procter: {{tags: {{$in: ["PROCTER_2H", "PROCTER_48H"]}}}}
- Enna: {{tags: {{$in: ["ENNA_2H", "ENNA_48H"]}}}}
- Nordic: {{tags: {{$in: ["NORDIC_2H", "NORDIC_48H"]}}}}
- Chiesi: {{tags: {{$in: ["CHIESI_48H", "CHIESI_BACKUP"]}}}}
- Ferrer: {{tags: {{$in: ["FERRER_2H", "FERRER_48H"]}}}}

Si especifica tiempo de respuesta:
- "2h" o "2 horas" → solo _2H
- "48h" → solo _48H
- Sin especificar → incluir ambos

PARTNERS SIN TAGS (Uber, Justeat):
- NO usar tags (no existen en pharmacies.tags)
- CRITERIO: Farmacia con pedidos del partner en el período de la consulta
- Query en bookings: agrupar farmacias únicas con pedidos
- Filtrar por createdDate según período mencionado (esta semana, este mes, etc.)
- Si NO especifica período → asumir últimos 7 días
- Ejemplo: db.bookings.aggregate([
    {{$match: {{thirdUser.user: "uber", createdDate: {{$gte: fecha_segun_periodo}}}}}},
    {{$group: {{_id: "$target"}}}},
    {{$count: "total"}}
  ])

IGNORAR:
- NUTRIBEN (no es partner activo)

**FILTROS GEOGRÁFICOS (ciudad, provincia):**
- SIEMPRE usar {{$regex: "nombre", $options: "i"}} para filtros de ciudad o provincia
- NO usar coincidencia exacta (evita problemas con acentos y mayúsculas/minúsculas)
- Ejemplos:
  * "provincia de castellon" → {{"contact.province": {{$regex: "castellon", $options: "i"}}}}
  * "ciudad de madrid" → {{"contact.city": {{$regex: "madrid", $options: "i"}}}}
  * "en barcelona" → {{"contact.city": {{$regex: "barcelona", $options: "i"}}}}

**FILTRADO AUTOMÁTICO POR ESTADO ACTIVO:**
- **FARMAC IAS**: SIEMPRE filtrar por {{active: 1}} salvo que se pida explícitamente "inactivas" o "todas"
  * Añadir {{$match: {{active: 1}}}} al inicio del pipeline
  * Ejemplo: "farmacias por provincia" → filtrar active: 1
- **PRODUCTOS**: SIEMPRE filtrar por {{active: 1}} salvo que se pida explícitamente "inactivos"
  * Añadir {{$match: {{active: 1}}}} al inicio del pipeline

**ORDENAMIENTO DE RESULTADOS:**
- Para queries de **conteo/agregación** (cuántas, distribución, ranking):
  * SIEMPRE añadir {{$sort}} al final del pipeline
  * Ordenar descendente por el campo calculado (count, total, sum)
  * Ejemplo: {{$sort: {{count: -1}}}} o {{$sort: {{total: -1}}}}
- Para queries de **listado** (listar, mostrar, cuáles):
  * Ordenar por nombre o campo relevante

**Instrucciones:**
1. Identifica los campos de MongoDB necesarios
2. SI pregunta por farmacias/productos → FILTRAR por active: 1 automáticamente
3. SI pregunta por farmacias en partner → USA TAGS si el partner los tiene
4. Detecta el período temporal si se menciona
5. Para filtros geográficos (ciudad/provincia) → USA REGEX case-insensitive
6. Para agregaciones → AÑADIR $sort descendente al final
7. Sugiere la agregación MongoDB óptima
8. Explica tu razonamiento brevemente

**IMPORTANTE: Responde SOLO con JSON puro (sin markdown, SIN comentarios):**
{{
    "collection": "nombre_coleccion",
    "fields_detected": ["campo1", "campo2"],
    "time_range": "últimos 7 días" o null,
    "aggregation_type": "count|sum|avg|group",
    "pipeline": [...],
    "explanation": "Explicación breve en español para el usuario",
    "confidence": 0.0-1.0
}}

CRÍTICO:
- NO uses bloques ```json```
- NO uses comentarios // o /* */ dentro del JSON
- Para filtros de fecha: NO incluyas filtro de createdDate en el pipeline
  * Si menciona "esta semana", "este mes", etc. → indica SOLO en el campo time_range
  * NO generes $match con createdDate en el pipeline
  * NO uses $dateSubtract, $date, $$NOW u otros operadores de fecha
  * El sistema agregará el filtro temporal real basándose en time_range
  * Ejemplo: time_range: "últimos 7 días" (sin filtro en pipeline)
- Para top/ranking por partner: incluye $match SOLO con thirdUser.user
- Solo devuelve el objeto JSON válido
"""
    
    def _build_user_prompt(self, query: str, semantic_context: str) -> str:
        """Construye el user prompt con contexto semántico."""
        
        # Detectar menciones específicas de partners
        query_lower = query.lower()
        partner_mentioned = None
        partners = ['glovo', 'uber', 'danone', 'carrefour', 'justeat', 'amazon', 
                   'procter', 'enna', 'nordic', 'chiesi', 'ferrer', 'glovo-otc']
        
        for partner in partners:
            if partner in query_lower:
                partner_mentioned = partner
                break
        
        prompt = f"""Query del usuario: "{query}"

{semantic_context}"""
        
        # Si menciona un partner específico, dar instrucción clara
        if partner_mentioned:
            prompt += f"""

IMPORTANTE: La query menciona "{partner_mentioned}". 
Debes incluir un $match inicial para filtrar por thirdUser.user = "{partner_mentioned}"."""
        
        # Si pide un ranking/top, dar formato específico
        if any(word in query_lower for word in ['top', 'ranking', 'mejores', 'más']):
            prompt += """

Para rankings/top, incluye SIEMPRE:
1. $match para filtrar por partner y fecha (si aplica)
2. $group para agregar por la entidad principal:
   - Si agrupa por farmacias: _id = "$target"
   - SIEMPRE incluir:
     * totalGMV: SIEMPRE calcular desde items usando $reduce:
       {{
         "$reduce": {{
           "input": "$items",
           "initialValue": 0,
           "in": {{
             "$add": [
               "$$value",
               {{
                 "$multiply": [
                   {{"$toDouble": {{"$ifNull": ["$$this.pvp", 0]}}}},
                   {{"$toInt": {{"$ifNull": ["$$this.quantity", 0]}}}}
                 ]
               }}
             ]
           }}
         }}
       }}
     * totalPedidos: {{$sum: 1}}
3. $sort descendente por la métrica principal
4. $limit para el número solicitado (10 por defecto)
5. $lookup para obtener info de farmacias/productos con "as": "pharmacy_info"

CRÍTICO GMV:
- NUNCA uses thirdUser.price directamente
- SIEMPRE calcula desde items[].pvp * items[].quantity
- Usa $reduce para iteración robusta (como arriba)
- O usa $sum con $map: {{"$sum": {{"$map": {{"input": "$items", "as": "item", "in": {{"$multiply": ["$$item.pvp", "$$item.quantity"]}}}}}}}}
"""
        
        prompt += """

Genera la agregación MongoDB correspondiente."""
        
        return prompt
    
    def _fallback_interpretation(self, query: str, mode: str) -> Dict[str, Any]:
        """Interpretación básica sin GPT."""
        
        query_lower = query.lower()
        
        # Detección simple de colección
        collection = self._detect_collection(query, mode)
        
        # Detección simple de intent
        if any(word in query_lower for word in ['cuántos', 'cuántas', 'número', 'total de']):
            intent = "count"
        elif any(word in query_lower for word in ['suma', 'total', 'sumar']):
            intent = "sum"
        elif any(word in query_lower for word in ['promedio', 'media', 'ticket medio']):
            intent = "average"
        elif any(word in query_lower for word in ['top', 'mejores', 'ranking']):
            intent = "top_n"
        else:
            intent = "search"
        
        return {
            "collection": collection,
            "intent": intent,
            "explanation": f"Interpretación básica: {intent} en {collection}",
            "confidence": 0.5
        }
    
    def _detect_collection(self, query: str, mode: str) -> str:
        """Detecta la colección MongoDB apropiada."""
        
        query_lower = query.lower()
        
        # Por modo
        if mode == "pharmacy":
            return "pharmacies"
        elif mode == "product":
            return "items"
        elif mode == "partner":
            return "bookings"
        
        # Por keywords
        if any(word in query_lower for word in ['farmacia', 'botica', 'establecimiento']):
            return "pharmacies"
        
        if any(word in query_lower for word in ['producto', 'medicamento', 'item', 'ean']):
            return "items"
        
        if any(word in query_lower for word in ['pedido', 'booking', 'reserva', 'gmv', 'partner']):
            return "bookings"
        
        if any(word in query_lower for word in ['stock', 'inventario']):
            return "stockItems"
        
        return "bookings"  # Default


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Test del sistema
    interpreter = QueryInterpreter()
    
    test_queries = [
        ("GMV de Glovo esta semana", "partner"),
        ("Farmacias activas en Madrid", "pharmacy"),
        ("Cuántos productos hay en el catálogo", "product"),
        ("Pedidos de hoy por partner", "partner")
    ]
    
    print("\n" + "="*70)
    print("  🧪 TEST DEL QUERY INTERPRETER")
    print("="*70)
    
    for query, mode in test_queries:
        print(f"\n📝 Query: '{query}'")
        print(f"   Modo: {mode}")
        
        # Buscar mappings
        mappings = find_field_mappings(query)
        print(f"   Campos detectados: {[m.field_path for m in mappings]}")
        
        # Sugerir pattern
        pattern = suggest_aggregation_pattern(query)
        if pattern:
            print(f"   Pattern sugerido: {pattern['pattern_name']}")
        
        # Interpretar con GPT (si disponible)
        if interpreter.available:
            result = interpreter.interpret_query(query, mode)
            print(f"   Interpretación: {result.get('explanation', 'N/A')[:100]}")
        
        print()

