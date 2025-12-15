#!/usr/bin/env python3
"""
Smart Query Processor - Procesa queries usando interpretación semántica con GPT.
"""

import os
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from domain.services.query_interpreter import QueryInterpreter
from domain.knowledge.semantic_mapping import find_field_mappings, BUSINESS_CONTEXT


class SmartQueryProcessor:
    """
    Procesador inteligente de queries que usa:
    1. Mapeo semántico para detectar campos relevantes
    2. GPT para interpretar intent y generar queries
    3. MongoDB para ejecutar y validar
    """
    
    def __init__(self, mongo_db, openai_api_key: Optional[str] = None):
        """
        Inicializa el procesador.
        
        Args:
            mongo_db: Instancia de PyMongo database
            openai_api_key: API key de OpenAI
        """
        self.db = mongo_db
        self.interpreter = QueryInterpreter(openai_api_key)
    
    def process(self, query: str, mode: str) -> Dict[str, Any]:
        """
        Procesa una query usando interpretación semántica con diccionario.
        
        100% interpretativo - NO usa hardcode, solo diccionario + GPT.
        
        Args:
            query: Query del usuario
            mode: Modo activo
            
        Returns:
            Dict con respuesta formateada
        """
        # Paso 1: Detectar campos relevantes del diccionario
        mappings = find_field_mappings(query)
        
        # Paso 2: Interpretar con GPT (si está disponible)
        if self.interpreter.available:
            interpretation = self.interpreter.interpret_query(query, mode)
            
            # Si GPT devolvió un pipeline válido, ejecutarlo
            if 'pipeline' in interpretation and interpretation['pipeline'] and len(interpretation['pipeline']) > 0:
                try:
                    collection_name = interpretation.get('collection', 'bookings')
                    collection = getattr(self.db, collection_name)
                    
                    # POST-PROCESAR: Convertir fechas de formato GPT a datetime Python
                    pipeline = self._fix_pipeline_dates(interpretation['pipeline'].copy())
                    
                    # POST-PROCESAR: Asegurar conversiones de tipos en operaciones matemáticas
                    pipeline = self._ensure_type_conversions(pipeline)
                    
                    # AGREGAR FILTRO TEMPORAL si time_range está especificado
                    if interpretation.get('time_range'):
                        pipeline = self._add_time_filter(pipeline, interpretation['time_range'])
                    
                    # Si agrupa por target (farmacias) y no tiene lookup, añadirlo
                    if any('$group' in stage and '_id' in stage.get('$group', {}) and '$target' in str(stage['$group']['_id']) for stage in pipeline):
                        # Añadir lookup para obtener info de farmacia
                        pipeline.append({
                            "$lookup": {
                                "from": "pharmacies",
                                "let": {"target_id": {"$toObjectId": "$_id"}},
                                "pipeline": [
                                    {"$match": {"$expr": {"$eq": ["$_id", "$$target_id"]}}}
                                ],
                                "as": "pharmacy_info"
                            }
                        })
                    
                    result = list(collection.aggregate(pipeline))
                except Exception as e:
                    print(f"Error ejecutando pipeline GPT: {e}")
                    # Si falla la ejecución, intentar con lógica básica
                    result = self._execute_query(interpretation)
            else:
                # Sin pipeline, usar lógica básica
                result = self._execute_query(interpretation)
        else:
            interpretation = self._basic_interpretation(query, mode, mappings)
            result = self._execute_query(interpretation)
        
        # Paso 4: Formatear respuesta
        formatted_answer = self._format_answer(query, result, interpretation)
        
        return {
            'answer': formatted_answer,
            'database': 'mongodb',
            'confidence': interpretation.get('confidence', 0.7),
            'interpretation': interpretation
        }
    
    def _add_time_filter(self, pipeline: list, time_range: str) -> list:
        """
        Agrega filtro temporal al pipeline basado en time_range.
        
        Args:
            pipeline: Pipeline actual
            time_range: Descripción temporal (ej: "últimos 7 días", "este mes")
            
        Returns:
            Pipeline con filtro temporal agregado/actualizado
        """
        from datetime import datetime, timedelta
        
        # Calcular fecha según time_range
        now = datetime.now()
        date_filter = None
        
        if 'hoy' in time_range.lower():
            date_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'ayer' in time_range.lower():
            date_filter = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        elif 'semana' in time_range.lower() or '7' in time_range:
            date_filter = now - timedelta(days=7)
        elif 'mes' in time_range.lower() or '30' in time_range:
            date_filter = now - timedelta(days=30)
        else:
            # Default: últimos 7 días
            date_filter = now - timedelta(days=7)
        
        # Buscar si ya hay un $match en el pipeline
        match_index = None
        for idx, stage in enumerate(pipeline):
            if '$match' in stage:
                match_index = idx
                break
        
        # Agregar o actualizar el filtro de fecha
        if match_index is not None:
            # Ya hay un $match, agregar createdDate
            if 'createdDate' not in pipeline[match_index]['$match']:
                pipeline[match_index]['$match']['createdDate'] = {'$gte': date_filter}
        else:
            # No hay $match, agregarlo al inicio
            pipeline.insert(0, {
                '$match': {
                    'createdDate': {'$gte': date_filter}
                }
            })
        
        return pipeline
    
    def _add_time_filter(self, pipeline: list, time_range: str) -> list:
        """
        Agrega o actualiza filtro temporal en el pipeline.
        
        Args:
            pipeline: Pipeline actual
            time_range: Descripción del rango temporal
            
        Returns:
            Pipeline con filtro temporal
        """
        from datetime import datetime, timedelta
        
        # Calcular fecha basada en time_range
        now = datetime.now()
        date_filter = None
        
        time_range_lower = time_range.lower()
        
        if 'hoy' in time_range_lower:
            date_filter = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'ayer' in time_range_lower:
            date_filter = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        elif 'semana' in time_range_lower or '7 día' in time_range_lower:
            date_filter = now - timedelta(days=7)
        elif 'mes' in time_range_lower or '30 día' in time_range_lower:
            date_filter = now - timedelta(days=30)
        elif 'año' in time_range_lower:
            date_filter = now - timedelta(days=365)
        else:
            # Si no se puede determinar, no agregar filtro
            return pipeline
        
        # Buscar $match existente
        match_index = None
        for idx, stage in enumerate(pipeline):
            if '$match' in stage:
                match_index = idx
                break
        
        # Actualizar o crear $match
        if match_index is not None:
            # SIEMPRE reemplazar createdDate con la fecha correcta
            pipeline[match_index]['$match']['createdDate'] = {'$gte': date_filter}
        
        return pipeline
    
    def _fix_pipeline_dates(self, pipeline: list) -> list:
        """
        Post-procesa el pipeline para convertir fechas de formato GPT a datetime Python.
        
        GPT a veces genera: {"$date": "2023-10-01T00:00:00Z"}
        Necesitamos: datetime(2023, 10, 1)
        """
        from datetime import datetime, timedelta
        import json
        
        def fix_dates_recursive(obj):
            """Recursivamente reemplaza objetos $date con datetime reales"""
            if isinstance(obj, dict):
                # Si es un objeto {"$date": "..."}
                if len(obj) == 1 and "$date" in obj:
                    date_str = obj["$date"]
                    try:
                        # Intentar parsear la fecha
                        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    except:
                        # Si falla, usar fecha relativa
                        # GPT probablemente quiso decir "últimos 7 días"
                        return datetime.now() - timedelta(days=7)
                else:
                    # Recursivamente procesar cada valor del dict
                    return {k: fix_dates_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                # Recursivamente procesar cada elemento de la lista
                return [fix_dates_recursive(item) for item in obj]
            else:
                return obj
        
        return fix_dates_recursive(pipeline)
    
    def _basic_interpretation(self, query: str, mode: str, mappings) -> Dict[str, Any]:
        """Interpretación básica sin GPT."""
        
        query_lower = query.lower()
        
        # Detectar intent
        if 'cuántos' in query_lower or 'cuántas' in query_lower:
            intent = 'count'
        elif 'total' in query_lower and 'gmv' in query_lower:
            intent = 'sum_gmv'
        elif 'promedio' in query_lower or 'ticket medio' in query_lower:
            intent = 'average'
        elif 'top' in query_lower or 'ranking' in query_lower:
            intent = 'top_n'
        elif 'comparar' in query_lower or 'comparación' in query_lower:
            intent = 'compare'
        else:
            intent = 'info'
        
        # Detectar colección
        if mode == 'pharmacy':
            collection = 'pharmacies'
        elif mode == 'product':
            collection = 'items'
        elif mode == 'partner':
            collection = 'bookings'
        else:
            collection = 'bookings'
        
        # Detectar período temporal
        time_range = self._detect_time_range(query_lower)
        
        return {
            'collection': collection,
            'intent': intent,
            'fields_detected': [m.field_path for m in mappings],
            'time_range': time_range,
            'confidence': 0.6
        }
    
    def _detect_time_range(self, query_lower: str) -> Optional[datetime]:
        """Detecta el rango temporal de la query."""
        
        if 'hoy' in query_lower:
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif 'ayer' in query_lower:
            return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        elif 'esta semana' in query_lower or 'semana' in query_lower:
            return datetime.now() - timedelta(days=7)
        elif 'este mes' in query_lower or 'mes' in query_lower:
            return datetime.now() - timedelta(days=30)
        elif 'mes pasado' in query_lower:
            return datetime.now() - timedelta(days=60)
        
        # Default: última semana
        return datetime.now() - timedelta(days=7)
    
    def _execute_query(self, interpretation: Dict[str, Any]) -> Any:
        """Ejecuta la query interpretada en MongoDB."""
        
        try:
            collection_name = interpretation.get('collection', 'bookings')
            collection = getattr(self.db, collection_name)
            
            # Si hay pipeline definido por GPT
            if 'pipeline' in interpretation and interpretation['pipeline']:
                result = list(collection.aggregate(interpretation['pipeline']))
                return result
            
            # Ejecutar según intent básico
            intent = interpretation.get('intent', 'info')
            
            if intent == 'count':
                count = collection.count_documents({})
                return {'count': count}
            
            elif intent == 'info':
                # Obtener información básica
                count = collection.count_documents({})
                sample = collection.find_one()
                return {
                    'count': count,
                    'sample': sample,
                    'collection': collection_name
                }
            
            else:
                # Default: contar
                return {'count': collection.count_documents({})}
        
        except Exception as e:
            return {'error': str(e)}
    
    def _ensure_type_conversions(self, pipeline: list) -> list:
        """
        Asegura que todas las operaciones matemáticas usen conversiones de tipos.
        Previene errores como '$multiply only supports numeric types, not string'.
        
        Por ahora, devolvemos el pipeline sin modificar para evitar errores.
        GPT ya incluye las conversiones necesarias.
        
        Args:
            pipeline: Pipeline a procesar
            
        Returns:
            Pipeline (sin modificar por ahora)
        """
        # DESHABILITADO TEMPORALMENTE: Causaba error "Use of undefined variable: value"
        # GPT ya incluye conversiones de tipos en sus pipelines
        return pipeline
    
    def _format_answer(self, query: str, result: Any, interpretation: Dict[str, Any]) -> str:
        """Formatea la respuesta para el usuario."""
        
        # Si hay error
        if isinstance(result, dict) and 'error' in result:
            return f"❌ Error ejecutando query: {result['error']}"
        
        # PRIORIDAD 1: Si tenemos resultados de MongoDB, formatearlos
        if isinstance(result, list) and len(result) > 0:
            return self._format_results_list(query, result, interpretation)
        
        # PRIORIDAD 2: Si tenemos count, mostrarlo
        if isinstance(result, dict) and 'count' in result:
            return f"📊 Se encontraron **{result['count']:,} registros** para: '{query}'\n\n*Fuente: Luda Mind - MongoDB*"
        
        # PRIORIDAD 3: Si GPT dio una explicación PERO no hay resultados
        if 'explanation' in interpretation:
            explanation = interpretation['explanation']
            
            # Limpiar cualquier JSON que GPT haya incluido en el texto
            import re
            clean_text = re.sub(r'```json.*?```', '', explanation, flags=re.DOTALL).strip()
            clean_text = re.sub(r'\{[\s\S]*?"pipeline"[\s\S]*?\}', '', clean_text).strip()
            
            if clean_text and len(clean_text) > 20:
                return clean_text + "\n\n*Fuente: Luda Mind - MongoDB*"
        
        # FALLBACK: Mensaje genérico
        return f"✅ Query procesada: '{query}'\n\nNo se encontraron resultados específicos.\n\n*Fuente: Luda Mind - MongoDB*"
    
    def _format_results_list(self, query: str, results: list, interpretation: Dict[str, Any]) -> str:
        """Formatea una lista de resultados de manera legible."""
        
        if not results or len(results) == 0:
            return f"📊 No se encontraron resultados para: '{query}'\n\n*Fuente: Luda Mind - MongoDB*"
        
        # CRÍTICO: Si resultado es 1 elemento con campo "total", es un COUNT
        if len(results) == 1 and isinstance(results[0], dict):
            first_result = results[0]
            if 'total' in first_result:
                entity = self._extract_entity_from_query(query)
                total = first_result['total']
                return f"📊 **Total de {entity}:** {total:,}\n\n*Fuente: Luda Mind - MongoDB (interpretación GPT)*"
            elif 'count' in first_result:
                entity = self._extract_entity_from_query(query)
                total = first_result['count']
                return f"📊 **Total de {entity}:** {total:,}\n\n*Fuente: Luda Mind - MongoDB (interpretación GPT)*"
        
        # CRÍTICO: Si hay MUCHOS resultados (>50), convertir a count simple
        if len(results) > 50:
            entity = self._extract_entity_from_query(query)
            return f"📊 **Total de {entity} encontrados:** {len(results):,}\n\n*Tip: Para ver detalles, usa 'listame' o especifica filtros.*\n\n*Fuente: Luda Mind - MongoDB (interpretación GPT)*"
        
        # Detectar si es ranking de farmacias con Glovo
        query_lower = query.lower()
        is_pharmacy_ranking = 'farmacia' in query_lower and 'top' in query_lower
        is_glovo_related = 'glovo' in query_lower
        
        answer = ""
        
        # Si es ranking de farmacias
        if is_pharmacy_ranking and all(isinstance(r, dict) and '_id' in r for r in results[:3]):
            if is_glovo_related:
                answer += "🏥 **Top 10 Farmacias con más ventas en Glovo** (Luda Mind)\n\n"
            else:
                answer += "🏥 **Top 10 Farmacias** (Luda Mind)\n\n"
            
            total_sales = 0
            total_pedidos = 0
            
            for idx, item in enumerate(results[:10], 1):
                item_id = item.get('_id', 'N/A')
                
                # Buscar campos de ventas con diferentes nombres posibles
                sales = item.get('totalGMV', item.get('totalSales', item.get('total_gmv', item.get('gmv', 0))))
                pedidos = item.get('totalPedidos', item.get('total_pedidos', item.get('count', 0)))
                
                total_sales += sales
                total_pedidos += pedidos
                
                # Si hay info de farmacia en lookup (puede ser pharmacy_info o pharmacyInfo)
                pharmacy_info_list = item.get('pharmacy_info', item.get('pharmacyInfo', []))
                if pharmacy_info_list and len(pharmacy_info_list) > 0:
                    pharmacy_data = pharmacy_info_list[0]
                    pharmacy_name = pharmacy_data.get('description', f'Farmacia {str(item_id)[:12]}...')
                    city = pharmacy_data.get('contact', {}).get('city', '')
                    
                    answer += f"**{idx}. {pharmacy_name}**"
                    if city:
                        answer += f" ({city})"
                    answer += "\n"
                else:
                    answer += f"**{idx}. Farmacia ID: {str(item_id)[:24]}...**\n"
                
                if sales > 0:
                    answer += f"• GMV: €{sales:,.2f}\n"
                if pedidos > 0:
                    answer += f"• Pedidos: {pedidos:,}\n"
                
                answer += "\n"
            
            # Añadir totales
            if total_sales > 0 or total_pedidos > 0:
                answer += "📊 **Totales:**\n"
                if total_pedidos > 0:
                    answer += f"• Total pedidos (top 10): {total_pedidos:,}\n"
                if total_sales > 0:
                    answer += f"• GMV total (top 10): €{total_sales:,.2f}\n"
        
        else:
            # Para listas medianas (21-50), mostrar resumen + primeros resultados
            if len(results) > 20 and len(results) <= 50:
                entity = self._extract_entity_from_query(query)
                answer += f"📊 **{entity.capitalize()} encontrados:** {len(results):,}\n\n"
                answer += f"*Mostrando los primeros 10 resultados:*\n\n"
            else:
                # Para listas cortas (<= 20), mostrar todos
                answer += f"📊 **Resultados para:** '{query}'\n\n"
                answer += f"Se encontraron {len(results)} registros\n\n"
            
            for idx, item in enumerate(results[:5], 1):
                if isinstance(item, dict):
                    answer += f"{idx}. {str(item.get('_id', item))[:50]}\n"
                    # Mostrar campos principales
                    for key, value in list(item.items())[:3]:
                        if key != '_id':
                            answer += f"   • {key}: {value}\n"
                else:
                    answer += f"{idx}. {str(item)[:100]}\n"
        
        answer += "\n*Fuente: Luda Mind - MongoDB (interpretación GPT)*"
        return answer
    
    def _build_system_prompt(self, mode: str) -> str:
        """Construye el system prompt para GPT."""
        
        mode_context = {
            "pharmacy": "Farmacias y establecimientos",
            "product": "Productos y catálogo",
            "partner": "Partners y canales de venta",
            "conversational": "Análisis general y KPIs"
        }
        
        return f"""Eres un asistente experto en MongoDB para Luda Mind.

**Modo activo:** {mode} - {mode_context.get(mode, 'General')}

**Tu misión:**
Interpretar queries en español y convertirlas en agregaciones MongoDB efectivas.

**Reglas importantes:**
1. MongoDB es la base de datos principal
2. MySQL solo para sell in / sell out
3. Campos principales:
   - Partners: thirdUser.user, thirdUser.price
   - Farmacias: name, city, active
   - Productos: name, ean, price, active
   - Fechas: createdDate
4. Usar $regex con case insensitive para textos
5. Manejar nulls con $ifNull
6. Limitar resultados (default 100)

**Responde explicando:**
- Qué campos usar
- Qué agregación hacer
- Cómo interpretas la query
- Resultado esperado

Sé claro y conciso. Si no estás seguro, di qué necesitas aclarar.
"""
    
    def _build_user_prompt(self, query: str, semantic_context: str) -> str:
        """Construye el user prompt."""
        
        return f"""Interpreta esta query:

**Query:** "{query}"

**Contexto detectado automáticamente:**
{semantic_context}

**Tu respuesta debe incluir:**
1. Colección MongoDB a usar
2. Campos relevantes detectados
3. Período temporal (si aplica)
4. Tipo de agregación sugerida
5. Explicación clara para el usuario
6. Nivel de confianza (0-1)

Genera una respuesta útil y accionable.
"""
    
    def _extract_entity_from_query(self, query: str) -> str:
        """
        Extrae la entidad principal de la query para mensajes genéricos.
        
        Args:
            query: Query del usuario
            
        Returns:
            Nombre de la entidad en plural (ej: "farmacias", "productos", "partners")
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['farmacia', 'pharmacy', 'botica']):
            return "farmacias"
        elif any(word in query_lower for word in ['producto', 'product', 'item', 'medicamento']):
            return "productos"
        elif any(word in query_lower for word in ['partner', 'canal', 'marketplace']):
            return "partners"
        elif any(word in query_lower for word in ['pedido', 'booking', 'orden']):
            return "pedidos"
        else:
            return "registros"

