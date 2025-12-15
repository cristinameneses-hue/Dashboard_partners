"""
Análisis de KPIs de Glovo - Octubre 2025

Este script calcula los siguientes KPIs para el partner Glovo en octubre 2025:
1. GMV total
2. GMV cancelado
3. Número de bookings
4. Número de bookings cancelados
5. Número de farmacias con pedidos
"""

import asyncio
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from infrastructure.repositories.mongodb_repository import MongoDBRepository

# Cargar variables de entorno
load_dotenv()

# Estado cancelado según DICCIONARIO_SEMANTICO_FINAL.md
CANCELLED_STATE_ID = "5a54c525b2948c860f00000d"


async def analizar_glovo_octubre_2025():
    """
    Ejecuta el análisis completo de KPIs de Glovo para octubre 2025.
    """
    # Configurar conexión a MongoDB
    mongo_url = os.getenv('MONGO_LUDAFARMA_URL')
    if not mongo_url:
        print("❌ Error: MONGO_LUDAFARMA_URL no encontrada en .env")
        return

    # Crear repositorio MongoDB
    repo = MongoDBRepository(
        connection_string=mongo_url,
        database_name="ludafarma",
        read_only=True,
        max_limit=100000  # Aumentar límite para análisis completo
    )

    try:
        # Conectar
        await repo.connect()
        print("✅ Conectado a MongoDB (ludafarma)")
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

        # Preparar query
        query_obj = {
            "collection": "bookings",
            "pipeline": pipeline
        }

        print("🔍 Ejecutando análisis de KPIs de Glovo (Octubre 2025)...")
        print()

        # Ejecutar query
        results = await repo.execute_query(json.dumps(query_obj))

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
            print("═" * 70)
            print("📊 KPIS DE GLOVO - OCTUBRE 2025")
            print("═" * 70)
            print()
            print(f"📦 Número de Bookings:                 {num_bookings:,}")
            print(f"❌ Número de Bookings Cancelados:      {num_cancelados:,}")
            print(f"✅ Número de Bookings Activos:         {num_bookings - num_cancelados:,}")
            print()
            print(f"💰 GMV Total:                          €{gmv_total:,.2f}")
            print(f"🚫 GMV Cancelado:                      €{gmv_cancelado:,.2f}")
            print(f"✅ GMV Activo:                         €{gmv_total - gmv_cancelado:,.2f}")
            print()
            print(f"🏥 Número de Farmacias con Pedidos:    {num_farmacias:,}")
            print()
            print("═" * 70)
            print()

            # Calcular estadísticas adicionales
            if num_bookings > 0:
                ticket_promedio = gmv_total / num_bookings
                tasa_cancelacion = (num_cancelados / num_bookings) * 100
                gmv_por_farmacia = gmv_total / num_farmacias if num_farmacias > 0 else 0

                print("📈 ESTADÍSTICAS ADICIONALES")
                print("─" * 70)
                print(f"💳 Ticket Promedio:                    €{ticket_promedio:.2f}")
                print(f"📊 Tasa de Cancelación:                {tasa_cancelacion:.2f}%")
                print(f"🏥 GMV Promedio por Farmacia:          €{gmv_por_farmacia:,.2f}")
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
                    "ticket_promedio_euros": round(ticket_promedio, 2) if num_bookings > 0 else 0,
                    "tasa_cancelacion_porcentaje": round(tasa_cancelacion, 2) if num_bookings > 0 else 0,
                    "gmv_promedio_por_farmacia_euros": round(gmv_por_farmacia, 2) if num_farmacias > 0 else 0
                }
            }

            # Guardar resultados
            output_file = "resultados_glovo_octubre_2025.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"💾 Resultados guardados en: {output_file}")
            print()

            return output

        else:
            print("⚠️ No se encontraron datos para Glovo en octubre 2025")
            return None

    except Exception as e:
        print(f"❌ Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        # Desconectar
        await repo.disconnect()
        print("✅ Desconectado de MongoDB")


if __name__ == "__main__":
    # Ejecutar análisis
    resultado = asyncio.run(analizar_glovo_octubre_2025())

    if resultado:
        print()
        print("🎉 Análisis completado exitosamente!")
    else:
        print()
        print("⚠️ El análisis no pudo completarse")
