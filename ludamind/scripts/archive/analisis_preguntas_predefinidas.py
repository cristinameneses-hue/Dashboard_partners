"""
Análisis de preguntas predefinidas - Hardcoded vs GPT
Comparamos el esquema fijo con la interpretación de GPT
"""
import os
import sys
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

# Asegurar que podemos importar los módulos del dominio
sys.path.insert(0, os.path.dirname(__file__))

from domain.services.query_interpreter import QueryInterpreter

# ============================================================================
# PREGUNTAS PREDEFINIDAS POR MODO
# ============================================================================

PREGUNTAS_POR_MODO = {
    "pharmacy": [
        "¿Cuántas farmacias activas tenemos?",
        "Farmacias activas en {ciudad}",
        "GMV total de la farmacia {farmacia_id}",
        "GMV de {farmacia_id} en la última semana",
        "Pedidos de {farmacia_id} en {partner}",
        "Top 10 farmacias que más venden",
        "Top 10 farmacias en {partner}",
        "Farmacias con más de {cantidad} pedidos esta semana",
    ],
    
    "product": [
        "¿Cuántos productos activos tenemos?",
        "Stock de {producto} (por code o ean13)",
        "Precio PVP de {producto}",
        "¿Qué farmacias tienen {producto} en stock?",
        "Productos más vendidos esta semana",
        "Top 10 productos por GMV",
        "Productos de parafarmacia (itemType = 3)",
        "Medicamentos más demandados",
    ],
    
    "partner": [
        "GMV total de {partner}",
        "GMV de {partner} esta semana",
        "Pedidos totales por partner",
        "Top 10 partners por GMV",
        "Farmacias activas en {partner}",
        "GMV promedio por pedido en {partner}",
        "Evolución de pedidos de {partner} (últimos 7 días)",
        "Partners con más crecimiento",
    ]
}

# ============================================================================
# ESQUEMAS HARDCODEADOS
# ============================================================================

def get_hardcoded_schema(query_type: str, params: dict = None) -> dict:
    """
    Devuelve el esquema hardcodeado para cada tipo de pregunta.
    params contiene las variables: farmacia_id, producto, partner, ciudad, cantidad, etc.
    """
    params = params or {}
    
    # Calcular fechas
    fecha_hoy = datetime.now()
    fecha_semana_pasada = fecha_hoy - timedelta(days=7)
    
    schemas = {
        # ========== PHARMACY QUERIES ==========
        "farmacias_activas_total": {
            "collection": "pharmacies",
            "pipeline": [
                {"$match": {"active": 1}},
                {"$count": "total"}
            ],
            "explanation": "Cuenta todas las farmacias con active=1",
            "variables": []
        },
        
        "farmacias_activas_ciudad": {
            "collection": "pharmacies",
            "pipeline": [
                {"$match": {"active": 1, "contact.city": "{ciudad}"}},
                {"$project": {"description": 1, "contact.city": 1, "contact.postalCode": 1}}
            ],
            "explanation": "Lista farmacias activas en una ciudad específica",
            "variables": ["ciudad"]
        },
        
        "gmv_farmacia_total": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {"target": "{farmacia_id}"}},
                {"$group": {
                    "_id": None,
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }}
            ],
            "explanation": "Calcula GMV total histórico de una farmacia usando cálculo híbrido",
            "variables": ["farmacia_id"]
        },
        
        "gmv_farmacia_periodo": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {
                    "target": "{farmacia_id}",
                    "createdAt": {"$gte": "{fecha_inicio}", "$lte": "{fecha_fin}"}
                }},
                {"$group": {
                    "_id": None,
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }}
            ],
            "explanation": "GMV de farmacia en un período específico",
            "variables": ["farmacia_id", "fecha_inicio", "fecha_fin"]
        },
        
        "pedidos_farmacia_partner": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {
                    "target": "{farmacia_id}",
                    "thirdUser.user": "{partner}"
                }},
                {"$group": {
                    "_id": None,
                    "totalPedidos": {"$sum": 1},
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }}
            ],
            "explanation": "Pedidos y GMV de una farmacia en un partner específico",
            "variables": ["farmacia_id", "partner"]
        },
        
        "top_farmacias_gmv": {
            "collection": "bookings",
            "pipeline": [
                {"$group": {
                    "_id": "$target",
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }},
                {"$sort": {"totalGMV": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "pharmacies",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "pharmacy_info"
                }}
            ],
            "explanation": "Top 10 farmacias por GMV total (histórico)",
            "variables": []
        },
        
        "top_farmacias_partner": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {"thirdUser.user": "{partner}"}},
                {"$group": {
                    "_id": "$target",
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }},
                {"$sort": {"totalGMV": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "pharmacies",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "pharmacy_info"
                }}
            ],
            "explanation": "Top 10 farmacias en un partner específico",
            "variables": ["partner"]
        },
        
        # ========== PRODUCT QUERIES ==========
        "productos_activos_total": {
            "collection": "items",
            "pipeline": [
                {"$match": {"active": 1}},
                {"$count": "total"}
            ],
            "explanation": "Cuenta todos los productos activos",
            "variables": []
        },
        
        "stock_producto": {
            "collection": "stockItems",
            "pipeline": [
                {"$match": {"code": "{producto_code}"}},
                {"$lookup": {
                    "from": "pharmacies",
                    "localField": "target",
                    "foreignField": "_id",
                    "as": "pharmacy_info"
                }},
                {"$project": {
                    "target": 1,
                    "quantity": 1,
                    "pvp": 1,
                    "pva": 1,
                    "pharmacy_name": {"$arrayElemAt": ["$pharmacy_info.description", 0]}
                }}
            ],
            "explanation": "Stock de un producto por código nacional (code)",
            "variables": ["producto_code"]
        },
        
        "precio_producto": {
            "collection": "stockItems",
            "pipeline": [
                {"$match": {"code": "{producto_code}"}},
                {"$group": {
                    "_id": None,
                    "pvp_moda": {"$first": "$pvp"},
                    "pvp_min": {"$min": "$pvp"},
                    "pvp_max": {"$max": "$pvp"},
                    "pvp_promedio": {"$avg": "$pvp"}
                }}
            ],
            "explanation": "Estadísticas de precios PVP de un producto",
            "variables": ["producto_code"]
        },
        
        "farmacias_con_stock": {
            "collection": "stockItems",
            "pipeline": [
                {"$match": {"code": "{producto_code}", "quantity": {"$gt": 0}}},
                {"$lookup": {
                    "from": "pharmacies",
                    "localField": "target",
                    "foreignField": "_id",
                    "as": "pharmacy_info"
                }},
                {"$project": {
                    "pharmacy_id": "$target",
                    "quantity": 1,
                    "pvp": 1,
                    "pharmacy_name": {"$arrayElemAt": ["$pharmacy_info.description", 0]},
                    "pharmacy_city": {"$arrayElemAt": ["$pharmacy_info.contact.city", 0]}
                }}
            ],
            "explanation": "Farmacias que tienen stock de un producto",
            "variables": ["producto_code"]
        },
        
        "top_productos_vendidos": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {"createdAt": {"$gte": "{fecha_inicio}"}}},
                {"$unwind": "$items"},
                {"$group": {
                    "_id": "$items.code",
                    "totalVendido": {"$sum": "$items.quantity"},
                    "totalPedidos": {"$sum": 1},
                    "gmvTotal": {
                        "$sum": {"$multiply": ["$items.pvp", "$items.quantity"]}
                    }
                }},
                {"$sort": {"totalVendido": -1}},
                {"$limit": 10},
                {"$lookup": {
                    "from": "items",
                    "localField": "_id",
                    "foreignField": "code",
                    "as": "product_info"
                }}
            ],
            "explanation": "Top 10 productos más vendidos en un período",
            "variables": ["fecha_inicio"]
        },
        
        # ========== PARTNER QUERIES ==========
        "gmv_partner_total": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {"thirdUser.user": "{partner}"}},
                {"$group": {
                    "_id": None,
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }}
            ],
            "explanation": "GMV total histórico de un partner",
            "variables": ["partner"]
        },
        
        "gmv_partner_periodo": {
            "collection": "bookings",
            "pipeline": [
                {"$match": {
                    "thirdUser.user": "{partner}",
                    "createdAt": {"$gte": "{fecha_inicio}", "$lte": "{fecha_fin}"}
                }},
                {"$group": {
                    "_id": None,
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }}
            ],
            "explanation": "GMV de partner en un período específico",
            "variables": ["partner", "fecha_inicio", "fecha_fin"]
        },
        
        "pedidos_por_partner": {
            "collection": "bookings",
            "pipeline": [
                {"$group": {
                    "_id": "$thirdUser.user",
                    "totalPedidos": {"$sum": 1},
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "ticketPromedio": {"$avg": "$thirdUser.price"}
                }},
                {"$sort": {"totalPedidos": -1}}
            ],
            "explanation": "Ranking de todos los partners por número de pedidos",
            "variables": []
        },
        
        "top_partners_gmv": {
            "collection": "bookings",
            "pipeline": [
                {"$group": {
                    "_id": "$thirdUser.user",
                    "totalGMV": {
                        "$sum": {
                            "$cond": {
                                "if": {"$gt": ["$thirdUser.price", None]},
                                "then": "$thirdUser.price",
                                "else": {
                                    "$sum": {
                                        "$map": {
                                            "input": "$items",
                                            "as": "item",
                                            "in": {"$multiply": ["$$item.pvp", "$$item.quantity"]}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "totalPedidos": {"$sum": 1}
                }},
                {"$sort": {"totalGMV": -1}},
                {"$limit": 10}
            ],
            "explanation": "Top 10 partners por GMV",
            "variables": []
        },
        
        "farmacias_activas_partner": {
            "collection": "pharmacies",
            "pipeline": [
                {"$match": {"active": 1, "tags": "{partner_tag}"}},
                {"$project": {"description": 1, "contact.city": 1, "tags": 1}}
            ],
            "explanation": "Farmacias activas en un partner (usando tags)",
            "variables": ["partner_tag"]
        },
    }
    
    return schemas.get(query_type, {})


def main():
    """Análisis completo de preguntas predefinidas"""
    
    print("\n" + "="*100)
    print("📋 ANÁLISIS DE PREGUNTAS PREDEFINIDAS - HARDCODED vs GPT")
    print("="*100)
    
    # Inicializar QueryInterpreter
    print("\n🔧 Inicializando QueryInterpreter para comparación con GPT...")
    interpreter = QueryInterpreter(openai_api_key=os.getenv('OPENAI_API_KEY'))
    
    if not interpreter.available:
        print("⚠️  GPT no disponible, solo mostraré esquemas hardcodeados")
    
    # Analizar cada modo
    for modo, preguntas in PREGUNTAS_POR_MODO.items():
        print("\n" + "="*100)
        print(f"📂 MODO: {modo.upper()}")
        print("="*100)
        
        for i, pregunta in enumerate(preguntas, 1):
            print(f"\n{'─'*100}")
            print(f"❓ PREGUNTA {i}: {pregunta}")
            print(f"{'─'*100}")
            
            # Determinar query_type basado en la pregunta
            query_type = detectar_query_type(pregunta, modo)
            
            # 1. Mostrar esquema hardcodeado
            print("\n🔹 ESQUEMA HARDCODEADO:")
            schema = get_hardcoded_schema(query_type)
            if schema:
                print(f"   Colección: {schema['collection']}")
                print(f"   Variables: {schema['variables']}")
                print(f"   Explicación: {schema['explanation']}")
                print(f"\n   Pipeline:")
                print(json.dumps(schema['pipeline'], indent=6, ensure_ascii=False))
            else:
                print(f"   ⚠️  No hay esquema definido para: {query_type}")
            
            # 2. Comparar con interpretación de GPT
            if interpreter.available:
                print(f"\n🔹 INTERPRETACIÓN GPT:")
                try:
                    result = interpreter.interpret_query(pregunta, modo)
                    
                    if result.get('error'):
                        print(f"   ❌ Error: {result['error']}")
                    else:
                        print(f"   Colección: {result.get('collection', 'N/A')}")
                        print(f"   Explicación: {result.get('explanation', 'N/A')}")
                        print(f"\n   Pipeline GPT:")
                        print(json.dumps(result.get('pipeline', []), indent=6, ensure_ascii=False))
                        
                        # Comparar similitud
                        if schema:
                            similitud = comparar_pipelines(schema['pipeline'], result.get('pipeline', []))
                            print(f"\n   📊 Similitud: {similitud}%")
                            if similitud >= 80:
                                print("   ✅ GPT genera query muy similar al hardcoded")
                            elif similitud >= 60:
                                print("   ⚠️  GPT genera query similar pero con diferencias")
                            else:
                                print("   ❌ GPT genera query diferente, revisar")
                
                except Exception as e:
                    print(f"   ❌ Error al interpretar: {str(e)}")
    
    print("\n" + "="*100)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*100 + "\n")


def detectar_query_type(pregunta: str, modo: str) -> str:
    """Detecta el tipo de query basado en keywords"""
    pregunta_lower = pregunta.lower()
    
    # Pharmacy queries
    if "cuántas farmacias activas" in pregunta_lower and "ciudad" not in pregunta_lower:
        return "farmacias_activas_total"
    if "farmacias activas en" in pregunta_lower or "{ciudad}" in pregunta:
        return "farmacias_activas_ciudad"
    if "gmv total de la farmacia" in pregunta_lower or ("gmv de" in pregunta_lower and "última semana" not in pregunta_lower and "partner" not in pregunta_lower):
        return "gmv_farmacia_total"
    if "gmv de" in pregunta_lower and ("última semana" in pregunta_lower or "último mes" in pregunta_lower):
        return "gmv_farmacia_periodo"
    if "pedidos de" in pregunta_lower and "en" in pregunta_lower:
        return "pedidos_farmacia_partner"
    if "top" in pregunta_lower and "farmacias" in pregunta_lower and "venden" in pregunta_lower and "{partner}" not in pregunta:
        return "top_farmacias_gmv"
    if "top" in pregunta_lower and "farmacias" in pregunta_lower and "{partner}" in pregunta:
        return "top_farmacias_partner"
    
    # Product queries
    if "cuántos productos activos" in pregunta_lower:
        return "productos_activos_total"
    if "stock de" in pregunta_lower:
        return "stock_producto"
    if "precio" in pregunta_lower:
        return "precio_producto"
    if "qué farmacias tienen" in pregunta_lower or "farmacias con stock" in pregunta_lower:
        return "farmacias_con_stock"
    if "productos más vendidos" in pregunta_lower:
        return "top_productos_vendidos"
    
    # Partner queries
    if "gmv total de" in pregunta_lower and modo == "partner":
        return "gmv_partner_total"
    if "gmv de" in pregunta_lower and ("esta semana" in pregunta_lower or "este mes" in pregunta_lower):
        return "gmv_partner_periodo"
    if "pedidos totales por partner" in pregunta_lower:
        return "pedidos_por_partner"
    if "top" in pregunta_lower and "partners" in pregunta_lower:
        return "top_partners_gmv"
    if "farmacias activas en" in pregunta_lower and modo == "partner":
        return "farmacias_activas_partner"
    
    return "unknown"


def comparar_pipelines(pipeline1: list, pipeline2: list) -> int:
    """
    Compara dos pipelines y devuelve un porcentaje de similitud.
    Simplificado: compara número de stages y operadores principales.
    """
    if not pipeline1 or not pipeline2:
        return 0
    
    # Comparar número de stages
    len_similarity = min(len(pipeline1), len(pipeline2)) / max(len(pipeline1), len(pipeline2)) * 100
    
    # Comparar operadores principales en cada stage
    ops1 = set()
    ops2 = set()
    
    for stage in pipeline1:
        ops1.update(stage.keys())
    
    for stage in pipeline2:
        ops2.update(stage.keys())
    
    if not ops1 or not ops2:
        return int(len_similarity)
    
    ops_similarity = len(ops1 & ops2) / len(ops1 | ops2) * 100
    
    # Promedio ponderado
    return int(len_similarity * 0.3 + ops_similarity * 0.7)


if __name__ == "__main__":
    main()

