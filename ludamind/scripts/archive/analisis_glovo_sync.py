"""
Análisis de KPIs de Glovo - Octubre 2025 (Versión Síncrona)

Este script calcula los siguientes KPIs para el partner Glovo en octubre 2025:
1. GMV total
2. GMV cancelado
3. Número de bookings
4. Número de bookings cancelados
5. Número de farmacias con pedidos
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

# Cargar variables de entorno
load_dotenv()

# Estado cancelado según DICCIONARIO_SEMANTICO_FINAL.md
CANCELLED_STATE_ID = "5a54c525b2948c860f00000d"


def convert_objectid(doc):
    """Convierte ObjectId a string para JSON serialization."""
    if isinstance(doc, dict):
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, dict):
                doc[key] = convert_objectid(value)
            elif isinstance(value, list):
                doc[key] = [
                    convert_objectid(item) if isinstance(item, dict) else
                    str(item) if isinstance(item, ObjectId) else item
                    for item in value
                ]
            elif isinstance(value, datetime):
                doc[key] = value.isoformat()
    return doc


def analizar_glovo_octubre_2025():
    """
    Ejecuta el análisis completo de KPIs de Glovo para octubre 2025.
    """
    # Configurar conexión a MongoDB
    mongo_url = os.getenv('MONGO_LUDAFARMA_URL')
    if not mongo_url:
        print("ERROR: MONGO_LUDAFARMA_URL no encontrada en .env")
        return

    # Crear cliente MongoDB
    client = MongoClient(mongo_url)
    db = client['LudaFarma-PRO']
    collection = db['bookings']

    try:
        print("CONECTADO a MongoDB (LudaFarma-PRO)")
        print()

        # Pipeline de agregación según DICCIONARIO_SEMANTICO_FINAL.md
        pipeline = [
            # Filtro inicial: Glovo + Octubre 2025
            {
                "$match": {
                    "thirdUser.user": "glovo",
                    "createdDate": {
                        "$gte": datetime(2025, 10, 1),
                        "$lt": datetime(2025, 11, 1)
                    }
                }
            },
            # Calcular todas las métricas en paralelo con $facet
            {
                "$facet": {
                    # Métricas totales
                    "total_metrics": [
                        {
                            "$group": {
                                "_id": None,
                                "total_bookings": {"$sum": 1},
                                "total_gmv": {
                                    "$sum": {
                                        "$cond": {
                                            "if": {"$ne": ["$thirdUser.price", None]},
                                            "then": "$thirdUser.price",
                                            "else": {
                                                "$sum": {
                                                    "$map": {
                                                        "input": "$items",
                                                        "as": "item",
                                                        "in": {
                                                            "$multiply": [
                                                                {"$ifNull": ["$$item.pvp", 0]},
                                                                {"$ifNull": ["$$item.quantity", 0]}
                                                            ]
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    # Métricas de cancelados
                    "cancelled_metrics": [
                        {
                            "$match": {
                                "state": CANCELLED_STATE_ID
                            }
                        },
                        {
                            "$group": {
                                "_id": None,
                                "cancelled_bookings": {"$sum": 1},
                                "cancelled_gmv": {
                                    "$sum": {
                                        "$cond": {
                                            "if": {"$ne": ["$thirdUser.price", None]},
                                            "then": "$thirdUser.price",
                                            "else": {
                                                "$sum": {
                                                    "$map": {
                                                        "input": "$items",
                                                        "as": "item",
                                                        "in": {
                                                            "$multiply": [
                                                                {"$ifNull": ["$$item.pvp", 0]},
                                                                {"$ifNull": ["$$item.quantity", 0]}
                                                            ]
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    # Farmacias únicas
                    "unique_pharmacies": [
                        {
                            "$group": {
                                "_id": "$target"
                            }
                        },
                        {
                            "$count": "num_pharmacies"
                        }
                    ]
                }
            }
        ]

        print("EJECUTANDO analisis de KPIs de Glovo (Octubre 2025)...")
        print()

        # Ejecutar agregación
        cursor = collection.aggregate(pipeline)
        results = list(cursor)

        # Convertir ObjectIds
        results = [convert_objectid(doc) for doc in results]

        # Procesar resultados
        if results and len(results) > 0:
            data = results[0]

            # Extraer métricas
            total_metrics = data.get('total_metrics', [{}])[0]
            cancelled_metrics = data.get('cancelled_metrics', [{}])[0] if data.get('cancelled_metrics') else {}
            unique_pharmacies = data.get('unique_pharmacies', [{}])[0] if data.get('unique_pharmacies') else {}

            # KPIs extraídos
            gmv_total = total_metrics.get('total_gmv', 0)
            num_bookings = total_metrics.get('total_bookings', 0)
            gmv_cancelado = cancelled_metrics.get('cancelled_gmv', 0)
            num_cancelados = cancelled_metrics.get('cancelled_bookings', 0)
            num_farmacias = unique_pharmacies.get('num_pharmacies', 0)

            # Presentar resultados
            print("=" * 70)
            print("KPIS DE GLOVO - OCTUBRE 2025")
            print("=" * 70)
            print()
            print(f"Numero de Bookings:                 {num_bookings:,}")
            print(f"Numero de Bookings Cancelados:      {num_cancelados:,}")
            print(f"Numero de Bookings Activos:         {num_bookings - num_cancelados:,}")
            print()
            print(f"GMV Total:                          EUR {gmv_total:,.2f}")
            print(f"GMV Cancelado:                      EUR {gmv_cancelado:,.2f}")
            print(f"GMV Activo:                         EUR {gmv_total - gmv_cancelado:,.2f}")
            print()
            print(f"Numero de Farmacias con Pedidos:    {num_farmacias:,}")
            print()
            print("=" * 70)
            print()

            # Calcular estadísticas adicionales
            ticket_promedio = 0
            tasa_cancelacion = 0
            gmv_por_farmacia = 0

            if num_bookings > 0:
                ticket_promedio = gmv_total / num_bookings
                tasa_cancelacion = (num_cancelados / num_bookings) * 100

            if num_farmacias > 0:
                gmv_por_farmacia = gmv_total / num_farmacias

            print("ESTADISTICAS ADICIONALES")
            print("-" * 70)
            print(f"Ticket Promedio:                    EUR {ticket_promedio:.2f}")
            print(f"Tasa de Cancelacion:                {tasa_cancelacion:.2f}%")
            print(f"GMV Promedio por Farmacia:          EUR {gmv_por_farmacia:,.2f}")
            print()

            # Exportar a JSON
            output = {
                "partner": "glovo",
                "periodo": "octubre 2025",
                "fecha_analisis": datetime.now().isoformat(),
                "kpis": {
                    "num_bookings": num_bookings,
                    "num_bookings_cancelados": num_cancelados,
                    "num_bookings_activos": num_bookings - num_cancelados,
                    "gmv_total_euros": round(gmv_total, 2),
                    "gmv_cancelado_euros": round(gmv_cancelado, 2),
                    "gmv_activo_euros": round(gmv_total - gmv_cancelado, 2),
                    "num_farmacias_con_pedidos": num_farmacias
                },
                "estadisticas_adicionales": {
                    "ticket_promedio_euros": round(ticket_promedio, 2),
                    "tasa_cancelacion_porcentaje": round(tasa_cancelacion, 2),
                    "gmv_promedio_por_farmacia_euros": round(gmv_por_farmacia, 2)
                },
                "pipeline_mongodb": pipeline
            }

            # Guardar resultados
            output_file = "resultados_glovo_octubre_2025.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False, default=str)

            print(f"Resultados guardados en: {output_file}")
            print()

            return output

        else:
            print("No se encontraron datos para Glovo en octubre 2025")
            return None

    except Exception as e:
        print(f"ERROR durante el analisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        # Cerrar conexión
        client.close()
        print("DESCONECTADO de MongoDB")


if __name__ == "__main__":
    # Ejecutar análisis
    resultado = analizar_glovo_octubre_2025()

    if resultado:
        print()
        print("Analisis completado exitosamente!")
        print()
        print("RESUMEN EJECUTIVO:")
        print(f"  - Total bookings: {resultado['kpis']['num_bookings']}")
        print(f"  - GMV total: EUR {resultado['kpis']['gmv_total_euros']:,.2f}")
        print(f"  - Farmacias atendidas: {resultado['kpis']['num_farmacias_con_pedidos']}")
    else:
        print()
        print("El analisis no pudo completarse")
