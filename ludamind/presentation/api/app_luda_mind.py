#!/usr/bin/env python3
"""
Luda Mind - Sistema Inteligente de Consultas
Versión con branding actualizado y color verde corporativo.
MODO HÍBRIDO: Queries predefinidas (rápidas) + Interpretación semántica (flexibles)
Siguiendo Clean Architecture y principios SOLID.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import os
import sys
import re
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()

# Import sistema semántico
try:
    from domain.services.smart_query_processor import SmartQueryProcessor
    SEMANTIC_SYSTEM_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Sistema semántico no disponible: {e}")
    SEMANTIC_SYSTEM_AVAILABLE = False

# Import security validators
try:
    from infrastructure.security import MongoQuerySecurityValidator
    SECURITY_VALIDATORS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Validadores de seguridad no disponibles: {e}")
    SECURITY_VALIDATORS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FLASK APPLICATION SETUP
# ============================================================================

app = Flask(
    __name__,
    template_folder='../web/templates',
    static_folder='../web/static'
)

# Security configuration
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'luda-mind-secret-key-change-in-production')

# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

# In-memory session storage (consider Redis for production)
sessions = {}

# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

mysql_connected = False
mongodb_connected = False
mysql_conn = None
mongo_db = None
smart_processor = None  # Sistema semántico inteligente
mongo_validator = None  # Validador de seguridad MongoDB

# Try MySQL connection
try:
    import mysql.connector
    mysql_conn = mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', '3307')),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASS'),
        database=os.getenv('MYSQL_DB'),
        connect_timeout=5
    )
    mysql_connected = True
    logger.info("✅ MySQL connected successfully for Luda Mind")
except Exception as e:
    logger.warning(f"⚠️ MySQL connection failed: {str(e)[:100]}")

# Try MongoDB connection
try:
    from pymongo import MongoClient
    import re
    mongo_uri = os.getenv('MONGO_LUDAFARMA_URL')
    if mongo_uri:
        mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Extract database name from URI (never hardcode!)
        db_match = re.search(r'/([^/?]+)(\?|$)', mongo_uri)
        db_name = db_match.group(1) if db_match else None
        if not db_name:
            raise ValueError("No database name found in MongoDB URI")
        mongo_db = mongo_client[db_name]
        # Test connection
        mongo_db.list_collection_names()
        mongodb_connected = True
        logger.info(f"✅ MongoDB connected successfully for Luda Mind (DB: {db_name})")
        
        # Inicializar Smart Query Processor (sistema semántico)
        if SEMANTIC_SYSTEM_AVAILABLE:
            try:
                smart_processor = SmartQueryProcessor(
                    mongo_db=mongo_db,
                    openai_api_key=os.getenv('OPENAI_API_KEY')
                )
                logger.info("✅ Sistema semántico inicializado")
            except Exception as sem_err:
                logger.warning(f"⚠️ Sistema semántico no disponible: {sem_err}")

        # Inicializar validador de seguridad MongoDB
        if SECURITY_VALIDATORS_AVAILABLE:
            try:
                mongo_validator = MongoQuerySecurityValidator()
                logger.info("✅ Validador de seguridad MongoDB inicializado")
            except Exception as sec_err:
                logger.warning(f"⚠️ Validador de seguridad no disponible: {sec_err}")

except Exception as e:
    logger.warning(f"⚠️ MongoDB connection failed: {str(e)[:100]}")

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main interface with Luda Mind branding v2 - improved UX."""
    return render_template('index_luda_mind_v2.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files including logo."""
    return send_from_directory('../web/static', filename)

# ============================================================================
# HELPER FUNCTIONS - SECURITY & VALIDATION
# ============================================================================

def validate_mongodb_pipeline(pipeline: list, collection: str) -> tuple:
    """
    Valida un pipeline de MongoDB antes de ejecutarlo.

    Args:
        pipeline: Pipeline de agregación MongoDB
        collection: Nombre de la colección

    Returns:
        (is_safe: bool, error_message: str)
    """
    if not mongo_validator:
        # Validador no disponible, permitir por defecto (modo degradado)
        return (True, None)

    try:
        result = mongo_validator.validate_pipeline(pipeline, collection)

        if not result.is_safe:
            error_msg = f"Pipeline bloqueado por seguridad: {', '.join(result.blocked_reasons)}"
            logger.warning(f"[SECURITY] {error_msg}")
            return (False, error_msg)

        if result.warnings:
            logger.info(f"[SECURITY] Pipeline warnings: {', '.join(result.warnings)}")

        return (True, None)

    except Exception as e:
        logger.error(f"[SECURITY] Error validando pipeline: {e}")
        # En caso de error del validador, denegar por seguridad
        return (False, f"Error de validación de seguridad: {str(e)}")


def validate_mongodb_query(query: dict, collection: str) -> tuple:
    """
    Valida una query de MongoDB antes de ejecutarla.

    Args:
        query: Query de MongoDB
        collection: Nombre de la colección

    Returns:
        (is_safe: bool, error_message: str)
    """
    if not mongo_validator:
        return (True, None)

    try:
        result = mongo_validator.validate_query(query, collection)

        if not result.is_safe:
            error_msg = f"Query bloqueada por seguridad: {', '.join(result.blocked_reasons)}"
            logger.warning(f"[SECURITY] {error_msg}")
            return (False, error_msg)

        if result.warnings:
            logger.info(f"[SECURITY] Query warnings: {', '.join(result.warnings)}")

        return (True, None)

    except Exception as e:
        logger.error(f"[SECURITY] Error validando query: {e}")
        return (False, f"Error de validación de seguridad: {str(e)}")


# ============================================================================
# HELPER FUNCTIONS - QUERY DETECTION
# ============================================================================

def is_predefined_query(query: str, mode: str) -> bool:
    """
    Detecta si una query es predefinida (tiene lógica hardcoded optimizada).
    
    Args:
        query: Query del usuario
        mode: Modo activo
        
    Returns:
        True si es query predefinida, False si debe usar sistema semántico
    """
    query_lower = query.lower()
    
    # Modo conversacional SIEMPRE usa sistema semántico
    if mode == "conversational":
        return False
    
    # Queries predefinidas de PHARMACY
    if mode == "pharmacy":
        predefined_patterns = [
            "farmacias activas",
            "farmacia activa",
            "total de farmacias",
            "estado de la red",
            "distribución geográfica",
            "farmacias por ciudad"
        ]
        return any(pattern in query_lower for pattern in predefined_patterns)
    
    # Queries predefinidas de PRODUCT
    if mode == "product":
        predefined_patterns = [
            "catálogo de productos",
            "total de productos",
            "productos activos",
            "activos vs inactivos"
        ]
        return any(pattern in query_lower for pattern in predefined_patterns)
    
    # Queries predefinidas de PARTNER
    if mode == "partner":
        # Lista de partners conocidos
        known_partners = ['glovo', 'uber', 'justeat', 'carrefour', 'amazon', 
                         'danone', 'procter', 'enna', 'nordic', 'chiesi', 'ferrer']
        
        predefined_patterns = [
            "gmv de",
            "gmv total",
            "pedidos de",
            "pedidos totales",
            "comparación",
            "ticket medio",
            "rendimiento de",
            "top farmacias",
            "top 10 farmacias",
            "ranking de farmacias",
            "farmacias que más venden",
            "mejores farmacias"
        ]
        
        # Es predefinida si menciona un patrón conocido Y un partner
        has_pattern = any(pattern in query_lower for pattern in predefined_patterns)
        has_partner = any(partner in query_lower for partner in known_partners)
        
        return has_pattern and has_partner
    
    return False


# ============================================================================
# API ROUTES - SESSION & MODE MANAGEMENT
# ============================================================================

@app.route('/api/session/mode', methods=['POST'])
def change_mode():
    """Change the mode for current session."""
    data = request.json
    session_id = data.get('session_id', 'default')
    mode = data.get('mode', 'conversational')

    # Store in session
    if session_id not in sessions:
        sessions[session_id] = {
            'mode': mode,
            'created_at': datetime.now(),
            'query_count': 0,
            'last_entity': None
        }
    else:
        sessions[session_id]['mode'] = mode

    logger.info(f"[Luda Mind] Session {session_id} changed to mode: {mode}")

    return jsonify({
        'success': True,
        'mode': mode,
        'message': f'Modo cambiado a {mode}'
    })

# ============================================================================
# API ROUTES - QUERY PROCESSING
# ============================================================================

@app.route('/api/query', methods=['POST'])
def process_query():
    """
    Process a query with mode context for Luda Mind.
    """
    data = request.json
    query = data.get('query', '')
    mode = data.get('mode', 'conversational')
    session_id = data.get('session_id', 'default')

    if not query:
        return jsonify({
            'success': False,
            'error': 'No query provided'
        }), 400

    # Update session
    if session_id not in sessions:
        sessions[session_id] = {
            'mode': mode,
            'created_at': datetime.now(),
            'query_count': 0,
            'last_entity': None
        }

    sessions[session_id]['query_count'] += 1

    logger.info(f"[Luda Mind] Processing query in mode {mode}: {query[:100]}")

    try:
        # ====================================================================
        # MODO HÍBRIDO: Predefinidas (rápidas) vs Semánticas (flexibles)
        # ====================================================================
        
        # Modo conversacional SIEMPRE usa sistema semántico
        if mode == 'conversational':
            if smart_processor and mongodb_connected:
                logger.info(f"[Luda Mind] 🧠 Usando sistema semántico (conversational)")
                result = smart_processor.process(query, mode)
            else:
                # Fallback si no hay sistema semántico
                result = process_conversational_query(query)
        
        # Otros modos: detectar si es query predefinida
        elif is_predefined_query(query, mode):
            # Query predefinida → usar lógica optimizada (hardcoded)
            logger.info(f"[Luda Mind] ⚡ Usando query predefinida (optimizada)")
            
            if mode == 'pharmacy':
                result = process_pharmacy_query(query)
            elif mode == 'product':
                result = process_product_query(query)
            elif mode == 'partner':
                result = process_partner_query(query)
            else:
                result = process_conversational_query(query)
        
        else:
            # Query NO predefinida → usar sistema semántico
            if smart_processor and mongodb_connected:
                logger.info(f"[Luda Mind] 🧠 Usando sistema semántico (query no predefinida)")
                result = smart_processor.process(query, mode)
            else:
                # Fallback a lógica hardcoded si no hay semántico
                logger.warning(f"[Luda Mind] ⚠️ Sistema semántico no disponible, usando fallback")
                
                if mode == 'pharmacy':
                    result = process_pharmacy_query(query)
                elif mode == 'product':
                    result = process_product_query(query)
                elif mode == 'partner':
                    result = process_partner_query(query)
                else:
                    result = process_conversational_query(query)

        return jsonify({
            'success': True,
            'answer': result['answer'],
            'database': result.get('database', 'unknown'),
            'mode': mode,
            'confidence': result.get('confidence', 0.8),
            'timestamp': datetime.now().isoformat(),
            'system': 'Luda Mind',
            'method': 'semantic' if not is_predefined_query(query, mode) or mode == 'conversational' else 'optimized'
        })

    except Exception as e:
        logger.error(f"[Luda Mind] Query processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)[:200],
            'answer': f"Error procesando consulta: {str(e)[:100]}"
        }), 500

# ============================================================================
# MODE-SPECIFIC PROCESSORS
# ============================================================================

def process_pharmacy_query(query: str) -> dict:
    """Process pharmacy-specific queries for Luda Mind."""

    if not mongodb_connected:
        return {
            'answer': "⚠️ MongoDB no está conectado. Por favor, verifica el túnel SSH para consultas de farmacias.",
            'database': 'mongodb'
        }

    try:
        query_lower = query.lower()
        
        # Queries generales (sin ID específico)
        if 'total' in query_lower and 'farmacias' in query_lower:
            total = mongo_db.pharmacies.count_documents({})
            active = mongo_db.pharmacies.count_documents({'active': 1})  # active es int, no bool
            
            answer = f"""
🏥 **Red de Farmacias** (Luda Mind)

📊 **Estadísticas Generales:**
• Total de farmacias: {total:,}
• Farmacias activas: {active:,}
• Farmacias inactivas: {total - active:,}
• Tasa de actividad: {(active/total*100):.1f}%

*Fuente: Luda Mind - MongoDB*
            """
            return {
                'answer': answer,
                'database': 'mongodb',
                'confidence': 0.95
            }

        # =====================================================================
        # QUERY PREDEFINIDA: Farmacias por provincia
        # =====================================================================
        if ('provincia' in query_lower or 'provincias' in query_lower) and \
           ('farmacia' in query_lower or 'distribución' in query_lower or 'cuántas' in query_lower or 'numero' in query_lower or 'número' in query_lower):

            # Pipeline optimizado
            pipeline = [
                {"$match": {"active": 1}},
                {
                    "$group": {
                        "_id": "$contact.province",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]

            # Validar seguridad
            is_safe, error_msg = validate_mongodb_pipeline(pipeline, "pharmacies")
            if not is_safe:
                return {
                    'answer': f"❌ Consulta bloqueada: {error_msg}",
                    'database': 'mongodb',
                    'confidence': 0.0
                }

            # Ejecutar
            results = list(mongo_db.pharmacies.aggregate(pipeline))

            if results:
                answer = "📊 **Distribución de Farmacias por Provincia** (Luda Mind)\n\n"
                answer += f"Total de provincias: {len(results)}\n\n"

                # Mostrar todas las provincias o top 20
                limit = 20 if len(results) > 20 else len(results)

                for idx, item in enumerate(results[:limit], 1):
                    provincia = item.get('_id') or "(sin provincia)"
                    count = item.get('count', 0)
                    answer += f"{idx:2}. {provincia:30} → {count:4} farmacias\n"

                if len(results) > limit:
                    answer += f"\n... y {len(results) - limit} provincias más\n"

                # Totales
                total_farmacias = sum(r['count'] for r in results)
                answer += f"\n📈 **Total de Farmacias Activas:** {total_farmacias:,}\n"
                answer += "\n*Fuente: Luda Mind - MongoDB (query predefinida)*"

                return {
                    'answer': answer,
                    'database': 'mongodb',
                    'confidence': 0.98
                }

        # =====================================================================
        # QUERY PREDEFINIDA: Porcentaje de farmacias activas
        # =====================================================================
        if ('porcentaje' in query_lower or '%' in query_lower) and \
           ('activas' in query_lower or 'activo' in query_lower):

            # Pipeline con $facet para obtener activas y totales en paralelo
            pipeline = [
                {"$facet": {
                    "activas": [
                        {"$match": {"active": 1}},
                        {"$count": "count"}
                    ],
                    "totales": [
                        {"$count": "count"}
                    ]
                }}
            ]

            # Validar seguridad
            is_safe, error_msg = validate_mongodb_pipeline(pipeline, "pharmacies")
            if not is_safe:
                return {
                    'answer': f"❌ Consulta bloqueada: {error_msg}",
                    'database': 'mongodb',
                    'confidence': 0.0
                }

            # Ejecutar
            results = list(mongo_db.pharmacies.aggregate(pipeline))

            if results:
                result = results[0]
                activas = result['activas'][0]['count'] if result['activas'] else 0
                totales = result['totales'][0]['count'] if result['totales'] else 0
                inactivas = totales - activas
                porcentaje_activas = (activas / totales * 100) if totales > 0 else 0
                porcentaje_inactivas = (inactivas / totales * 100) if totales > 0 else 0

                answer = f"""📊 **Porcentaje de Farmacias Activas** (Luda Mind)

📈 **Estadísticas:**
• Total de farmacias: {totales:,}
• Farmacias activas: {activas:,} ({porcentaje_activas:.1f}%)
• Farmacias inactivas: {inactivas:,} ({porcentaje_inactivas:.1f}%)

📊 **Ratio de actividad:** {porcentaje_activas:.2f}%

*Fuente: Luda Mind - MongoDB (query predefinida)*"""

                return {
                    'answer': answer,
                    'database': 'mongodb',
                    'confidence': 0.98
                }

        # =====================================================================
        # QUERY PREDEFINIDA: Presencia de un producto en farmacias
        # =====================================================================
        # Detectar patrones: "presencia de [producto]", "qué farmacias tienen [producto]",
        # "dónde se vende [producto]", "farmacias con [producto]"
        producto_patterns = [
            r'presencia\s+(?:de\s+)?(?:el\s+)?(?:producto\s+)?["\']?(.+?)["\']?(?:\s+en|\s*$)',
            r'(?:qué|que|cuáles|cuales)\s+farmacias\s+(?:tienen|venden|ofrecen)\s+["\']?(.+?)["\']?(?:\s*$|\?)',
            r'(?:dónde|donde)\s+(?:se\s+)?(?:vende|tienen|hay)\s+["\']?(.+?)["\']?(?:\s*$|\?)',
            r'farmacias\s+(?:con|que\s+tienen)\s+["\']?(.+?)["\']?(?:\s+en|\s*$)',
            r'(?:buscar|encontrar)\s+["\']?(.+?)["\']?\s+en\s+farmacias'
        ]

        producto_buscado = None
        for pattern in producto_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                producto_buscado = match.group(1).strip()
                # Limpiar el producto de palabras comunes al final
                producto_buscado = re.sub(r'\s+(en|de|las|los|la|el)$', '', producto_buscado)
                break

        if producto_buscado and len(producto_buscado) >= 3:
            # Pipeline para buscar farmacias que tienen el producto
            # Busca en el catálogo de productos de cada farmacia
            pipeline = [
                {"$match": {"active": 1}},
                {"$lookup": {
                    "from": "products",
                    "let": {"pharmacy_id": "$_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$pharmacy_id", "$$pharmacy_id"]},
                            "name": {"$regex": producto_buscado, "$options": "i"}
                        }},
                        {"$limit": 1}
                    ],
                    "as": "producto_encontrado"
                }},
                {"$match": {"producto_encontrado": {"$ne": []}}},
                {"$project": {
                    "_id": 1,
                    "name": 1,
                    "contact.province": 1,
                    "contact.city": 1,
                    "producto": {"$arrayElemAt": ["$producto_encontrado.name", 0]}
                }},
                {"$limit": 100}
            ]

            # Validar seguridad
            is_safe, error_msg = validate_mongodb_pipeline(pipeline, "pharmacies")
            if not is_safe:
                return {
                    'answer': f"❌ Consulta bloqueada: {error_msg}",
                    'database': 'mongodb',
                    'confidence': 0.0
                }

            try:
                results = list(mongo_db.pharmacies.aggregate(pipeline))

                if results:
                    answer = f"📊 **Presencia del producto '{producto_buscado}'** (Luda Mind)\n\n"
                    answer += f"✅ **Farmacias que lo tienen:** {len(results)}\n\n"

                    # Agrupar por provincia para mejor visualización
                    por_provincia = {}
                    for farm in results:
                        prov = farm.get('contact', {}).get('province', 'Sin provincia')
                        if prov not in por_provincia:
                            por_provincia[prov] = []
                        por_provincia[prov].append(farm)

                    # Mostrar resumen por provincia
                    answer += "📍 **Distribución por provincia:**\n"
                    for prov, farms in sorted(por_provincia.items(), key=lambda x: -len(x[1])):
                        answer += f"  • {prov}: {len(farms)} farmacias\n"

                    # Mostrar detalle de primeras 10 farmacias
                    answer += "\n🏥 **Primeras 10 farmacias:**\n"
                    for idx, farm in enumerate(results[:10], 1):
                        nombre = farm.get('name', 'N/A')
                        ciudad = farm.get('contact', {}).get('city', '')
                        answer += f"  {idx}. {nombre}"
                        if ciudad:
                            answer += f" ({ciudad})"
                        answer += "\n"

                    if len(results) > 10:
                        answer += f"\n  ... y {len(results) - 10} farmacias más\n"

                    answer += "\n*Fuente: Luda Mind - MongoDB (query predefinida)*"
                else:
                    answer = f"❌ No se encontraron farmacias con el producto '{producto_buscado}'\n\n"
                    answer += "💡 **Sugerencias:**\n"
                    answer += "• Verifica el nombre del producto\n"
                    answer += "• Prueba con un nombre más genérico\n"
                    answer += "• El producto puede no estar en el catálogo actual"

                return {
                    'answer': answer,
                    'database': 'mongodb',
                    'confidence': 0.95
                }
            except Exception as e:
                logger.error(f"Error en query presencia producto: {e}")
                # Continuar con el flujo normal si falla

        # =====================================================================
        # QUERY PREDEFINIDA: Top farmacias ventas por partner (Glovo, Uber, etc.)
        # =====================================================================
        # Detectar patrones: "top ventas glovo barcelona", "farmacia top glovo",
        # "ranking farmacias uber madrid", "mejores farmacias glovo"
        partners = ['glovo', 'uber', 'danone', 'hartmann', 'carrefour', 'shortage']
        partner_detected = None
        provincia_detected = None

        # Detectar partner
        for partner in partners:
            if partner in query_lower:
                partner_detected = partner
                break

        # Detectar provincia/ciudad (lista simplificada de las más comunes)
        provincias_map = {
            'barcelona': 'Barcelona', 'madrid': 'Madrid', 'valencia': 'Valencia',
            'sevilla': 'Sevilla', 'málaga': 'Málaga', 'malaga': 'Málaga',
            'alicante': 'Alicante', 'murcia': 'Murcia', 'zaragoza': 'Zaragoza',
            'bilbao': 'Vizcaya', 'vizcaya': 'Vizcaya', 'bizkaia': 'Vizcaya',
            'granada': 'Granada', 'córdoba': 'Córdoba', 'cordoba': 'Córdoba',
            'valladolid': 'Valladolid', 'palma': 'Illes Balears', 'mallorca': 'Illes Balears',
            'las palmas': 'Las Palmas', 'tenerife': 'Santa Cruz de Tenerife',
            'asturias': 'Asturias', 'oviedo': 'Asturias', 'gijón': 'Asturias',
            'cantabria': 'Cantabria', 'santander': 'Cantabria',
            'navarra': 'Navarra', 'pamplona': 'Navarra',
            'la rioja': 'La Rioja', 'logroño': 'La Rioja',
            'castellón': 'Castellón', 'castellon': 'Castellón',
            'toledo': 'Toledo', 'ciudad real': 'Ciudad Real',
            'cádiz': 'Cádiz', 'cadiz': 'Cádiz', 'huelva': 'Huelva',
            'almería': 'Almería', 'almeria': 'Almería', 'jaén': 'Jaén', 'jaen': 'Jaén'
        }

        for key, value in provincias_map.items():
            if key in query_lower:
                provincia_detected = value
                break

        # Detectar si es query de top ventas
        is_top_ventas = any(kw in query_lower for kw in [
            'top ventas', 'top farmacia', 'ranking', 'mejores farmacia',
            'farmacia top', 'más vende', 'mas vende', 'mejor farmacia',
            'farmacias top', 'top farmacias'
        ])

        if partner_detected and is_top_ventas:
            try:
                # Pipeline para top farmacias por partner
                match_stage = {"thirdUser.user": partner_detected}

                # Si hay provincia, necesitamos hacer lookup primero
                if provincia_detected:
                    pipeline = [
                        {"$match": match_stage},
                        # Lookup para obtener datos de farmacia
                        {"$lookup": {
                            "from": "pharmacies",
                            "let": {"target_id": {"$toObjectId": "$target"}},
                            "pipeline": [
                                {"$match": {"$expr": {"$eq": ["$_id", "$$target_id"]}}},
                                {"$project": {"description": 1, "contact.province": 1, "contact.city": 1}}
                            ],
                            "as": "pharmacy_info"
                        }},
                        {"$unwind": {"path": "$pharmacy_info", "preserveNullAndEmptyArrays": False}},
                        # Filtrar por provincia
                        {"$match": {"pharmacy_info.contact.province": provincia_detected}},
                        # Agrupar por farmacia
                        {"$group": {
                            "_id": "$target",
                            "pharmacy_name": {"$first": "$pharmacy_info.description"},
                            "city": {"$first": "$pharmacy_info.contact.city"},
                            "num_pedidos": {"$sum": 1},
                            "gmv_total": {
                                "$sum": {
                                    "$reduce": {
                                        "input": {"$ifNull": ["$items", []]},
                                        "initialValue": 0,
                                        "in": {
                                            "$add": [
                                                "$$value",
                                                {"$multiply": [
                                                    {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                    {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                                ]}
                                            ]
                                        }
                                    }
                                }
                            }
                        }},
                        {"$sort": {"gmv_total": -1}},
                        {"$limit": 20}
                    ]
                else:
                    # Sin filtro de provincia
                    pipeline = [
                        {"$match": match_stage},
                        {"$lookup": {
                            "from": "pharmacies",
                            "let": {"target_id": {"$toObjectId": "$target"}},
                            "pipeline": [
                                {"$match": {"$expr": {"$eq": ["$_id", "$$target_id"]}}},
                                {"$project": {"description": 1, "contact.province": 1, "contact.city": 1}}
                            ],
                            "as": "pharmacy_info"
                        }},
                        {"$unwind": {"path": "$pharmacy_info", "preserveNullAndEmptyArrays": False}},
                        {"$group": {
                            "_id": "$target",
                            "pharmacy_name": {"$first": "$pharmacy_info.description"},
                            "province": {"$first": "$pharmacy_info.contact.province"},
                            "city": {"$first": "$pharmacy_info.contact.city"},
                            "num_pedidos": {"$sum": 1},
                            "gmv_total": {
                                "$sum": {
                                    "$reduce": {
                                        "input": {"$ifNull": ["$items", []]},
                                        "initialValue": 0,
                                        "in": {
                                            "$add": [
                                                "$$value",
                                                {"$multiply": [
                                                    {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                    {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                                ]}
                                            ]
                                        }
                                    }
                                }
                            }
                        }},
                        {"$sort": {"gmv_total": -1}},
                        {"$limit": 20}
                    ]

                # Validar seguridad
                is_safe, error_msg = validate_mongodb_pipeline(pipeline, "bookings")
                if not is_safe:
                    return {
                        'answer': f"❌ Consulta bloqueada: {error_msg}",
                        'database': 'mongodb',
                        'confidence': 0.0
                    }

                # Ejecutar
                results = list(mongo_db.bookings.aggregate(pipeline, allowDiskUse=True))

                if results:
                    partner_title = partner_detected.capitalize()
                    location_str = f" en {provincia_detected}" if provincia_detected else ""
                    answer = f"📊 **Top Farmacias {partner_title}{location_str}** (Luda Mind)\n\n"

                    # Calcular totales
                    total_gmv = sum(r.get('gmv_total', 0) for r in results)
                    total_pedidos = sum(r.get('num_pedidos', 0) for r in results)

                    answer += f"📈 **Resumen:**\n"
                    answer += f"• Total farmacias: {len(results)}\n"
                    answer += f"• Total pedidos: {total_pedidos:,}\n"
                    answer += f"• GMV total: €{total_gmv:,.2f}\n\n"

                    answer += f"🏆 **Ranking Top 20:**\n"
                    answer += "```\n"
                    answer += f"{'#':>2} {'Farmacia':<30} {'Pedidos':>8} {'GMV (€)':>12}\n"
                    answer += "-" * 56 + "\n"

                    for idx, r in enumerate(results[:20], 1):
                        nombre = (r.get('pharmacy_name') or 'Sin nombre')[:28]
                        pedidos = r.get('num_pedidos', 0)
                        gmv = r.get('gmv_total', 0)
                        answer += f"{idx:>2}. {nombre:<28} {pedidos:>8,} {gmv:>11,.2f}\n"

                    answer += "```\n"
                    answer += "\n*Fuente: Luda Mind - MongoDB (query predefinida)*"

                    return {
                        'answer': answer,
                        'database': 'mongodb',
                        'confidence': 0.97
                    }
                else:
                    location_str = f" en {provincia_detected}" if provincia_detected else ""
                    return {
                        'answer': f"❌ No se encontraron datos de {partner_detected.capitalize()}{location_str}",
                        'database': 'mongodb',
                        'confidence': 0.9
                    }

            except Exception as e:
                logger.error(f"Error en query top ventas partner: {e}")
                # Continuar con el flujo normal si falla

        # Extract pharmacy ID if present
        pharmacy_match = re.search(r'farmacia\s+(\d+)', query_lower)

        if pharmacy_match:
            pharmacy_id = pharmacy_match.group(1)

            # Query specific pharmacy
            pharmacy = mongo_db.pharmacies.find_one({'_id': int(pharmacy_id)})

            if pharmacy:
                # Get additional stats
                bookings_count = mongo_db.bookings.count_documents({'pharmacy_id': int(pharmacy_id)})

                answer = f"""
🏥 **Información de Farmacia {pharmacy_id}** (Luda Mind)

📍 **Datos Básicos:**
• Nombre: {pharmacy.get('name', 'N/A')}
• Estado: {'✅ Activa' if pharmacy.get('active') else '❌ Inactiva'}
• Dirección: {pharmacy.get('address', 'N/A')}
• Ciudad: {pharmacy.get('city', 'N/A')}

📊 **Estadísticas:**
• Total de pedidos: {bookings_count:,}

*Fuente: Luda Mind - MongoDB (modo Farmacias)*
                """
            else:
                answer = f"❌ No se encontró la farmacia con ID {pharmacy_id}"

        elif 'activas' in query.lower():
            # Count active pharmacies
            total = mongo_db.pharmacies.count_documents({})
            active = mongo_db.pharmacies.count_documents({'active': 1})

            # Get city breakdown if mentioned
            if 'madrid' in query.lower():
                madrid_count = mongo_db.pharmacies.count_documents({'city': 'Madrid', 'active': True})
                answer = f"""
🏥 **Farmacias Activas en Madrid** (Luda Mind)

• Madrid: {madrid_count:,} farmacias activas
• Total sistema: {active:,} de {total:,} farmacias

*Fuente: Luda Mind - MongoDB*
                """
            else:
                answer = f"""
🏥 **Estado General de Farmacias** (Luda Mind)

• Total: {total:,} farmacias
• Activas: {active:,} farmacias ({(active/total*100):.1f}%)
• Inactivas: {total - active:,} farmacias

*Fuente: Luda Mind - MongoDB*
                """

        elif 'top' in query.lower():
            # Top pharmacies
            pipeline = [
                {"$lookup": {
                    "from": "bookings",
                    "localField": "_id",
                    "foreignField": "pharmacy_id",
                    "as": "bookings"
                }},
                {"$project": {
                    "name": 1,
                    "city": 1,
                    "booking_count": {"$size": "$bookings"}
                }},
                {"$sort": {"booking_count": -1}},
                {"$limit": 10}
            ]

            top_pharmacies = list(mongo_db.pharmacies.aggregate(pipeline))

            answer = "🏥 **Top 10 Farmacias por Pedidos** (Luda Mind)\n\n"
            for i, pharmacy in enumerate(top_pharmacies, 1):
                answer += f"{i}. {pharmacy.get('name', 'N/A')} ({pharmacy.get('city', 'N/A')}): {pharmacy.get('booking_count', 0):,} pedidos\n"

            answer += "\n*Fuente: Luda Mind - MongoDB*"

        else:
            # General query
            total = mongo_db.pharmacies.count_documents({})
            answer = f"""
🏥 **Información de Farmacias** (Luda Mind)

Total de farmacias en el sistema: {total:,}

💡 **Sugerencias:**
• Pregunta por una farmacia específica (ej: "farmacia 123")
• Consulta farmacias activas
• Solicita el top de farmacias

*Sistema: Luda Mind - Modo Farmacias*
                """

        return {
            'answer': answer,
            'database': 'mongodb',
            'confidence': 0.9
        }

    except Exception as e:
        logger.error(f"[Luda Mind] Pharmacy query error: {e}")
        return {
            'answer': f"❌ Error procesando consulta: {str(e)[:100]}",
            'database': 'error',
            'confidence': 0.3
        }

def process_product_query(query: str) -> dict:
    """Process product-specific queries for Luda Mind - Solo MongoDB."""

    if not mongodb_connected:
        return {
            'answer': "⚠️ MongoDB no está conectado para consultas de productos.",
            'database': 'mongodb'
        }

    try:
        query_lower = query.lower()
        
        # Catálogo general
        if 'catálogo' in query_lower or ('total' in query_lower and 'productos' in query_lower):
            total = mongo_db.items.count_documents({})
            active = mongo_db.items.count_documents({'active': 1})
            
            answer = f"""
💊 **Catálogo de Productos** (Luda Mind)

📦 **Estadísticas:**
• Total de productos: {total:,}
• Productos activos: {active:,}
• Productos inactivos: {total - active:,}
• Tasa de actividad: {(active/total*100):.1f}%

💡 **Información disponible:**
• Búsqueda de productos
• Precios y disponibilidad
• Categorías
• EANs y códigos

*Fuente: Luda Mind - MongoDB*
            """
        
        # Productos activos vs inactivos
        elif 'activos' in query_lower or 'inactivos' in query_lower:
            total = mongo_db.items.count_documents({})
            active = mongo_db.items.count_documents({'active': 1})
            inactive = total - active
            
            answer = f"""
💊 **Estado de Productos** (Luda Mind)

✅ **Activos:** {active:,} productos ({(active/total*100):.1f}%)
❌ **Inactivos:** {inactive:,} productos ({(inactive/total*100):.1f}%)

📊 **Total:** {total:,} productos en el catálogo

*Fuente: Luda Mind - MongoDB*
            """
        
        # Búsqueda por EAN o nombre
        elif 'ean' in query_lower or 'buscar' in query_lower or 'código' in query_lower:
            # Ejemplo de búsqueda
            sample_products = list(mongo_db.items.find({'active': 1}).limit(5))
            
            answer = "💊 **Búsqueda de Productos** (Luda Mind)\n\n"
            
            if sample_products:
                answer += "📋 **Productos de ejemplo:**\n"
                for product in sample_products[:3]:
                    answer += f"\n• {product.get('name', 'Sin nombre')}\n"
                    answer += f"  EAN: {product.get('ean', 'N/A')}\n"
                    if 'price' in product:
                        answer += f"  Precio: €{product.get('price', 0):.2f}\n"
                
                answer += "\n💡 Proporciona un EAN o nombre específico para búsqueda detallada."
            
            answer += "\n\n*Fuente: Luda Mind - MongoDB*"
        
        # Precios
        elif 'precio' in query_lower:
            # Estadísticas de precios
            pipeline = [
                {"$match": {"active": True, "price": {"$exists": True, "$gt": 0}}},
                {"$group": {
                    "_id": None,
                    "avg_price": {"$avg": "$price"},
                    "min_price": {"$min": "$price"},
                    "max_price": {"$max": "$price"},
                    "count": {"$sum": 1}
                }}
            ]
            
            result = list(mongo_db.items.aggregate(pipeline))
            
            if result and result[0]['count'] > 0:
                stats = result[0]
                answer = f"""
💊 **Análisis de Precios** (Luda Mind)

💰 **Estadísticas:**
• Precio promedio: €{stats.get('avg_price', 0):.2f}
• Precio mínimo: €{stats.get('min_price', 0):.2f}
• Precio máximo: €{stats.get('max_price', 0):.2f}
• Productos con precio: {stats.get('count', 0):,}

*Fuente: Luda Mind - MongoDB*
                """
            else:
                answer = "💊 No se encontró información de precios en el catálogo."
        
        # Categorías
        elif 'categoría' in query_lower or 'categorias' in query_lower:
            # Ver si hay campo de categoría
            categories = mongo_db.items.distinct('category')
            
            if categories and len(categories) > 0:
                answer = f"""
💊 **Categorías de Productos** (Luda Mind)

📂 **Total de categorías:** {len(categories)}

🏷️ **Principales categorías:**
"""
                for cat in categories[:10]:
                    if cat:
                        count = mongo_db.items.count_documents({'category': cat})
                        answer += f"• {cat}: {count:,} productos\n"
                
                answer += "\n*Fuente: Luda Mind - MongoDB*"
            else:
                answer = "💊 El catálogo no tiene categorías definidas actualmente."
        
        # Stock o disponibilidad
        elif 'stock' in query_lower or 'disponibilidad' in query_lower:
            total_stock_items = mongo_db.stockItems.count_documents({})
            
            answer = f"""
💊 **Disponibilidad de Productos** (Luda Mind)

📦 **Inventario:**
• Registros de stock: {total_stock_items:,}

💡 **Para consultar stock específico:**
Proporciona el ID o EAN del producto.

*Fuente: Luda Mind - MongoDB*
            """
        
        # MySQL queries (sell in / sell out)
        elif any(term in query_lower for term in ['vendidos', 'ventas', 'rotación', 'demanda']):
            answer = """
💊 **Análisis de Ventas** (Luda Mind)

⚠️ **Nota:** Los datos de ventas (sell in/sell out) están en MySQL.

Para análisis de productos en MongoDB puedes consultar:
• Catálogo de productos
• Precios y disponibilidad
• Stock actual
• Información de EANs

*Para ventas, usa MySQL exclusivamente.*
            """
        
        else:
            # Respuesta general
            total = mongo_db.items.count_documents({})
            answer = f"""
💊 **Modo Productos** (Luda Mind)

📦 **Catálogo:** {total:,} productos

💡 **Consultas disponibles:**
• Catálogo completo
• Productos activos/inactivos
• Búsqueda por EAN o nombre
• Precios de productos
• Categorías
• Disponibilidad y stock

⚠️ **Nota:** Datos de ventas solo en MySQL (sell in/sell out)

*Fuente: Luda Mind - MongoDB*
            """
        
        return {
            'answer': answer,
            'database': 'mongodb',
            'confidence': 0.85
        }

    except Exception as e:
        logger.error(f"[Luda Mind] Product query error: {e}")
        return {
            'answer': f"❌ Error procesando consulta: {str(e)[:100]}",
            'database': 'error',
            'confidence': 0.3
        }

def process_partner_query(query: str) -> dict:
    """Process partner-specific queries for Luda Mind."""

    if not mongodb_connected:
        return {
            'answer': "⚠️ MongoDB no está conectado. Necesario para consultas de partners.",
            'database': 'mongodb'
        }

    try:
        from datetime import datetime, timedelta
        query_lower = query.lower()

        # Identify partner (12 activos, orden específico para evitar false matches)
        partners = [
            'glovo-otc',  # PRIMERO para evitar que "glovo" lo capture
            'glovo',
            'uber',
            'justeat',
            'carrefour',
            'amazon',
            'danone',
            'procter',
            'enna',
            'nordic',
            'chiesi',
            'ferrer'
        ]
        selected_partner = None

        for partner in partners:
            if partner in query_lower:
                selected_partner = partner
                break

        # =====================================================================
        # QUERY PREDEFINIDA: Top farmacias por partner
        # =====================================================================
        if selected_partner and any(pattern in query_lower for pattern in ['top', 'ranking', 'mejores', 'más venden']):
            # Determinar límite
            limit = 10  # Default
            if 'top 5' in query_lower:
                limit = 5
            elif 'top 20' in query_lower:
                limit = 20
            
            # Pipeline optimizado para top farmacias
            pipeline = [
                {"$match": {"thirdUser.user": selected_partner}},
                {
                    "$group": {
                        "_id": "$target",
                        "total_gmv": {
                            "$sum": {
                                "$cond": {
                                    "if": {"$gt": ["$thirdUser.price", None]},
                                    "then": "$thirdUser.price",
                                    "else": {
                                        "$sum": {
                                            "$map": {
                                                "input": "$items",
                                                "as": "item",
                                                "in": {
                                                    "$multiply": [
                                                        {"$toDouble": {"$ifNull": ["$$item.pvp", 0]}},
                                                        {"$toInt": {"$ifNull": ["$$item.quantity", 0]}}
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "total_pedidos": {"$sum": 1}
                    }
                },
                {"$sort": {"total_gmv": -1}},
                {"$limit": limit},
                {
                    "$lookup": {
                        "from": "pharmacies",
                        "localField": "_id",
                        "foreignField": "_id",
                        "as": "pharmacy_info"
                    }
                }
            ]

            # Validar pipeline por seguridad
            is_safe, error_msg = validate_mongodb_pipeline(pipeline, "bookings")
            if not is_safe:
                return {
                    'answer': f"❌ Consulta bloqueada por seguridad: {error_msg}",
                    'database': 'mongodb',
                    'confidence': 0.0
                }

            results = list(mongo_db.bookings.aggregate(pipeline))
            
            if results:
                answer = f"🏥 **Top {limit} Farmacias con más ventas en {selected_partner.title()}** (Luda Mind)\n\n"
                
                for idx, item in enumerate(results, 1):
                    pharmacy_info = item['pharmacy_info'][0] if item.get('pharmacy_info') else {}
                    name = pharmacy_info.get('description', f"Farmacia ID: {str(item['_id'])[:12]}...")
                    city = pharmacy_info.get('contact', {}).get('city', '')
                    
                    answer += f"**{idx}. {name}**"
                    if city:
                        answer += f" ({city})"
                    answer += "\n"
                    answer += f"• GMV: €{item['total_gmv']:,.2f}\n"
                    answer += f"• Pedidos: {item['total_pedidos']:,}\n\n"
                
                # Totales
                total_gmv = sum(r['total_gmv'] for r in results)
                total_pedidos = sum(r['total_pedidos'] for r in results)
                
                answer += f"\n📊 **Totales (Top {limit}):**\n"
                answer += f"• GMV Total: €{total_gmv:,.2f}\n"
                answer += f"• Pedidos Totales: {total_pedidos:,}\n"
                answer += "\n*Fuente: Luda Mind - MongoDB (query predefinida)*"
                
                return {
                    'answer': answer,
                    'database': 'mongodb',
                    'confidence': 0.95
                }
        
        # =====================================================================
        # QUERY PREDEFINIDA: KPIs COMPLETOS de partner
        # =====================================================================
        if selected_partner and 'kpis' in query_lower:
            # Detectar período - más exhaustivo para "mes pasado", "octubre", etc.
            import re
            from dateutil.relativedelta import relativedelta

            match_filter = {"thirdUser.user": selected_partner}
            period_text = "últimos 7 días"  # Default

            # Detectar mes pasado
            if 'mes pasado' in query_lower or 'último mes' in query_lower:
                last_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(months=1)
                current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                match_filter["createdDate"] = {"$gte": last_month_start, "$lt": current_month_start}
                period_text = f"mes pasado ({last_month_start.strftime('%B %Y')})"

            # Detectar mes específico (octubre, noviembre, etc.)
            elif any(month in query_lower for month in ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                                                         'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']):
                month_names = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
                              'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}

                for month_name, month_num in month_names.items():
                    if month_name in query_lower:
                        # Detectar año si se menciona
                        year_match = re.search(r'\b(20\d{2})\b', query_lower)
                        year = int(year_match.group(1)) if year_match else datetime.now().year

                        month_start = datetime(year, month_num, 1)
                        if month_num == 12:
                            month_end = datetime(year + 1, 1, 1)
                        else:
                            month_end = datetime(year, month_num + 1, 1)

                        match_filter["createdDate"] = {"$gte": month_start, "$lt": month_end}
                        period_text = f"{month_name.capitalize()} {year}"
                        break

            # Semana/mes/hoy
            elif 'semana' in query_lower or 'semanal' in query_lower:
                one_week_ago = datetime.now() - timedelta(days=7)
                match_filter["createdDate"] = {"$gte": one_week_ago}
                period_text = "esta semana"
            elif 'mes' in query_lower or 'mensual' in query_lower or 'este mes' in query_lower:
                one_month_ago = datetime.now() - timedelta(days=30)
                match_filter["createdDate"] = {"$gte": one_month_ago}
                period_text = "este mes"
            elif 'hoy' in query_lower:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                match_filter["createdDate"] = {"$gte": today}
                period_text = "hoy"
            else:
                # Default: últimos 7 días
                one_week_ago = datetime.now() - timedelta(days=7)
                match_filter["createdDate"] = {"$gte": one_week_ago}
                period_text = "últimos 7 días"

            # Pipeline con $facet para calcular TODAS las métricas en paralelo
            cancelled_state_id = "5a54c525b2948c860f00000d"

            pipeline = [
                {"$match": match_filter},
                {"$facet": {
                    # Métricas totales
                    "total_metrics": [
                        {"$addFields": {
                            "calculated_gmv": {
                                "$cond": {
                                    "if": {"$ifNull": ["$thirdUser.price", False]},
                                    "then": {"$toDouble": {"$ifNull": ["$thirdUser.price", 0]}},
                                    "else": {
                                        "$reduce": {
                                            "input": "$items",
                                            "initialValue": 0,
                                            "in": {
                                                "$add": [
                                                    "$$value",
                                                    {"$multiply": [
                                                        {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                        {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                                    ]}
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }},
                        {"$group": {
                            "_id": None,
                            "total_gmv": {"$sum": "$calculated_gmv"},
                            "total_bookings": {"$sum": 1}
                        }}
                    ],
                    # Métricas de cancelados
                    "cancelled_metrics": [
                        {"$match": {"state": cancelled_state_id}},
                        {"$addFields": {
                            "calculated_gmv": {
                                "$cond": {
                                    "if": {"$ifNull": ["$thirdUser.price", False]},
                                    "then": {"$toDouble": {"$ifNull": ["$thirdUser.price", 0]}},
                                    "else": {
                                        "$reduce": {
                                            "input": "$items",
                                            "initialValue": 0,
                                            "in": {
                                                "$add": [
                                                    "$$value",
                                                    {"$multiply": [
                                                        {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                        {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                                    ]}
                                                ]
                                            }
                                        }
                                    }
                                }
                            }
                        }},
                        {"$group": {
                            "_id": None,
                            "cancelled_gmv": {"$sum": "$calculated_gmv"},
                            "cancelled_bookings": {"$sum": 1}
                        }}
                    ],
                    # Farmacias únicas
                    "unique_pharmacies": [
                        {"$group": {"_id": "$target"}},
                        {"$count": "count"}
                    ]
                }}
            ]

            results = list(mongo_db.bookings.aggregate(pipeline))

            if results:
                result = results[0]

                # Extraer métricas
                total_metrics = result['total_metrics'][0] if result['total_metrics'] else {}
                cancelled_metrics = result['cancelled_metrics'][0] if result['cancelled_metrics'] else {}
                pharmacy_count = result['unique_pharmacies'][0]['count'] if result['unique_pharmacies'] else 0

                total_gmv = total_metrics.get('total_gmv', 0)
                total_bookings = total_metrics.get('total_bookings', 0)
                cancelled_gmv = cancelled_metrics.get('cancelled_gmv', 0)
                cancelled_bookings = cancelled_metrics.get('cancelled_bookings', 0)

                # Calcular métricas derivadas
                active_gmv = total_gmv - cancelled_gmv
                active_bookings = total_bookings - cancelled_bookings
                cancellation_rate = (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0

                answer = f"""
🤖 🤝 **Análisis de Partner: {selected_partner.capitalize()}** (Luda Mind)

📅 **Período:** {period_text}

📊 **KPIs Completos:**

💰 **GMV:**
• GMV Total: €{total_gmv:,.2f}
• GMV Cancelado: €{cancelled_gmv:,.2f}
• GMV Activo: €{active_gmv:,.2f}

📦 **Bookings:**
• Total Bookings: {total_bookings:,}
• Bookings Cancelados: {cancelled_bookings:,}
• Bookings Activos: {active_bookings:,}
• Tasa de Cancelación: {cancellation_rate:.2f}%

🏥 **Cobertura:**
• Farmacias con Pedidos: {pharmacy_count:,}

*Fuente: Luda Mind - MongoDB (query hardcodeada KPIs completos)*
                """

                return {
                    'answer': answer.strip(),
                    'database': 'mongodb',
                    'confidence': 0.98
                }
            else:
                answer = f"❌ No se encontraron datos de KPIs para {selected_partner} en {period_text}"
                return {
                    'answer': answer,
                    'database': 'mongodb',
                    'confidence': 0.5
                }

        # =====================================================================
        # QUERY PREDEFINIDA: GMV/Stats de partner
        # =====================================================================
        if selected_partner:
            # Determinar período de tiempo
            match_filter = {
                "thirdUser.user": {"$regex": selected_partner, "$options": "i"}
            }

            # Añadir filtro de fecha si se menciona
            if 'semana' in query_lower or 'semanal' in query_lower:
                one_week_ago = datetime.now() - timedelta(days=7)
                match_filter["createdDate"] = {"$gte": one_week_ago}
                period_text = "esta semana"
            elif 'mes' in query_lower or 'mensual' in query_lower:
                one_month_ago = datetime.now() - timedelta(days=30)
                match_filter["createdDate"] = {"$gte": one_month_ago}
                period_text = "este mes"
            elif 'hoy' in query_lower:
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                match_filter["createdDate"] = {"$gte": today}
                period_text = "hoy"
            else:
                # Default: últimos 7 días
                one_week_ago = datetime.now() - timedelta(days=7)
                match_filter["createdDate"] = {"$gte": one_week_ago}
                period_text = "últimos 7 días"
            
            # Query specific partner with correct fields
            # Usar método híbrido: thirdUser.price O calcular desde items
            pipeline = [
                {"$match": match_filter},
                {"$addFields": {
                    "calculated_gmv": {
                        "$cond": {
                            "if": {"$ifNull": ["$thirdUser.price", False]},
                            "then": {"$toDouble": {"$ifNull": ["$thirdUser.price", 0]}},
                            "else": {
                                "$reduce": {
                                    "input": "$items",
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {"$multiply": [
                                                {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                            ]}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }},
                {"$group": {
                    "_id": None,
                    "total_gmv": {"$sum": "$calculated_gmv"},
                    "count": {"$sum": 1},
                    "avg_gmv": {"$avg": "$calculated_gmv"}
                }}
            ]

            results = list(mongo_db.bookings.aggregate(pipeline))

            if results and results[0].get('count', 0) > 0:
                result = results[0]
                answer = f"""
🤝 **Análisis de Partner: {selected_partner.capitalize()}** (Luda Mind)

📅 **Período:** {period_text}

💰 **Métricas Principales:**
• GMV Total: €{result.get('total_gmv', 0):,.2f}
• Total de pedidos: {result.get('count', 0):,}
• Ticket medio: €{result.get('avg_gmv', 0):.2f}

📊 **Rendimiento:**
• Promedio diario: €{result.get('total_gmv', 0) / 7:,.2f}
• Tendencia: ↗️ Activo

*Fuente: Luda Mind - MongoDB (modo Partners)*
                """
            else:
                answer = f"❌ No se encontraron datos para el partner {selected_partner} en {period_text}"

        elif 'comparación' in query_lower or 'comparar' in query_lower:
            # Compare partners
            from datetime import datetime, timedelta
            one_week_ago = datetime.now() - timedelta(days=7)
            
            answer = "🤝 **Comparación de Partners** (Luda Mind)\n"
            answer += "📅 **Período:** Últimos 7 días\n\n"

            total_found = 0
            for partner in ['glovo', 'uber']:
                pipeline = [
                    {"$match": {
                        "thirdUser.user": {"$regex": partner, "$options": "i"},
                        "createdDate": {"$gte": one_week_ago}
                    }},
                    {"$addFields": {
                        "calculated_gmv": {
                            "$cond": {
                                "if": {"$ifNull": ["$thirdUser.price", False]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$reduce": {
                                        "input": "$items",
                                        "initialValue": 0,
                                        "in": {
                                            "$add": [
                                                "$$value",
                                                {"$multiply": [
                                                    {"$ifNull": ["$$this.pvp", 0]},
                                                    {"$ifNull": ["$$this.quantity", 0]}
                                                ]}
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }},
                    {"$group": {
                        "_id": None,
                        "total_gmv": {"$sum": "$calculated_gmv"},
                        "count": {"$sum": 1},
                        "avg_gmv": {"$avg": "$calculated_gmv"}
                    }}
                ]

                results = list(mongo_db.bookings.aggregate(pipeline))
                if results and results[0].get('count', 0) > 0:
                    result = results[0]
                    total_found += 1
                    answer += f"**{partner.capitalize()}:**\n"
                    answer += f"• GMV: €{result.get('total_gmv', 0):,.2f}\n"
                    answer += f"• Pedidos: {result.get('count', 0):,}\n"
                    answer += f"• Ticket medio: €{result.get('avg_gmv', 0):.2f}\n\n"
                else:
                    answer += f"**{partner.capitalize()}:**\n"
                    answer += f"• Sin datos esta semana\n\n"
            
            if total_found > 1:
                answer += "📊 **Análisis:** Glovo lidera el mercado de delivery\n"
            
            answer += "\n*Fuente: Luda Mind - MongoDB*"

        elif 'pedidos' in query_lower and ('partner' in query_lower or 'canal' in query_lower):
            # Pedidos totales por partner
            from datetime import datetime, timedelta
            
            # Determinar período
            if 'semana' in query_lower:
                date_filter = datetime.now() - timedelta(days=7)
                period = "esta semana"
            elif 'mes' in query_lower:
                date_filter = datetime.now() - timedelta(days=30)
                period = "este mes"
            elif 'hoy' in query_lower:
                date_filter = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                period = "hoy"
            else:
                date_filter = datetime.now() - timedelta(days=7)
                period = "últimos 7 días"
            
            # Agregación por partner con cálculo híbrido de GMV
            pipeline = [
                {"$match": {
                    "thirdUser.user": {"$exists": True},
                    "createdDate": {"$gte": date_filter}
                }},
                {"$addFields": {
                    "calculated_gmv": {
                        "$cond": {
                            "if": {"$ifNull": ["$thirdUser.price", False]},
                            "then": {"$toDouble": {"$ifNull": ["$thirdUser.price", 0]}},
                            "else": {
                                "$reduce": {
                                    "input": "$items",
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {"$multiply": [
                                                {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                            ]}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }},
                {"$group": {
                    "_id": "$thirdUser.user",
                    "total_pedidos": {"$sum": 1},
                    "total_gmv": {"$sum": "$calculated_gmv"},
                    "ticket_medio": {"$avg": "$calculated_gmv"}
                }},
                {"$sort": {"total_pedidos": -1}},
                {"$limit": 10}
            ]
            
            results = list(mongo_db.bookings.aggregate(pipeline))
            
            if results and len(results) > 0:
                answer = f"""
🤝 **Pedidos Totales por Partner** (Luda Mind)

📅 **Período:** {period}

📊 **Ranking de Partners:**
"""
                total_pedidos_global = 0
                total_gmv_global = 0
                
                for idx, partner_data in enumerate(results, 1):
                    partner_name = partner_data.get('_id', 'Unknown')
                    pedidos = partner_data.get('total_pedidos', 0)
                    gmv = partner_data.get('total_gmv', 0)
                    ticket = partner_data.get('ticket_medio', 0)
                    
                    total_pedidos_global += pedidos
                    total_gmv_global += gmv
                    
                    # Capitalizar nombres conocidos
                    if partner_name:
                        partner_display = partner_name.capitalize()
                        if 'glovo' in partner_name.lower():
                            partner_display = 'Glovo' if partner_name == 'glovo' else partner_name.replace('glovo', 'Glovo')
                        elif partner_name.lower() == 'uber':
                            partner_display = 'Uber'
                    
                    answer += f"\n**{idx}. {partner_display}**\n"
                    answer += f"• Pedidos: {pedidos:,}\n"
                    answer += f"• GMV: €{gmv:,.2f}\n"
                    answer += f"• Ticket medio: €{ticket:.2f}\n"
                
                answer += f"""

💰 **Totales:**
• Pedidos totales: {total_pedidos_global:,}
• GMV total: €{total_gmv_global:,.2f}
• Partners activos: {len(results)}

*Fuente: Luda Mind - MongoDB (modo Partners)*
                """
            else:
                answer = f"❌ No se encontraron pedidos de partners para {period}"
        
        elif 'gmv' in query_lower and 'total' in query_lower:
            # Total GMV - Separado en Ecommerce vs Shortage
            from datetime import datetime, timedelta
            
            # Determinar período
            if 'semana' in query_lower:
                date_filter = datetime.now() - timedelta(days=7)
                period = "esta semana"
            elif 'mes' in query_lower:
                date_filter = datetime.now() - timedelta(days=30)
                period = "este mes"
            else:
                date_filter = datetime.now() - timedelta(days=7)
                period = "últimos 7 días"
            
            # GMV Ecommerce (con thirdUser)
            pipeline_ecommerce = [
                {"$match": {
                    "thirdUser": {"$exists": True},
                    "createdDate": {"$gte": date_filter}
                }},
                {"$addFields": {
                    "calculated_gmv": {
                        "$cond": {
                            "if": {"$ifNull": ["$thirdUser.price", False]},
                            "then": {"$toDouble": {"$ifNull": ["$thirdUser.price", 0]}},
                            "else": {
                                "$reduce": {
                                    "input": "$items",
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {"$multiply": [
                                                {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                                {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                            ]}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }},
                {"$group": {
                    "_id": None,
                    "total_gmv": {"$sum": "$calculated_gmv"},
                    "count": {"$sum": 1}
                }}
            ]
            
            # GMV Shortage (con origin)
            pipeline_shortage = [
                {"$match": {
                    "origin": {"$exists": True},
                    "createdDate": {"$gte": date_filter}
                }},
                {"$addFields": {
                    "calculated_gmv": {
                        "$reduce": {
                            "input": "$items",
                            "initialValue": 0,
                            "in": {
                                "$add": [
                                    "$$value",
                                    {"$multiply": [
                                        {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                                        {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
                                    ]}
                                ]
                            }
                        }
                    }
                }},
                {"$group": {
                    "_id": None,
                    "total_gmv": {"$sum": "$calculated_gmv"},
                    "count": {"$sum": 1}
                }}
            ]

            result_ecommerce = list(mongo_db.bookings.aggregate(pipeline_ecommerce))
            result_shortage = list(mongo_db.bookings.aggregate(pipeline_shortage))

            if result_ecommerce or result_shortage:
                ecom_gmv = result_ecommerce[0].get('total_gmv', 0) if result_ecommerce else 0
                ecom_count = result_ecommerce[0].get('count', 0) if result_ecommerce else 0
                
                short_gmv = result_shortage[0].get('total_gmv', 0) if result_shortage else 0
                short_count = result_shortage[0].get('count', 0) if result_shortage else 0
                
                total_gmv = ecom_gmv + short_gmv
                total_count = ecom_count + short_count
                
                answer = f"""
🤝 **GMV Total del Sistema** (Luda Mind)

📅 **Período:** {period}

💰 **Ecommerce (Partners):**
• GMV: €{ecom_gmv:,.2f}
• Pedidos: {ecom_count:,}
• Ticket medio: €{(ecom_gmv / max(ecom_count, 1)):.2f}

🔄 **Shortage (Transferencias):**
• GMV: €{short_gmv:,.2f}
• Transferencias: {short_count:,}
• Ticket medio: €{(short_gmv / max(short_count, 1)):.2f}

📊 **TOTAL SISTEMA:**
• GMV Total: €{total_gmv:,.2f}
• Total operaciones: {total_count:,}
• Ticket medio global: €{(total_gmv / max(total_count, 1)):.2f}

*Fuente: Luda Mind - MongoDB (modo Partners)*
                """
            else:
                answer = f"❌ No se encontraron datos de GMV para {period}"

        else:
            # General partner info
            answer = """
🤝 **Análisis de Partners** (Luda Mind)

Partners disponibles:
• Glovo
• Uber
• Danone
• Hartmann
• Carrefour

💡 **Puedes consultar:**
• GMV por partner
• Comparación entre partners
• Evolución temporal
• Comisiones y rentabilidad

*Sistema: Luda Mind - Modo Partners*
                """

        return {
            'answer': answer,
            'database': 'mongodb',
            'confidence': 0.9
        }

    except Exception as e:
        logger.error(f"[Luda Mind] Partner query error: {e}")
        return {
            'answer': f"❌ Error procesando consulta: {str(e)[:100]}",
            'database': 'error',
            'confidence': 0.3
        }

def process_conversational_query(query: str) -> dict:
    """Process general conversational queries for Luda Mind."""

    answer = f"""
💬 **Luda Mind - Modo Conversacional**

Tu consulta: "{query[:100]}{"..." if len(query) > 100 else ""}"

Este modo permite consultas abiertas y análisis complejos que cruzan múltiples dimensiones.
    """

    # Try to provide some general insights
    if mysql_connected or mongodb_connected:
        answer += "\n\n📊 **Insights Disponibles (Luda Mind):**\n"

        if mongodb_connected:
            try:
                total_pharmacies = mongo_db.pharmacies.count_documents({})
                total_bookings = mongo_db.bookings.count_documents({})
                answer += f"• {total_pharmacies:,} farmacias registradas\n"
                answer += f"• {total_bookings:,} pedidos totales\n"
            except:
                pass

        if mysql_connected:
            answer += "• Análisis de ventas disponible\n"
            answer += "• Predicciones activas en Luda Mind\n"

    answer += "\n*Sistema: Luda Mind - IA para Consultas Inteligentes*"

    return {
        'answer': answer,
        'database': 'mixed',
        'confidence': 0.7
    }

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'system': 'Luda Mind',
        'architecture': 'clean_with_modes',
        'databases': {
            'mysql': mysql_connected,
            'mongodb': mongodb_connected
        },
        'sessions_active': len(sessions),
        'branding': 'Luda Mind',
        'version': '4.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/version')
def version():
    """Version information."""
    return jsonify({
        'name': 'Luda Mind',
        'tagline': 'Sistema Inteligente de Consultas de Datos',
        'version': '4.0.0',
        'color': '#41A837',
        'modes': ['pharmacy', 'product', 'partner', 'conversational'],
        'databases': {
            'mysql': mysql_connected,
            'mongodb': mongodb_connected
        },
        'architecture': 'Clean Architecture with SOLID principles'
    })

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  🚀 LUDA MIND - Sistema Inteligente de Consultas")
    print("="*70)
    print("\n✨ Características:")
    print("   - Nuevo branding: Luda Mind")
    print("   - Color corporativo: Verde (#41A837)")
    print("   - Logo: LUDA-LOGO-HOR-COLOR.svg")
    print("   - 4 Modos especializados en sidebar")
    print("   - Clean Architecture con principios SOLID")
    print(f"\n📊 Conexiones:")
    print(f"   - MySQL: {'✅ Conectado' if mysql_connected else '❌ No conectado'}")
    print(f"   - MongoDB: {'✅ Conectado' if mongodb_connected else '❌ No conectado'}")
    print("\n🌐 Acceso:")
    print("   http://localhost:5000")
    print("\n💚 Luda Mind - IA para tus datos farmacéuticos")
    print("="*70 + "\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )
