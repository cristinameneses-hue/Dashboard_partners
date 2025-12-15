#!/usr/bin/env python3
"""
Sistema de Mapeo Semántico para Luda Mind.
Relaciona palabras clave del usuario con campos de base de datos y su contexto.
"""

from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class FieldMapping:
    """Mapeo de un campo de base de datos con su contexto semántico."""
    field_path: str  # Ej: "thirdUser.user"
    collection: str  # Ej: "bookings"
    data_type: str   # Ej: "string", "number", "date"
    description: str  # Descripción de negocio
    keywords: List[str]  # Palabras clave relacionadas
    synonyms: List[str]  # Sinónimos
    examples: List[str]  # Ejemplos de valores
    aggregation_hints: List[str]  # Sugerencias de agregación


# ============================================================================
# MAPEO SEMÁNTICO DE MONGODB - LUDA MIND
# ============================================================================

SEMANTIC_MAPPINGS = {
    # ========================================================================
    # PARTNERS / CANALES
    # ========================================================================
    "partner": FieldMapping(
        field_path="thirdUser.user",
        collection="bookings",
        data_type="string",
        description="Identificador del partner o canal de venta (coincide con thirdUsers.idUser)",
        keywords=[
            "partner", "partners", "canal", "canales", "marketplace",
            "plataforma", "tercero", "intermediario", "distribuidor", "ecommerce"
        ],
        synonyms=[
            # PARTNERS ACTIVOS (12 verificados en thirdUsers por idUser)
            "uber",        # Uber - delivery
            "glovo",       # Glovo - delivery
            "glovo-otc",   # Glovo OTC
            "justeat",     # JustEat - delivery
            "danone",      # Danone - lab corporativo
            "procter",     # Procter & Gamble - lab
            "enna",        # Enna - lab
            "nordic",      # Nordic - lab
            "carrefour",   # Carrefour - retail
            "chiesi",      # Chiesi - lab
            "amazon",      # Amazon
            "ferrer"       # Ferrer - lab
        ],
        examples=["glovo", "uber", "justeat", "carrefour", "danone"],
        aggregation_hints=["$group by thirdUser.user", "$match con regex case-insensitive"]
    ),
    
    "partner_price": FieldMapping(
        field_path="thirdUser.price",
        collection="bookings",
        data_type="number",
        description="Precio o GMV (Gross Merchandise Value) del pedido del partner",
        keywords=[
            "precio", "gmv", "valor", "importe", "monto", "cantidad",
            "facturación", "ingreso", "revenue", "venta", "coste"
        ],
        synonyms=["gmv", "precio", "valor", "importe", "total"],
        examples=["19.50", "23.80", "40.18"],
        aggregation_hints=["$sum para total", "$avg para promedio"]
    ),
    
    # ========================================================================
    # FARMACIAS
    # ========================================================================
    "pharmacy_id": FieldMapping(
        field_path="_id",
        collection="pharmacies",
        data_type="objectid",
        description="ID único de la farmacia (ObjectId de MongoDB)",
        keywords=[
            "id", "identificador", "código de farmacia"
        ],
        synonyms=[],
        examples=["5a30f602c495ec99da3b2d77"],
        aggregation_hints=["Buscar por ObjectId cuando usuario pasa ID sin sentido semántico"]
    ),
    
    "pharmacy_name": FieldMapping(
        field_path="description",
        collection="pharmacies",
        data_type="string",
        description="Nombre comercial de la farmacia",
        keywords=[
            "farmacia", "farmacias", "botica", "boticas", "establecimiento",
            "punto de venta", "local", "sucursal", "tienda", "nombre"
        ],
        synonyms=["farmacia", "pharmacy", "botica", "droguería", "oficina de farmacia"],
        examples=["FARMACIA ISABEL CELADA", "FARMACIA ARAPILES"],
        aggregation_hints=["$regex case-insensitive para búsqueda parcial por nombre"]
    ),
    
    "pharmacy_city": FieldMapping(
        field_path="contact.city",
        collection="pharmacies",
        data_type="string",
        description="Ciudad donde está ubicada la farmacia",
        keywords=[
            "ciudad", "localidad", "municipio", "población",
            "ubicación", "lugar"
        ],
        synonyms=["madrid", "barcelona", "valencia", "sevilla", "bilbao"],
        examples=["Madrid", "Barcelona", "El Ejido"],
        aggregation_hints=["$group by contact.city para distribución geográfica"]
    ),

    "pharmacy_province": FieldMapping(
        field_path="contact.province",
        collection="pharmacies",
        data_type="string",
        description="Provincia donde está ubicada la farmacia",
        keywords=[
            "provincia", "provincias", "región", "zona", "área geográfica",
            "comunidad", "territorio"
        ],
        synonyms=[
            "madrid", "barcelona", "valencia", "castellón", "castellon",
            "alicante", "sevilla", "málaga", "murcia", "cádiz", "zaragoza"
        ],
        examples=["Madrid", "Barcelona", "Castellón", "Valencia", "Almería"],
        aggregation_hints=["$group by contact.province para distribución por provincias"]
    ),

    "pharmacy_postal_code": FieldMapping(
        field_path="contact.postalCode",
        collection="pharmacies",
        data_type="string",
        description="Código postal de la farmacia para búsquedas por zona",
        keywords=[
            "código postal", "cp", "zona postal", "postal"
        ],
        synonyms=["28001", "08001", "46001"],
        examples=["28010", "08080"],
        aggregation_hints=["Búsqueda exacta o por prefijo para zona"]
    ),
    
    "pharmacy_active": FieldMapping(
        field_path="active",
        collection="pharmacies",
        data_type="number",
        description="Indica si la farmacia está activa en el sistema (1=activa, 0=inactiva)",
        keywords=[
            "activa", "activas", "operativa", "funcionando",
            "en servicio", "disponible", "habilitada", "vigente"
        ],
        synonyms=["activa", "operativa", "funcionando"],
        examples=["1", "0"],
        aggregation_hints=["$match con {active: 1}"]
    ),
    
    "pharmacy_tags": FieldMapping(
        field_path="tags",
        collection="pharmacies",
        data_type="array",
        description="Array de tags que indican en qué partners/programas está activa la farmacia",
        keywords=[
            "en glovo", "en amazon", "en carrefour", "disponible en",
            "activa en", "partner", "con tiempo de respuesta", "2h", "48h"
        ],
        synonyms=[
            # Glovo
            "glovo", "glovo-otc",
            # Amazon
            "amazon",
            # Carrefour
            "carrefour",
            # Danone
            "danone",
            # Procter
            "procter",
            # Enna
            "enna",
            # Nordic
            "nordic",
            # Chiesi
            "chiesi",
            # Ferrer
            "ferrer"
        ],
        examples=["GLOVO", "AMAZON_2H", "CARREFOUR_48H"],
        aggregation_hints=[
            "Para buscar farmacias en partner: {tags: {$in: ['PARTNER_2H', 'PARTNER_48H']}}",
            "Si especifica tiempo: solo ese tag (GLOVO_2H o GLOVO_48H)",
            "Si NO especifica tiempo: incluir ambos (_2H y _48H)"
        ]
    ),
    
    # ========================================================================
    # PEDIDOS / BOOKINGS
    # ========================================================================
    "booking_date": FieldMapping(
        field_path="createdDate",
        collection="bookings",
        data_type="date",
        description="Fecha en que se creó el pedido",
        keywords=[
            "fecha", "día", "cuando", "momento", "tiempo",
            "período", "semana", "mes", "año", "hoy", "ayer",
            "reciente", "último", "pasado", "actual"
        ],
        synonyms=[
            "hoy", "ayer", "esta semana", "este mes", "este año",
            "últimos días", "últimas semanas", "reciente"
        ],
        examples=["2025-11-20", "2024-01-15"],
        aggregation_hints=["$match con $gte para rangos", "$dateToString para agrupar"]
    ),
    
    "booking_origin": FieldMapping(
        field_path="origin",
        collection="bookings",
        data_type="string",
        description="ID de farmacia origen - Si existe, el booking es SHORTAGE (transferencia interna)",
        keywords=[
            "shortage", "shortages", "transferencia", "interno",
            "entre farmacias", "traspaso"
        ],
        synonyms=["shortage", "transferencia", "traspaso"],
        examples=["5a30f602c495ec99da3b2d77"],
        aggregation_hints=["$match con {origin: {$exists: true}} para detectar shortages"]
    ),
    
    "booking_target": FieldMapping(
        field_path="target",
        collection="bookings",
        data_type="string",
        description="ID de farmacia destino del pedido (pharmacyId como string)",
        keywords=[
            "destino", "farmacia destino", "para farmacia"
        ],
        synonyms=[],
        examples=["652e45c26e6923eeef7bd1ef"],
        aggregation_hints=["Filtrar por farmacia destino, separar por partner si aplica"]
    ),
    
    "booking_state": FieldMapping(
        field_path="state",
        collection="bookings",
        data_type="string",
        description="Estado del pedido (ID de referencia)",
        keywords=[
            "estado", "status", "situación", "fase", "etapa"
        ],
        synonyms=["finalizado", "pendiente", "en proceso", "cancelado"],
        examples=["5a54c4dab2948c860f00000b"],
        aggregation_hints=["Unir con collection de states para descripción"]
    ),
    
    "booking_items": FieldMapping(
        field_path="items",
        collection="bookings",
        data_type="array",
        description="Lista de productos incluidos en el pedido",
        keywords=[
            "productos", "items", "artículos", "referencias",
            "medicamentos", "contenido", "comprados"
        ],
        synonyms=["productos", "items", "artículos", "medicamentos"],
        examples=["[{product_id: '123', quantity: 2}]"],
        aggregation_hints=["$unwind para expandir array", "$size para contar"]
    ),
    
    # ========================================================================
    # PRODUCTOS
    # ========================================================================
    "product_description": FieldMapping(
        field_path="description",
        collection="items",
        data_type="string",
        description="Nombre/descripción del producto o medicamento",
        keywords=[
            "producto", "productos", "medicamento", "medicina",
            "fármaco", "artículo", "item", "nombre", "descripción"
        ],
        synonyms=["ibuprofeno", "paracetamol", "omeprazol", "natalben", "ozempic"],
        examples=["NATALBEN SUPRA 30 CAPSULAS", "FISIOGEN FERRO FORTE"],
        aggregation_hints=["$regex case-insensitive con {$options: 'i'} para búsqueda flexible"]
    ),
    
    "product_code": FieldMapping(
        field_path="code",
        collection="items",
        data_type="string",
        description="Código nacional del producto (6 dígitos, puede tener ceros a la izquierda)",
        keywords=[
            "código nacional", "cn", "código", "code", "referencia"
        ],
        synonyms=["cn", "codigo", "código nacional"],
        examples=["154653", "174511", "001234"],
        aggregation_hints=["Búsqueda exacta como STRING (mantener ceros a la izquierda)"]
    ),
    
    "product_ean": FieldMapping(
        field_path="ean13",
        collection="items",
        data_type="string",
        description="Código EAN-13 (código de barras) del producto (13 dígitos)",
        keywords=[
            "ean", "ean13", "código de barras", "barcode"
        ],
        synonyms=["ean", "código de barras", "barcode"],
        examples=["8470001546531", "8470001745118"],
        aggregation_hints=["Búsqueda exacta por EAN como STRING"]
    ),
    
    "product_type": FieldMapping(
        field_path="itemType",
        collection="items",
        data_type="number",
        description="Tipo de producto: 3=Parafarmacia, otro valor=Medicamento",
        keywords=[
            "tipo", "categoría", "parafarmacia", "medicamento",
            "medicina", "categorizar"
        ],
        synonyms=["parafarmacia", "medicamento", "medicina"],
        examples=["3 (parafarmacia)", "1 (medicamento)"],
        aggregation_hints=["$match con {itemType: 3} para parafarmacia"]
    ),
    
    "product_active": FieldMapping(
        field_path="active",
        collection="items",
        data_type="number",
        description="Indica si el producto está activo en el catálogo (1=activo, 0=inactivo)",
        keywords=[
            "activo", "disponible", "vigente", "habilitado",
            "en catálogo", "vendible"
        ],
        synonyms=["activo", "disponible", "vigente"],
        examples=["1", "0"],
        aggregation_hints=["$match con {active: 1} para productos activos"]
    ),
    
    # ========================================================================
    # STOCK / INVENTARIO
    # ========================================================================
    "stock_quantity": FieldMapping(
        field_path="quantity",
        collection="stockItems",
        data_type="number",
        description="Cantidad disponible en stock en una farmacia específica",
        keywords=[
            "stock", "inventario", "cantidad", "disponibilidad",
            "existencias", "unidades", "disponible", "quedan"
        ],
        synonyms=["stock", "inventario", "existencias", "disponible"],
        examples=["2", "5", "0"],
        aggregation_hints=["$sum para total en todas farmacias", "filtrar quantity > 0"]
    ),
    
    "stock_pvp": FieldMapping(
        field_path="pvp",
        collection="stockItems",
        data_type="number",
        description="Precio Venta Público (lo que paga el cliente) - varía por farmacia",
        keywords=[
            "precio", "pvp", "precio público", "precio venta",
            "coste", "valor", "caro", "barato"
        ],
        synonyms=["precio", "pvp", "precio público"],
        examples=["20.00", "14.50", "8.52"],
        aggregation_hints=["Moda por defecto, $avg/$min/$max si se especifica"]
    ),
    
    "stock_pva": FieldMapping(
        field_path="pva",
        collection="stockItems",
        data_type="number",
        description="Precio Venta Almacén (coste para farmacia) - solo si usuario lo pide explícitamente",
        keywords=[
            "pva", "precio almacén", "coste farmacia", "precio compra"
        ],
        synonyms=["pva", "precio almacén"],
        examples=["14.48", "10.20"],
        aggregation_hints=["Solo usar si usuario pide explícitamente PVA"]
    ),
    
    "stock_pharmacy_id": FieldMapping(
        field_path="pharmacyId",
        collection="stockItems",
        data_type="string",
        description="ID de la farmacia (STRING, no ObjectId) que tiene este stock",
        keywords=["farmacia", "establecimiento"],
        synonyms=[],
        examples=["5c41b4ead37e740b0fe3f89a"],
        aggregation_hints=["Relacionar con pharmacies._id (convertir a string)"]
    ),
    
    "stock_item_id": FieldMapping(
        field_path="itemId",
        collection="stockItems",
        data_type="string",
        description="ID del producto (STRING, no ObjectId) en stock",
        keywords=["producto", "item"],
        synonyms=[],
        examples=["5ab0d643915854234881255f"],
        aggregation_hints=["Relacionar con items._id (convertir a string)"]
    ),
    
    # ========================================================================
    # MÉTRICAS CALCULADAS
    # ========================================================================
    "ticket_medio": FieldMapping(
        field_path="calculated",
        collection="bookings",
        data_type="calculated",
        description="Promedio del valor de pedidos (GMV / número de pedidos)",
        keywords=[
            "ticket medio", "promedio", "media", "average",
            "ticket promedio", "valor medio", "gasto medio"
        ],
        synonyms=["ticket medio", "promedio", "average"],
        examples=["19.50", "23.80"],
        aggregation_hints=["$avg de thirdUser.price"]
    ),
    
    "total": FieldMapping(
        field_path="calculated",
        collection="any",
        data_type="calculated",
        description="Suma total de valores",
        keywords=[
            "total", "suma", "sumar", "acumulado", "global",
            "conjunto", "completo", "todos", "totales"
        ],
        synonyms=["total", "suma", "global", "acumulado"],
        examples=["1000", "50000"],
        aggregation_hints=["$sum"]
    ),
    
    "conteo": FieldMapping(
        field_path="calculated",
        collection="any",
        data_type="calculated",
        description="Número de documentos o registros",
        keywords=[
            "cuántos", "cuántas", "número", "cantidad", "conteo",
            "count", "total de", "hay", "existen"
        ],
        synonyms=["cuántos", "número", "cantidad", "count"],
        examples=["100", "1500"],
        aggregation_hints=["$count o $sum: 1"]
    )
}


# ============================================================================
# CONTEXTO DE NEGOCIO
# ============================================================================

BUSINESS_CONTEXT = {
    "partners": """
    Los partners (ecommerce) son canales de venta terceros que generan pedidos.
    
    PARTNERS ACTIVOS (12 verificados):
    
    DELIVERY/MARKETPLACE:
    - glovo: Mayor volumen de pedidos
    - glovo-otc: Glovo OTC
    - uber: Segundo mayor partner de delivery
    - justeat: JustEat delivery
    - amazon: Amazon marketplace
    - carrefour: Carrefour retail
    
    LABS CORPORATIVOS:
    - danone: Danone lab
    - procter: Procter & Gamble
    - enna: Enna lab
    - nordic: Nordic lab
    - chiesi: Chiesi lab
    - ferrer: Ferrer lab
    
    CAMPOS CLAVE:
    - thirdUser.user: Nombre del partner (coincide exactamente con thirdUsers.idUser)
    - thirdUser.price: GMV del pedido (si existe)
    - Si NO tiene thirdUser.price: GMV = sum(items[].pvp * items[].quantity)
    
    IDENTIFICACIÓN:
    - Booking con thirdUser = pedido de partner (ecommerce)
    - Booking con origin = shortage (transferencia interna)
    - GMV TOTAL = separar ecommerce vs shortage
    
    NOTA: Solo estos 12 partners están actualmente operativos.
    """,
    
    "pharmacies": """
    Las farmacias son los establecimientos farmacéuticos.
    
    CAMPOS IMPORTANTES:
    - _id: ObjectId único (usar para relacionar con otras tablas como pharmacyId)
    - description: Nombre comercial de la farmacia
    - contact.city: Ciudad
    - contact.postalCode: CP para búsquedas por zona
    - contact.address: Dirección completa
    - active: 1=activa, 0=inactiva
    - tags: Array de strings que indica en qué partners está activa
    
    IDENTIFICACIÓN POR USUARIO:
    - Si parece ID (varchar sin sentido) → buscar por _id
    - Si es nombre legible (ej: "FARMACIA ISABEL") → buscar por description (regex)
    - Si no encuentra por nombre → pedir ID al usuario
    
    FARMACIAS ACTIVAS EN PARTNERS:
    
    PARA PARTNERS CON TAGS (Glovo, Amazon, Carrefour, Danone, Procter, Enna, Nordic, Chiesi, Ferrer):
    - Buscar en campo tags con el nombre del partner
    - Tags tienen sufijos _2H (entrega 2 horas) y _48H (entrega 48 horas)
    - Si NO especifica tiempo de respuesta: incluir ambos {tags: {$in: ["PARTNER_2H", "PARTNER_48H"]}}
    - Si especifica "2h" o "2 horas": solo {tags: "PARTNER_2H"}
    - Si especifica "48h": solo {tags: "PARTNER_48H"}
    - También hay _BACKUP (farmacias backup, incluir si no especifica tiempo)
    
    Ejemplos de tags:
    - GLOVO (1,105 farmacias) - Sin sufijo
    - GLOVO-OTC_2H, GLOVO-OTC_48H (44 farmacias)
    - AMAZON_2H, AMAZON_48H (59 farmacias)
    - CARREFOUR_2H, CARREFOUR_48H (305 farmacias)
    - PROCTER_2H, PROCTER_48H (2,035 farmacias)
    - DANONE_2H, DANONE_48H (650 farmacias)
    - ENNA_2H, ENNA_48H (651 farmacias)
    - NORDIC_2H, NORDIC_48H (38 farmacias)
    - CHIESI_48H, CHIESI_BACKUP (79 farmacias)
    - FERRER_2H, FERRER_48H (16 farmacias)
    
    PARA PARTNERS SIN TAGS (Uber, Justeat):
    - NO usar tags (no existen)
    - CRITERIO DE ACTIVA: Farmacia con pedidos del partner en el período consultado
    - Buscar farmacias únicas en bookings con thirdUser.user = "uber" o "justeat"
    - Agrupar por target (farmacia destino) para obtener farmacias únicas
    - Filtrar por createdDate según período de la consulta:
      * "esta semana" → últimos 7 días
      * "este mes" → últimos 30 días  
      * Sin especificar período → asumir últimos 7 días
    - Ejemplo query: db.bookings.aggregate([{$match: {thirdUser.user: "uber", createdDate: {$gte: fecha}}}, {$group: {_id: "$target"}}])
    
    IGNORAR:
    - NUTRIBEN_* (no es partner activo)
    - Tags de campañas: envio-enero, envio-covid, mascarillas
    - Tags técnicos: test, SinInstalaciones, updateNotif*, TRENDS
    
    Para pedidos de farmacia: usar bookings.target (farmacia destino).
    """,
    
    "products": """
    Los productos son medicamentos y artículos de parafarmacia.
    Colección 'items' contiene el catálogo.
    
    CAMPOS CLAVE:
    - description: Nombre del producto
    - code: Código nacional (6 dígitos, STRING con ceros a la izquierda)
    - ean13: Código EAN (13 dígitos, STRING)
    - active: 1=activo, 0=inactivo
    - itemType: 3=Parafarmacia, otro=Medicamento
    
    CLAVES PRIMARIAS: code y ean13 (NO usar _id para búsquedas de usuario)
    
    IDENTIFICACIÓN POR USUARIO:
    - Texto libre (ej: "ozempic") → buscar en description con regex case-insensitive
    - 6 dígitos (ej: "154653") → buscar en code (como STRING)
    - 13 dígitos (ej: "8470001546531") → buscar en ean13 (como STRING)
    
    Si encuentra múltiples: mostrar lista con description + code y pedir que elija.
    
    PRECIOS: NO están en items, están en stockItems (pvp/pva).
    Para consultar precio: items → obtener _id → buscar en stockItems.itemId (como string).
    
    DATOS DE VENTAS (sell in/sell out): usar MySQL, NO MongoDB.
    """,
    
    "bookings": """
    Los bookings son pedidos de productos.
    
    TIPOS DE BOOKINGS:
    1. PEDIDOS DE PARTNERS (ecommerce):
       - Tienen thirdUser.user (nombre del partner)
       - GMV = **SIEMPRE** sum(items[].pvp * items[].quantity)
       - Iterar cada item en el array items[]
       - Multiplicar pvp * quantity de cada item
       - Sumar todos los resultados
    
    2. SHORTAGES (transferencias internas):
       - Tienen origin (farmacia origen)
       - NO tienen thirdUser
       - Son movimientos entre farmacias (uso interno)
       - GMV = sum(items[].pvp * items[].quantity)
    
    CAMPOS:
    - createdDate: Fecha del pedido (**SIEMPRE** usar createdDate, NO createdAt)
    - target: Farmacia destino (como string, relacionar con pharmacies._id)
    - origin: Farmacia origen (si existe = shortage)
    - items[]: Array de productos con pvp, quantity, code, ean13, description
    - thirdUser.user: Partner (si es pedido ecommerce)
    
    REGLA GMV ESTÁNDAR (CRÍTICO):
    **SIEMPRE calcular GMV desde items.pvp * items.quantity**
    - Pipeline MongoDB: usar $reduce o $map + $sum
    - Asegurar conversión: $toDouble para pvp, $toInt para quantity
    - Usar $ifNull para manejar valores null: {$ifNull: ["$$item.pvp", 0]}
    
    Ejemplo pipeline:
    {
      "$reduce": {
        "input": "$items",
        "initialValue": 0,
        "in": {
          "$add": [
            "$$value",
            {
              "$multiply": [
                {"$toDouble": {"$ifNull": ["$$this.pvp", 0]}},
                {"$toInt": {"$ifNull": ["$$this.quantity", 0]}}
              ]
            }
          ]
        }
      }
    }
    """,
    
    "temporal_analysis": """
    Para análisis temporal usar createdDate:
    - "hoy" = desde las 00:00 de hoy
    - "ayer" = desde las 00:00 de ayer
    - "esta semana" = últimos 7 días
    - "este mes" = últimos 30 días
    - "mes pasado" = de 60 a 30 días atrás
    
    Usar $gte con createdDate para filtros temporales.
    """
}


# ============================================================================
# PATTERNS DE AGREGACIÓN COMUNES
# ============================================================================

AGGREGATION_PATTERNS = {
    "count_by_field": {
        "description": "Contar documentos agrupados por un campo",
        "pattern": [
            {"$group": {"_id": "$FIELD", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ],
        "keywords": ["cuántos", "cantidad", "número", "count", "por"]
    },
    
    "sum_by_field": {
        "description": "Sumar valores agrupados por un campo",
        "pattern": [
            {"$group": {"_id": "$GROUP_FIELD", "total": {"$sum": "$VALUE_FIELD"}}},
            {"$sort": {"total": -1}}
        ],
        "keywords": ["total", "suma", "sumar", "por"]
    },
    
    "average_by_field": {
        "description": "Calcular promedio agrupado por un campo",
        "pattern": [
            {"$group": {"_id": "$GROUP_FIELD", "avg": {"$avg": "$VALUE_FIELD"}}}
        ],
        "keywords": ["promedio", "media", "average", "ticket medio"]
    },
    
    "top_n": {
        "description": "Obtener los N primeros resultados",
        "pattern": [
            {"$sort": {"FIELD": -1}},
            {"$limit": 10}
        ],
        "keywords": ["top", "mejores", "principales", "más", "mayor"]
    },
    
    "time_range": {
        "description": "Filtrar por rango de fechas",
        "pattern": [
            {"$match": {"createdDate": {"$gte": "DATE"}}}
        ],
        "keywords": ["desde", "hasta", "entre", "periodo", "fecha"]
    }
}


# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def find_field_mappings(query: str) -> List[FieldMapping]:
    """
    Encuentra los campos de BD relacionados con las palabras en la query.
    
    Args:
        query: Query del usuario en lenguaje natural
        
    Returns:
        Lista de FieldMapping relevantes
    """
    query_lower = query.lower()
    relevant_mappings = []
    
    for field_name, mapping in SEMANTIC_MAPPINGS.items():
        # Buscar keywords
        if any(keyword in query_lower for keyword in mapping.keywords):
            relevant_mappings.append(mapping)
            continue
        
        # Buscar synonyms
        if any(synonym in query_lower for synonym in mapping.synonyms):
            relevant_mappings.append(mapping)
    
    return relevant_mappings


def get_business_context(mapping: FieldMapping) -> str:
    """
    Obtiene el contexto de negocio relevante para un campo.
    
    Args:
        mapping: FieldMapping del campo
        
    Returns:
        Contexto de negocio relacionado
    """
    if "partner" in mapping.field_path or mapping.collection == "bookings":
        return BUSINESS_CONTEXT.get("partners", "") + "\n" + BUSINESS_CONTEXT.get("bookings", "")
    
    if mapping.collection == "pharmacies":
        return BUSINESS_CONTEXT.get("pharmacies", "")
    
    if mapping.collection == "items":
        return BUSINESS_CONTEXT.get("products", "")
    
    return ""


def suggest_aggregation_pattern(query: str) -> Dict[str, Any]:
    """
    Sugiere un pattern de agregación basado en la query.
    
    Args:
        query: Query del usuario
        
    Returns:
        Pattern de agregación sugerido
    """
    query_lower = query.lower()
    
    for pattern_name, pattern_info in AGGREGATION_PATTERNS.items():
        if any(keyword in query_lower for keyword in pattern_info["keywords"]):
            return {
                "pattern_name": pattern_name,
                "description": pattern_info["description"],
                "template": pattern_info["pattern"]
            }
    
    return {}


def get_context_for_mode(mode: str) -> str:
    """
    Obtiene el contexto de negocio correcto según el modo.

    Mapea correctamente los modos a las claves de BUSINESS_CONTEXT:
    - partner → partners
    - pharmacy → pharmacies
    - product → products
    - booking → bookings
    - conversational → partners + bookings + pharmacies

    Args:
        mode: Modo activo (partner, pharmacy, product, booking, conversational)

    Returns:
        Contexto de negocio relevante
    """
    # Mapeo de modos a claves de BUSINESS_CONTEXT
    mode_to_context = {
        'partner': ['partners', 'bookings'],
        'partners': ['partners', 'bookings'],
        'pharmacy': ['pharmacies'],
        'pharmacies': ['pharmacies'],
        'product': ['products'],
        'products': ['products'],
        'booking': ['bookings', 'partners'],
        'bookings': ['bookings', 'partners'],
        'conversational': ['partners', 'bookings', 'pharmacies', 'products'],
        'stock': ['products'],
        'temporal_analysis': ['bookings', 'temporal_analysis']
    }

    # Obtener las claves de contexto para el modo
    context_keys = mode_to_context.get(mode.lower(), ['bookings', 'partners'])

    # Construir el contexto combinado
    context_parts = []
    for key in context_keys:
        ctx = BUSINESS_CONTEXT.get(key, '')
        if ctx:
            context_parts.append(ctx.strip())

    return '\n\n'.join(context_parts)


def build_context_for_llm(query: str) -> str:
    """
    Construye un contexto rico para el LLM con mappings y contexto de negocio.

    Args:
        query: Query del usuario

    Returns:
        Contexto estructurado para el LLM
    """
    mappings = find_field_mappings(query)
    pattern = suggest_aggregation_pattern(query)
    
    context = f"# Contexto para Query: '{query}'\n\n"
    
    if mappings:
        context += "## Campos Relevantes de MongoDB:\n\n"
        for mapping in mappings[:5]:  # Top 5 más relevantes
            context += f"### {mapping.field_path} ({mapping.collection})\n"
            context += f"**Descripción:** {mapping.description}\n"
            context += f"**Tipo:** {mapping.data_type}\n"
            context += f"**Ejemplos:** {', '.join(mapping.examples[:3])}\n"
            context += f"**Agregación:** {', '.join(mapping.aggregation_hints)}\n\n"
            
            business_ctx = get_business_context(mapping)
            if business_ctx:
                context += f"**Contexto de Negocio:**\n{business_ctx}\n\n"
    
    if pattern:
        context += f"## Pattern de Agregación Sugerido:\n"
        context += f"**{pattern['pattern_name']}:** {pattern['description']}\n\n"
    
    context += "## Instrucciones:\n"
    context += "1. Usa los campos indicados para construir la query MongoDB\n"
    context += "2. Aplica el pattern de agregación sugerido si es relevante\n"
    context += "3. Considera el contexto de negocio para interpretar correctamente\n"
    context += "4. Si falta información, infiere el intent más probable\n"
    
    return context

