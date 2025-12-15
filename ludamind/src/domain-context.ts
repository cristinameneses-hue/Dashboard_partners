/**
 * Domain Context for Pharmacy Analytics System
 * This module provides rich context to help LLMs understand and translate
 * natural language queries into appropriate SQL statements.
 */

export interface TableContext {
  name: string;
  description: string;
  businessPurpose: string;
  commonQueries: string[];
  importantFields: FieldContext[];
  relationships: RelationshipContext[];
}

export interface FieldContext {
  name: string;
  description: string;
  businessMeaning: string;
  examples?: string[];
}

export interface RelationshipContext {
  relatedTable: string;
  description: string;
  joinCondition: string;
}

export interface QueryPattern {
  naturalLanguage: string[];
  sqlTemplate: string;
  explanation: string;
  category: string;
}

/**
 * Complete database schema context with business logic
 */
export const DOMAIN_CONTEXT: TableContext[] = [
  {
    name: "items",
    description: "Catálogo maestro de productos farmacéuticos",
    businessPurpose: "Contiene información de todos los medicamentos y productos disponibles, incluyendo precios, características especiales (narcóticos, refrigeración, etc.)",
    commonQueries: [
      "¿Qué productos son narcóticos?",
      "Dame el precio de un medicamento",
      "Lista de productos que requieren refrigeración",
      "Buscar productos por nombre o código"
    ],
    importantFields: [
      {
        name: "code",
        description: "Código nacional del producto (CN)",
        businessMeaning: "Identificador único del producto a nivel nacional, usado para relacionar con otras tablas"
      },
      {
        name: "description",
        description: "Nombre comercial del producto",
        businessMeaning: "Nombre con el que se comercializa el medicamento"
      },
      {
        name: "narcotics",
        description: "Indica si es sustancia controlada",
        businessMeaning: "1=sí, 0=no. Afecta los permisos de compra automática por farmacia"
      },
      {
        name: "efg",
        description: "Indica si es genérico (Equivalente Farmacéutico Genérico)",
        businessMeaning: "1=sí, 0=no. Productos genéricos con igual eficacia que marca"
      },
      {
        name: "pvp",
        description: "Precio de venta al público",
        businessMeaning: "Precio final que paga el cliente"
      }
    ],
    relationships: [
      {
        relatedTable: "trends_consolidado",
        description: "Métricas de ventas y demanda del producto",
        joinCondition: "items.code = trends_consolidado.id_farmaco"
      },
      {
        relatedTable: "carrito_compras",
        description: "Productos recomendados en carritos de compra",
        joinCondition: "items.code = carrito_compras.id_farmaco"
      }
    ]
  },
  {
    name: "stockEvents_{YYYY}_{MM}",
    description: "Eventos diarios de stock por farmacia y producto (tablas particionadas por mes)",
    businessPurpose: "Registro granular de ventas, aprovisionamiento y stock final de cada producto en cada farmacia. Base para analítica de tendencias.",
    commonQueries: [
      "Ventas de un producto en una farmacia específica",
      "Stock disponible al final del día",
      "Productos más vendidos en un periodo",
      "Evolución del stock de un producto"
    ],
    importantFields: [
      {
        name: "pharmacyId",
        description: "Identificador de la farmacia",
        businessMeaning: "Código único de la farmacia que reporta el evento"
      },
      {
        name: "id_farmaco",
        description: "Código nacional del producto",
        businessMeaning: "Referencia al producto en la tabla items"
      },
      {
        name: "nventas",
        description: "Número de unidades vendidas",
        businessMeaning: "Cantidad de producto vendido en esa fecha"
      },
      {
        name: "stockFinal",
        description: "Stock al final del día",
        businessMeaning: "Inventario disponible después de ventas y aprovisionamiento"
      },
      {
        name: "fecha",
        description: "Fecha del evento",
        businessMeaning: "Día en que ocurrió el evento de stock/venta"
      },
      {
        name: "pva",
        description: "Precio de compra aproximado",
        businessMeaning: "Precio al que la farmacia adquiere el producto"
      },
      {
        name: "pvp",
        description: "Precio de venta al público",
        businessMeaning: "Precio al que se vende al cliente final"
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "stockEvents.id_farmaco = items.code"
      },
      {
        relatedTable: "api_pharmacies",
        description: "Datos de la farmacia",
        joinCondition: "stockEvents.pharmacyId = api_pharmacies.pharmacy_id"
      }
    ]
  },
  {
    name: "trends_consolidado",
    description: "Métricas diarias consolidadas por producto (agregación de todas las fuentes)",
    businessPurpose: "Vista unificada de ventas, stock y demanda (bookings) por producto y día. Principal tabla para análisis de tendencias.",
    commonQueries: [
      "¿Cuál es la tendencia de ventas de un producto?",
      "Productos con más demanda (bookings) en los últimos días",
      "Comparar stock vs ventas de un producto",
      "Productos con desabastecimiento potencial"
    ],
    importantFields: [
      {
        name: "id_farmaco",
        description: "Código nacional del producto",
        businessMeaning: "Identificador del medicamento"
      },
      {
        name: "fecha",
        description: "Fecha de la métrica",
        businessMeaning: "Día del registro consolidado"
      },
      {
        name: "nventas",
        description: "Total de unidades vendidas",
        businessMeaning: "Suma de ventas de todas las farmacias"
      },
      {
        name: "stockFinal",
        description: "Stock total disponible",
        businessMeaning: "Suma del inventario de todas las farmacias"
      },
      {
        name: "Booking_total",
        description: "Total de reservas/derivaciones",
        businessMeaning: "Indicador de presión de demanda - clientes que buscaron el producto"
      },
      {
        name: "Booking_finalizado",
        description: "Reservas completadas",
        businessMeaning: "Derivaciones que resultaron en venta"
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "trends_consolidado.id_farmaco = items.code"
      },
      {
        relatedTable: "trends_metrica_intermedia",
        description: "Métricas avanzadas y grupos de riesgo",
        joinCondition: "trends_consolidado.id_farmaco = trends_metrica_intermedia.id_farmaco AND trends_consolidado.fecha = trends_metrica_intermedia.fecha"
      }
    ]
  },
  {
    name: "trends_metrica_intermedia",
    description: "Features avanzadas y clasificación de riesgo por producto/día",
    businessPurpose: "Contiene señales calculadas (medianas, z-scores, deltas) y grupos de riesgo (1-4) para detectar desabastecimientos o anomalías.",
    commonQueries: [
      "Productos en riesgo de desabastecimiento (grupos 3 y 4)",
      "Productos con stock anormalmente bajo",
      "Evolución del grupo de riesgo de un producto",
      "Productos con alta presión de demanda"
    ],
    importantFields: [
      {
        name: "id_grupo",
        description: "Grupo de riesgo del producto",
        businessMeaning: "0=sin riesgo, 1=riesgo bajo, 2=riesgo medio, 3=riesgo alto, 4=riesgo crítico. Basado en stock y demanda.",
        examples: ["1", "2", "3", "4", "0"]
      },
      {
        name: "Z_Y",
        description: "Z-score del stock normalizado",
        businessMeaning: "(stockFinal - mediana)/mediana. Negativo indica stock bajo respecto a histórico.",
        examples: ["-0.5 (50% menos que mediana)", "0.0 (igual a mediana)", "1.0 (doble de mediana)"]
      },
      {
        name: "mediana",
        description: "Mediana histórica del stock",
        businessMeaning: "Stock típico del producto en base a datos históricos (rolling window)"
      },
      {
        name: "booking_7_dias",
        description: "Bookings acumulados últimos 7 días",
        businessMeaning: "Presión de demanda reciente - cuántas veces se buscó el producto"
      },
      {
        name: "peso_bookings_producto",
        description: "Factor de peso de demanda",
        businessMeaning: "Importancia relativa de los bookings para este producto"
      }
    ],
    relationships: [
      {
        relatedTable: "trends_consolidado",
        description: "Datos base de ventas y stock",
        joinCondition: "trends_metrica_intermedia.id_farmaco = trends_consolidado.id_farmaco AND trends_metrica_intermedia.fecha = trends_consolidado.fecha"
      },
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "trends_metrica_intermedia.id_farmaco = items.code"
      }
    ]
  },
  {
    name: "carrito_compras",
    description: "Carrito de compra actual recomendado por farmacia",
    businessPurpose: "Contiene las recomendaciones actuales de qué productos y cuántas unidades debería pedir cada farmacia. Actualizado por algoritmos de reposición.",
    commonQueries: [
      "¿Qué productos se recomiendan comprar a una farmacia?",
      "Cantidad sugerida de un producto para una farmacia",
      "Productos recomendados que no son venta recurrente",
      "Total de unidades recomendadas por farmacia"
    ],
    importantFields: [
      {
        name: "pharmacy_id",
        description: "Identificador de la farmacia",
        businessMeaning: "Farmacia a la que se hace la recomendación"
      },
      {
        name: "id_farmaco",
        description: "Código del producto",
        businessMeaning: "Producto recomendado"
      },
      {
        name: "unidades_propuestas",
        description: "Cantidad sugerida",
        businessMeaning: "Número de unidades que el sistema recomienda comprar"
      },
      {
        name: "venta_recurrente",
        description: "Si la farmacia vende habitualmente este producto",
        businessMeaning: "'Y'=sí vende habitualmente, 'N'=producto nuevo o no habitual para esta farmacia",
        examples: ["Y", "N"]
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "carrito_compras.id_farmaco = items.code"
      },
      {
        relatedTable: "api_pharmacies",
        description: "Configuración de la farmacia",
        joinCondition: "carrito_compras.pharmacy_id = api_pharmacies.pharmacy_id"
      },
      {
        relatedTable: "pharmacies_auto_parameters",
        description: "Filtros y parámetros de compra automática",
        joinCondition: "carrito_compras.pharmacy_id = pharmacies_auto_parameters.pharmacy_id"
      }
    ]
  },
  {
    name: "historico_pedidos",
    description: "Historial de pedidos realizados por el sistema Trends",
    businessPurpose: "Registro de todos los pedidos generados automáticamente, incluyendo cantidades propuestas vs recibidas, cooperativa usada, etc.",
    commonQueries: [
      "Historial de pedidos de una farmacia",
      "Pedidos de un producto específico",
      "Diferencias entre unidades propuestas y recibidas",
      "Pedidos por cooperativa"
    ],
    importantFields: [
      {
        name: "pharmacy_id",
        description: "Farmacia que hizo el pedido",
        businessMeaning: "Identificador de la farmacia"
      },
      {
        name: "codigo_nacional",
        description: "Código del producto pedido",
        businessMeaning: "Producto solicitado"
      },
      {
        name: "unidades_propuestas",
        description: "Cantidad solicitada",
        businessMeaning: "Unidades que el sistema propuso/pidió"
      },
      {
        name: "unidades_recibidas",
        description: "Cantidad entregada",
        businessMeaning: "Unidades realmente suministradas por el proveedor"
      },
      {
        name: "cooperativa_id",
        description: "Proveedor que suministró",
        businessMeaning: "Cooperativa/almacén que procesó el pedido"
      },
      {
        name: "pedido_num",
        description: "Número de pedido",
        businessMeaning: "Identificador del pedido en el sistema del proveedor"
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "historico_pedidos.codigo_nacional = items.code"
      },
      {
        relatedTable: "cooperativas",
        description: "Datos de la cooperativa",
        joinCondition: "historico_pedidos.cooperativa_id = cooperativas.id"
      },
      {
        relatedTable: "api_pharmacies",
        description: "Datos de la farmacia",
        joinCondition: "historico_pedidos.pharmacy_id = api_pharmacies.pharmacy_id"
      }
    ]
  },
  {
    name: "historico_pedidos_cazados",
    description: "Historial de pedidos del sistema Hunter (búsqueda activa de productos)",
    businessPurpose: "Similar a historico_pedidos pero para el sistema 'Hunter' que busca activamente productos con desabastecimiento en múltiples proveedores.",
    commonQueries: [
      "Productos cazados para una farmacia",
      "Eficiencia del Hunter (unidades propuestas vs recibidas)",
      "Productos más cazados (alta demanda insatisfecha)"
    ],
    importantFields: [
      {
        name: "pharmacy_id",
        description: "Farmacia solicitante",
        businessMeaning: "Farmacia que necesitaba el producto"
      },
      {
        name: "codigo_nacional",
        description: "Producto cazado",
        businessMeaning: "Código del medicamento buscado"
      },
      {
        name: "unidades_propuestas",
        description: "Cantidad buscada",
        businessMeaning: "Unidades que Hunter intentó conseguir"
      },
      {
        name: "unidades_recibidas",
        description: "Cantidad conseguida",
        businessMeaning: "Unidades que se lograron obtener"
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "historico_pedidos_cazados.codigo_nacional = items.code"
      }
    ]
  },
  {
    name: "disponibilidad",
    description: "Estado actual de disponibilidad de productos por proveedor y farmacia",
    businessPurpose: "Indica qué productos están disponibles en qué cooperativas para cada farmacia. Se actualiza diariamente.",
    commonQueries: [
      "¿Dónde está disponible un producto?",
      "Productos disponibles en una cooperativa específica",
      "Última actualización de disponibilidad"
    ],
    importantFields: [
      {
        name: "codigo_nacional",
        description: "Código del producto",
        businessMeaning: "Medicamento consultado"
      },
      {
        name: "id_cooperativa",
        description: "Cooperativa que tiene disponibilidad",
        businessMeaning: "Proveedor con stock del producto"
      },
      {
        name: "pharmacy_id",
        description: "Farmacia para la que está disponible",
        businessMeaning: "Farmacia que puede pedir a esta cooperativa"
      },
      {
        name: "ultima_actualizacion",
        description: "Fecha de última verificación",
        businessMeaning: "Cuándo se consultó por última vez la disponibilidad"
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información del producto",
        joinCondition: "disponibilidad.codigo_nacional = items.code"
      },
      {
        relatedTable: "cooperativas",
        description: "Datos de la cooperativa",
        joinCondition: "disponibilidad.id_cooperativa = cooperativas.id"
      }
    ]
  },
  {
    name: "api_pharmacies",
    description: "Configuración de farmacias y acceso a APIs",
    businessPurpose: "Contiene credenciales y configuración de habilitación de sistemas automáticos (Trends, Hunter) por farmacia.",
    commonQueries: [
      "Farmacias con Trends activo",
      "Farmacias con Hunter habilitado",
      "Estado de activación de sistemas por farmacia"
    ],
    importantFields: [
      {
        name: "pharmacy_id",
        description: "Identificador de farmacia",
        businessMeaning: "ID único de la farmacia"
      },
      {
        name: "active",
        description: "Estado de Trends autobuy",
        businessMeaning: "1=Trends activo (compra automática habilitada), 0=deshabilitado"
      },
      {
        name: "hunter_active",
        description: "Estado de Hunter",
        businessMeaning: "1=Hunter activo (búsqueda automática habilitada), 0=deshabilitado"
      }
    ],
    relationships: [
      {
        relatedTable: "pharmacies",
        description: "Datos descriptivos de la farmacia",
        joinCondition: "api_pharmacies.pharmacy_id = pharmacies.pharmacy_id"
      },
      {
        relatedTable: "pharmacies_auto_parameters",
        description: "Parámetros de filtrado automático",
        joinCondition: "api_pharmacies.pharmacy_id = pharmacies_auto_parameters.pharmacy_id"
      }
    ]
  },
  {
    name: "pharmacies_auto_parameters",
    description: "Parámetros y filtros de compra automática por farmacia",
    businessPurpose: "Define qué tipo de productos puede comprar cada farmacia automáticamente (narcóticos, precio máximo, refrigeración, etc.)",
    commonQueries: [
      "¿Qué farmacias aceptan narcóticos?",
      "Precio máximo configurado por farmacia",
      "Farmacias que aceptan productos refrigerados"
    ],
    importantFields: [
      {
        name: "narcotics",
        description: "Permite sustancias controladas",
        businessMeaning: "1=sí puede comprar narcóticos, 0=no"
      },
      {
        name: "max_pvp",
        description: "Precio máximo aceptado",
        businessMeaning: "Tope de precio que la farmacia acepta en compra automática"
      },
      {
        name: "fridge",
        description: "Acepta productos refrigerados",
        businessMeaning: "1=sí tiene capacidad de refrigeración, 0=no"
      },
      {
        name: "freezer",
        description: "Acepta productos congelados",
        businessMeaning: "1=sí tiene congelador, 0=no"
      },
      {
        name: "group_1",
        description: "Permite productos grupo 1",
        businessMeaning: "1=permite, 0=no. Filtro por grupo de riesgo/clasificación"
      }
    ],
    relationships: [
      {
        relatedTable: "api_pharmacies",
        description: "Datos de configuración de API",
        joinCondition: "pharmacies_auto_parameters.pharmacy_id = api_pharmacies.pharmacy_id"
      }
    ]
  },
  {
    name: "cooperativas",
    description: "Catálogo de cooperativas/proveedores/almacenes",
    businessPurpose: "Lista de proveedores disponibles para suministro de medicamentos.",
    commonQueries: [
      "Lista de cooperativas disponibles",
      "Buscar cooperativa por nombre"
    ],
    importantFields: [
      {
        name: "id",
        description: "Identificador único",
        businessMeaning: "ID de la cooperativa"
      },
      {
        name: "nombre",
        description: "Nombre de la cooperativa",
        businessMeaning: "Razón social o nombre comercial"
      }
    ],
    relationships: [
      {
        relatedTable: "warehouse_priorities",
        description: "Prioridades de pedido por farmacia",
        joinCondition: "cooperativas.id = warehouse_priorities.id_cooperativa"
      },
      {
        relatedTable: "disponibilidad",
        description: "Productos disponibles en la cooperativa",
        joinCondition: "cooperativas.id = disponibilidad.id_cooperativa"
      }
    ]
  },
  {
    name: "warehouse_priorities",
    description: "Orden de prioridad de cooperativas por farmacia",
    businessPurpose: "Define en qué orden cada farmacia debe intentar pedir a las diferentes cooperativas (1=primera opción, 2=segunda, etc.)",
    commonQueries: [
      "Prioridades de una farmacia",
      "Farmacias que usan una cooperativa específica"
    ],
    importantFields: [
      {
        name: "pharmacy_id",
        description: "Farmacia configurada",
        businessMeaning: "Farmacia a la que aplica la prioridad"
      },
      {
        name: "id_cooperativa",
        description: "Cooperativa priorizada",
        businessMeaning: "Proveedor en esta posición de prioridad"
      },
      {
        name: "orden",
        description: "Posición en orden de prioridad",
        businessMeaning: "1=primera opción, 2=segunda, etc. Menor número = mayor prioridad",
        examples: ["1", "2", "3"]
      }
    ],
    relationships: [
      {
        relatedTable: "api_pharmacies",
        description: "Datos de la farmacia",
        joinCondition: "warehouse_priorities.pharmacy_id = api_pharmacies.pharmacy_id"
      },
      {
        relatedTable: "cooperativas",
        description: "Datos de la cooperativa",
        joinCondition: "warehouse_priorities.id_cooperativa = cooperativas.id"
      }
    ]
  },
  {
    name: "otc_categorias",
    description: "Categorización de productos OTC (medicamentos sin receta)",
    businessPurpose: "Clasifica productos OTC en categorías terapéuticas para análisis por segmento. Permite filtrar y analizar ventas, stock y recomendaciones por categoría farmacéutica.",
    commonQueries: [
      "Productos OTC en la categoría Analgésico",
      "Ventas de productos digestivos este mes",
      "Stock de productos dermatológicos en riesgo",
      "Recomendaciones de compra por categoría terapéutica",
      "Top categorías OTC más vendidas"
    ],
    importantFields: [
      {
        name: "id_farmaco",
        description: "Código nacional del producto",
        businessMeaning: "Identificador del producto OTC, referencia a items.code"
      },
      {
        name: "categoria",
        description: "Categoría terapéutica principal (SuperCollection)",
        businessMeaning: "Clasificación principal del producto: Analgésico, Sistema digestivo, Sistema dermatológico, etc. (15 categorías totales)",
        examples: ["Analgésico", "Sistema digestivo", "Sistema dermatológico", "Sistema respiratorio", "Sistema nervioso"]
      },
      {
        name: "subcategoria",
        description: "Subcategoría específica (Collection)",
        businessMeaning: "Clasificación detallada dentro de la categoría principal",
        examples: ["Analgésicos musculares", "Antitusivos y descongestionantes", "Antisépticos", "Laxante"]
      }
    ],
    relationships: [
      {
        relatedTable: "items",
        description: "Información completa del producto",
        joinCondition: "otc_categorias.id_farmaco = items.code"
      },
      {
        relatedTable: "trends_consolidado",
        description: "Ventas y métricas del producto OTC",
        joinCondition: "otc_categorias.id_farmaco = trends_consolidado.id_farmaco"
      },
      {
        relatedTable: "trends_metrica_intermedia",
        description: "Riesgo y análisis avanzado del producto OTC",
        joinCondition: "otc_categorias.id_farmaco = trends_metrica_intermedia.id_farmaco"
      },
      {
        relatedTable: "carrito_compras",
        description: "Recomendaciones de compra de productos OTC",
        joinCondition: "otc_categorias.id_farmaco = carrito_compras.id_farmaco"
      }
    ]
  }
];

/**
 * Common query patterns with natural language examples
 */
export const QUERY_PATTERNS: QueryPattern[] = [
  // VENTAS Y TENDENCIAS
  {
    category: "ventas",
    naturalLanguage: [
      "productos más vendidos",
      "top ventas del mes",
      "qué se vendió más",
      "productos con más demanda"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  SUM(tc.nventas) as total_ventas,
  SUM(tc.Booking_total) as total_bookings
FROM trends_consolidado tc
JOIN items i ON tc.id_farmaco = i.code
WHERE tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY i.code, i.description
ORDER BY total_ventas DESC
LIMIT 20;`,
    explanation: "Obtiene los productos más vendidos en los últimos 30 días, incluyendo bookings para ver demanda total"
  },
  {
    category: "ventas",
    naturalLanguage: [
      "ventas de [producto]",
      "cuánto se vendió de [producto]",
      "evolución de ventas de [producto]"
    ],
    sqlTemplate: `
SELECT
  tc.fecha,
  tc.nventas,
  tc.stockFinal,
  tc.Booking_total
FROM trends_consolidado tc
JOIN items i ON tc.id_farmaco = i.code
WHERE i.description LIKE '%[PRODUCTO]%'
  AND tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
ORDER BY tc.fecha DESC;`,
    explanation: "Muestra la evolución diaria de ventas, stock y demanda de un producto específico"
  },

  // RIESGO Y DESABASTECIMIENTO
  {
    category: "riesgo",
    naturalLanguage: [
      "productos en riesgo",
      "riesgo de desabastecimiento",
      "productos con stock bajo",
      "medicamentos en alerta"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  tm.id_grupo as grupo_riesgo,
  tm.Z_Y as z_score_stock,
  tm.stockFinal,
  tm.booking_7_dias,
  tc.nventas as ventas_ultimo_dia
FROM trends_metrica_intermedia tm
JOIN items i ON tm.id_farmaco = i.code
JOIN trends_consolidado tc ON tm.id_farmaco = tc.id_farmaco AND tm.fecha = tc.fecha
WHERE tm.id_grupo IN (3, 4)  -- Riesgo alto y crítico
  AND tm.fecha = (SELECT MAX(fecha) FROM trends_metrica_intermedia)
ORDER BY tm.id_grupo DESC, tm.booking_7_dias DESC
LIMIT 50;`,
    explanation: "Productos en riesgo alto (grupo 3) o crítico (grupo 4), ordenados por presión de demanda"
  },
  {
    category: "riesgo",
    naturalLanguage: [
      "productos con stock anormal",
      "anomalías en stock",
      "stock fuera de lo normal"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  tm.stockFinal,
  tm.mediana as stock_normal,
  tm.Z_Y as desviacion,
  CASE
    WHEN tm.Z_Y < -0.5 THEN 'Stock bajo'
    WHEN tm.Z_Y > 0.5 THEN 'Stock alto'
    ELSE 'Normal'
  END as estado
FROM trends_metrica_intermedia tm
JOIN items i ON tm.id_farmaco = i.code
WHERE tm.fecha = (SELECT MAX(fecha) FROM trends_metrica_intermedia)
  AND ABS(tm.Z_Y) > 0.5
ORDER BY ABS(tm.Z_Y) DESC
LIMIT 30;`,
    explanation: "Detecta productos con stock anormalmente alto o bajo comparado con su histórico"
  },

  // CARRITOS Y RECOMENDACIONES
  {
    category: "carritos",
    naturalLanguage: [
      "qué debe comprar la farmacia [id]",
      "recomendaciones para farmacia [id]",
      "carrito de compra de [farmacia]"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  cc.unidades_propuestas,
  cc.venta_recurrente,
  i.pvp,
  (cc.unidades_propuestas * i.pvp) as total_estimado
FROM carrito_compras cc
JOIN items i ON cc.id_farmaco = i.code
WHERE cc.pharmacy_id = '[PHARMACY_ID]'
ORDER BY cc.venta_recurrente DESC, cc.unidades_propuestas DESC;`,
    explanation: "Muestra las recomendaciones actuales de compra para una farmacia específica"
  },
  {
    category: "carritos",
    naturalLanguage: [
      "productos nuevos recomendados",
      "recomendaciones no recurrentes",
      "productos sugeridos fuera de lo habitual"
    ],
    sqlTemplate: `
SELECT
  p.description as farmacia,
  i.description as producto,
  cc.unidades_propuestas,
  i.pvp
FROM carrito_compras cc
JOIN items i ON cc.id_farmaco = i.code
JOIN pharmacies p ON cc.pharmacy_id = p.pharmacy_id
WHERE cc.venta_recurrente = 'N'
ORDER BY p.description, cc.unidades_propuestas DESC;`,
    explanation: "Productos recomendados que la farmacia normalmente no vende (oportunidades o desabastecimientos)"
  },

  // HISTÓRICO DE PEDIDOS
  {
    category: "pedidos",
    naturalLanguage: [
      "historial de pedidos de [farmacia]",
      "pedidos realizados por [farmacia]",
      "qué ha pedido [farmacia]"
    ],
    sqlTemplate: `
SELECT
  hp.fecha,
  i.description,
  hp.unidades_propuestas,
  hp.unidades_recibidas,
  c.nombre as cooperativa,
  CASE
    WHEN hp.unidades_recibidas < hp.unidades_propuestas THEN 'Parcial'
    WHEN hp.unidades_recibidas = hp.unidades_propuestas THEN 'Completo'
    ELSE 'Excedido'
  END as estado_pedido
FROM historico_pedidos hp
JOIN items i ON hp.codigo_nacional = i.code
JOIN cooperativas c ON hp.cooperativa_id = c.id
WHERE hp.pharmacy_id = '[PHARMACY_ID]'
  AND hp.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY hp.fecha DESC;`,
    explanation: "Historial de pedidos con estado de cumplimiento (completo/parcial)"
  },
  {
    category: "pedidos",
    naturalLanguage: [
      "eficiencia de proveedores",
      "qué cooperativa cumple mejor",
      "tasa de cumplimiento por proveedor"
    ],
    sqlTemplate: `
SELECT
  c.nombre as cooperativa,
  COUNT(*) as total_pedidos,
  SUM(hp.unidades_propuestas) as unidades_pedidas,
  SUM(hp.unidades_recibidas) as unidades_recibidas,
  ROUND(100 * SUM(hp.unidades_recibidas) / SUM(hp.unidades_propuestas), 2) as tasa_cumplimiento
FROM historico_pedidos hp
JOIN cooperativas c ON hp.cooperativa_id = c.id
WHERE hp.fecha >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
GROUP BY c.id, c.nombre
ORDER BY tasa_cumplimiento DESC;`,
    explanation: "Analiza qué cooperativas cumplen mejor con las cantidades solicitadas"
  },

  // DISPONIBILIDAD
  {
    category: "disponibilidad",
    naturalLanguage: [
      "dónde está disponible [producto]",
      "en qué cooperativas hay [producto]",
      "quién tiene stock de [producto]"
    ],
    sqlTemplate: `
SELECT
  c.nombre as cooperativa,
  COUNT(DISTINCT d.pharmacy_id) as farmacias_con_acceso,
  d.ultima_actualizacion
FROM disponibilidad d
JOIN cooperativas c ON d.id_cooperativa = c.id
JOIN items i ON d.codigo_nacional = i.code
WHERE i.description LIKE '%[PRODUCTO]%'
GROUP BY c.id, c.nombre, d.ultima_actualizacion
ORDER BY farmacias_con_acceso DESC;`,
    explanation: "Muestra en qué cooperativas está disponible un producto y para cuántas farmacias"
  },

  // ANÁLISIS DE FARMACIAS
  {
    category: "farmacias",
    naturalLanguage: [
      "farmacias con trends activo",
      "qué farmacias usan el sistema automático",
      "farmacias con compra automática"
    ],
    sqlTemplate: `
SELECT
  p.pharmacy_id,
  p.description,
  ap.active as trends_activo,
  ap.hunter_active as hunter_activo,
  pap.max_pvp,
  pap.narcotics as acepta_narcoticos,
  pap.fridge as tiene_refrigeracion
FROM pharmacies p
JOIN api_pharmacies ap ON p.pharmacy_id = ap.pharmacy_id
LEFT JOIN pharmacies_auto_parameters pap ON p.pharmacy_id = pap.pharmacy_id
WHERE ap.active = 1
ORDER BY p.description;`,
    explanation: "Lista farmacias con sistema automático activo y sus parámetros de configuración"
  },
  {
    category: "farmacias",
    naturalLanguage: [
      "configuración de compra de [farmacia]",
      "parámetros de [farmacia]",
      "qué puede comprar [farmacia]"
    ],
    sqlTemplate: `
SELECT
  p.description,
  pap.narcotics as acepta_narcoticos,
  pap.efg as acepta_genericos,
  pap.max_pvp as precio_maximo,
  pap.fridge as requiere_nevera,
  pap.freezer as requiere_congelador,
  ap.active as trends_activo,
  ap.hunter_active as hunter_activo
FROM pharmacies p
JOIN api_pharmacies ap ON p.pharmacy_id = ap.pharmacy_id
JOIN pharmacies_auto_parameters pap ON p.pharmacy_id = pap.pharmacy_id
WHERE p.pharmacy_id = '[PHARMACY_ID]';`,
    explanation: "Muestra la configuración completa de restricciones y capacidades de una farmacia"
  },

  // PRODUCTOS ESPECÍFICOS
  {
    category: "productos",
    naturalLanguage: [
      "buscar producto por nombre",
      "información de [producto]",
      "detalles de [medicamento]"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  i.pvp,
  i.narcotics as es_narcotico,
  i.efg as es_generico,
  i.fridge as requiere_nevera,
  i.freezer as requiere_congelador
FROM items i
WHERE i.description LIKE '%[PRODUCTO]%'
ORDER BY i.description
LIMIT 20;`,
    explanation: "Busca productos por nombre y muestra sus características principales"
  },
  {
    category: "productos",
    naturalLanguage: [
      "productos que requieren refrigeración",
      "medicamentos con nevera",
      "productos refrigerados"
    ],
    sqlTemplate: `
SELECT
  i.code,
  i.description,
  i.pvp,
  CASE
    WHEN i.freezer = 1 THEN 'Congelador'
    WHEN i.fridge = 1 THEN 'Refrigeración'
  END as tipo_frio
FROM items i
WHERE i.fridge = 1 OR i.freezer = 1
ORDER BY i.freezer DESC, i.description;`,
    explanation: "Lista productos que requieren cadena de frío"
  },

  // ANÁLISIS COMPARATIVO
  {
    category: "analisis",
    naturalLanguage: [
      "comparar ventas entre periodos",
      "ventas este mes vs mes anterior",
      "evolución mensual"
    ],
    sqlTemplate: `
SELECT
  DATE_FORMAT(tc.fecha, '%Y-%m') as mes,
  COUNT(DISTINCT tc.id_farmaco) as productos_vendidos,
  SUM(tc.nventas) as total_ventas,
  SUM(tc.Booking_total) as total_bookings,
  AVG(tc.stockFinal) as stock_promedio
FROM trends_consolidado tc
WHERE tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY DATE_FORMAT(tc.fecha, '%Y-%m')
ORDER BY mes DESC;`,
    explanation: "Compara métricas clave por mes en los últimos 6 meses"
  },
  {
    category: "analisis",
    naturalLanguage: [
      "productos con crecimiento en ventas",
      "productos en tendencia alcista",
      "qué está creciendo"
    ],
    sqlTemplate: `
SELECT
  i.description,
  SUM(CASE WHEN tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN tc.nventas ELSE 0 END) as ventas_ultima_semana,
  SUM(CASE WHEN tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
           AND tc.fecha < DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN tc.nventas ELSE 0 END) as ventas_semana_anterior,
  ROUND(100 * (
    SUM(CASE WHEN tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN tc.nventas ELSE 0 END) -
    SUM(CASE WHEN tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
             AND tc.fecha < DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN tc.nventas ELSE 0 END)
  ) / NULLIF(SUM(CASE WHEN tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                      AND tc.fecha < DATE_SUB(CURDATE(), INTERVAL 7 DAY) THEN tc.nventas ELSE 0 END), 0), 2) as crecimiento_porcentual
FROM trends_consolidado tc
JOIN items i ON tc.id_farmaco = i.code
GROUP BY i.code, i.description
HAVING ventas_semana_anterior > 0 AND crecimiento_porcentual > 20
ORDER BY crecimiento_porcentual DESC
LIMIT 20;`,
    explanation: "Identifica productos con crecimiento significativo (>20%) en ventas última semana vs anterior"
  },

  // ===== OTC CATEGORIES =====
  {
    naturalLanguage: [
      "Productos OTC en la categoría Analgésico",
      "Lista de medicamentos sin receta de tipo digestivo",
      "¿Qué productos OTC hay en sistema dermatológico?"
    ],
    category: "OTC Categories",
    sqlTemplate: `
SELECT
  i.code,
  i.description as producto,
  otc.categoria,
  otc.subcategoria,
  i.pvp as precio
FROM items i
JOIN otc_categorias otc ON i.code = otc.id_farmaco
WHERE otc.categoria = 'Analgésico'  -- Cambiar por la categoría deseada
ORDER BY i.description
LIMIT 50;`,
    explanation: "Lista productos OTC de una categoría terapéutica específica con precios"
  },
  {
    naturalLanguage: [
      "Ventas de productos OTC digestivos este mes",
      "¿Cuáles son los analgésicos más vendidos?",
      "Top 10 productos OTC respiratorios por ventas"
    ],
    category: "OTC Categories",
    sqlTemplate: `
SELECT
  i.code,
  i.description as producto,
  otc.categoria,
  otc.subcategoria,
  SUM(tc.nventas) as total_ventas,
  SUM(tc.Booking_total) as total_bookings
FROM trends_consolidado tc
JOIN items i ON tc.id_farmaco = i.code
JOIN otc_categorias otc ON i.code = otc.id_farmaco
WHERE otc.categoria = 'Sistema digestivo'  -- Cambiar por la categoría deseada
  AND tc.fecha >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
GROUP BY i.code, i.description, otc.categoria, otc.subcategoria
ORDER BY total_ventas DESC
LIMIT 20;`,
    explanation: "Top productos OTC más vendidos de una categoría en el mes actual"
  },
  {
    naturalLanguage: [
      "Productos OTC dermatológicos en riesgo",
      "¿Qué analgésicos están en desabastecimiento?",
      "Stock bajo de productos OTC respiratorios"
    ],
    category: "OTC Categories",
    sqlTemplate: `
SELECT
  i.code,
  i.description as producto,
  otc.categoria,
  otc.subcategoria,
  tm.id_grupo as grupo_riesgo,
  tm.Z_Y as z_score_stock,
  SUM(tc.stockFinal) as stock_actual
FROM trends_metrica_intermedia tm
JOIN items i ON tm.id_farmaco = i.code
JOIN otc_categorias otc ON i.code = otc.id_farmaco
LEFT JOIN trends_consolidado tc ON tm.id_farmaco = tc.id_farmaco
  AND tc.fecha = (SELECT MAX(fecha) FROM trends_consolidado)
WHERE otc.categoria = 'Sistema dermatológico'  -- Cambiar por categoría
  AND tm.id_grupo IN (2, 3, 4)  -- Riesgo medio, alto y crítico
  AND tm.fecha = (SELECT MAX(fecha) FROM trends_metrica_intermedia)
GROUP BY i.code, i.description, otc.categoria, otc.subcategoria, tm.id_grupo, tm.Z_Y
ORDER BY tm.id_grupo DESC, tm.Z_Y ASC
LIMIT 20;`,
    explanation: "Productos OTC de una categoría con riesgo de desabastecimiento (grupos 2-4)"
  },
  {
    naturalLanguage: [
      "Comparar ventas de categorías OTC",
      "¿Cuál categoría OTC vende más?",
      "Ranking de categorías OTC por ventas"
    ],
    category: "OTC Categories",
    sqlTemplate: `
SELECT
  otc.categoria,
  COUNT(DISTINCT otc.id_farmaco) as productos_distintos,
  SUM(tc.nventas) as total_ventas,
  SUM(tc.Booking_total) as total_bookings,
  ROUND(AVG(tc.nventas), 2) as promedio_ventas
FROM trends_consolidado tc
JOIN otc_categorias otc ON tc.id_farmaco = otc.id_farmaco
WHERE tc.fecha >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY otc.categoria
ORDER BY total_ventas DESC;`,
    explanation: "Ranking de categorías OTC por volumen de ventas en últimos 30 días"
  }
];

/**
 * Business rules that Claude should understand - BASED ON REAL BACKEND CODE
 */
export const BUSINESS_RULES = {
  riskGroups: {
    description: "Clasificación de riesgo de desabastecimiento (4 grupos + grupo 5 auxiliar para histéresis)",
    algorithm: "groupCreatorAutoChunkFix.py - Cálculo diario sobre trends_consolidado",
    levels: {
      1: {
        name: "Inicio de Problemas",
        condition: "Z_Y entre -0.10 y -0.15 (stock 10-15% bajo mediana)",
        action: "Recomendación: promedio_12_meses × 1 - stock_actual",
        minMediana: 600,
        filterEFG: true,
        meaning: "Señal temprana de posible problema de stock"
      },
      2: {
        name: "Desabastecimiento Probable",
        condition: "Z_Y entre -0.15 y -0.40 (stock 15-40% bajo mediana) O relacion_booking_stock > 7",
        action: "Recomendación: promedio_12_meses × security_stock (1-9, default=4) - stock_actual",
        minMediana: 900,
        usesNotWorkedFallback: true,
        filterEFG: false,
        meaning: "Alta probabilidad de desabastecimiento inminente"
      },
      3: {
        name: "Desabastecido",
        condition: "Z_Y entre -0.40 y -1.0 (stock 40-100% bajo mediana)",
        action: "Recomendación: promedio_12_meses × 2 - stock_actual",
        minMediana: 900,
        filterEFG: true,
        hysteresis: "Puede usar grupo 5 para transiciones suaves",
        meaning: "Producto ya desabastecido - necesita reposición urgente"
      },
      4: {
        name: "Recuperándose",
        condition: "Stock mejorando desde desabastecimiento (transición desde grupo 3)",
        action: "Nivel de recuperación con ajuste progresivo",
        minMediana: 900,
        meaning: "Producto saliendo del desabastecimiento - monitorear recuperación"
      }
    },
    grupo5_auxiliar: {
      description: "Grupo 5 NO es un grupo de riesgo real, solo se usa internamente para gestionar transiciones",
      purpose: "Garantiza permanencia en grupos y evita oscilaciones rápidas entre estados",
      usage: "Permite transiciones suaves entre grupos 3 y 4 principalmente"
    },
    stateMachine: "grupo_anterior rastrea estado previo para transiciones suaves y evitar cambios bruscos"
  },

  zScoreFormula: {
    description: "Z_Y: Métrica normalizada de stock vs mediana histórica",
    formula: "Z_Y = (stockFinal - Mediana) / Mediana",
    medianaCalculation: "expanding().median(stockFinal) - Mediana siempre creciente (toda la historia)",
    specialCase: "Si Mediana = 0, entonces Z_Y = 0",
    interpretation: {
      "Z_Y = 0": "Stock igual a mediana histórica (stock habitual/normal)",
      "Z_Y > 0": "Stock sobre mediana (sobre-stock, inventario excesivo)",
      "Z_Y entre -0.10 y -0.15": "GRUPO 1 - Inicio de problemas (10-15% bajo mediana)",
      "Z_Y entre -0.15 y -0.40": "GRUPO 2 - Desabastecimiento probable (15-40% bajo mediana)",
      "Z_Y entre -0.40 y -1.0": "GRUPO 3 - Desabastecido (40-100% bajo mediana)",
      "Z_Y < -1.0": "Stock críticamente depleto (más de 100% bajo mediana)"
    },
    rangesByGroup: {
      grupo1: "Z_Y: -0.10 a -0.15 (inicio de problemas)",
      grupo2: "Z_Y: -0.15 a -0.40 (desabastecimiento probable)",
      grupo3: "Z_Y: -0.40 a -1.0 (desabastecido)",
      grupo4: "Basado en recuperación desde grupo 3 (no tiene rango Z_Y fijo)"
    },
    relatedMetrics: {
      delta_Z_Y: "Cambio diario en Z_Y (primera diferencia)",
      delta_Z_Y_3dias: "Cambio de Z_Y en ventana de 3 días (detecta caídas rápidas)",
      Z_Y_hace_3_dias: "Valor de Z_Y hace 3 días"
    },
    criticalThresholds: {
      inicio_problemas: "Z_Y alcanza -0.10 (borde superior grupo 1)",
      probable_desabastecimiento: "Z_Y alcanza -0.15 (entra a grupo 2)",
      desabastecido: "Z_Y alcanza -0.40 (entra a grupo 3)",
      critico: "Z_Y < -1.0 (más de 100% depleto)"
    }
  },

  bookingConcept: {
    description: "Bookings = reservas/derivaciones anticipadas (diferente a ventas)",
    relationship: "nventas = ventas reales | Booking_total = pre-compromisos/reservas",
    metrics: {
      booking_4_dias: "Suma de Booking_total en ventana rolling de 4 días (señales corto plazo)",
      booking_7_dias: "Suma de Booking_total en ventana de 7 días (patrones semanales)",
      bookings_semana: "Rolling sum de 7 días de actividad de booking",
      peso_bookings_producto: "bookings_semana / total_bookings_semana (peso relativo)",
      relacion_booking_stock: "(peso_bookings / (Z_Y + 1)) × 1000"
    },
    criticalThreshold: "relacion_booking_stock > 7 → Activa Grupo 2 (presión crítica de demanda)",
    amplification: "Se amplifica cuando Z_Y es negativo (stock bajo + alta demanda = crisis)"
  },

  ventaRecurrente: {
    description: "Indica si producto tiene historial de ventas en farmacia específica",
    calculationPeriod: "Últimos 3 meses (suma ventas > 0)",
    values: {
      Y: {
        meaning: "Venta Recurrente - Producto vendido por farmacia en últimos 3 meses",
        recommendation: "Usa promedio_12_meses × factor_grupo - stock_actual (cálculo de calidad)",
        confidence: "Alta - basado en historial real de farmacia"
      },
      N: {
        meaning: "No Trabajado por Farmacia - Sin ventas en 3 meses",
        recommendation: "Usa tabla notworked_by_pharmacies.target_stock O promedio_global × 2",
        confidence: "Baja - estimación conservadora",
        ttl: "30 días (expira si no se actualiza)",
        onlyForGroup2: true
      }
    },
    businessLogic: "Grupo 2 puede incluir productos nuevos (N), Grupos 1/3 solo recurrentes (Y)"
  },

  systemTypes: {
    trends: {
      name: "Trends - Sistema Algorítmico",
      description: "Compra automática basada en grupos de riesgo y métricas",
      activation: "active = 1 en api_pharmacies",
      input: "trends_metrica_intermedia (grupos de riesgo) + carrito_compras (recomendaciones)",
      output: "historico_pedidos (órdenes trends)",
      filters: [
        "Blacklist (permanente y temporal)",
        "Parámetros farmacia (narcotics, max_pvp, fridge, freezer)",
        "EFG (grupos 1 y 3)",
        "Grupo 1 (configurable por farmacia)",
        "Bloqueo 24 horas (evita duplicados)"
      ],
      logic: "Recomendaciones filtradas con múltiples validaciones de negocio"
    },
    hunter: {
      name: "Hunter - Sistema Directo",
      description: "Pedidos manuales directos de farmacias",
      activation: "hunter_active = 1 en api_pharmacies",
      input: "cazador_entradas (productos solicitados manualmente)",
      output: "historico_pedidos_cazados (órdenes hunter)",
      filters: "Ninguno - pasa 1:1 (sin filtros algorítmicos)",
      logic: "Si farmacia lo pide, se envía cantidad completa",
      priority: "SOBRESCRIBE productos trends si ambos sistemas activos"
    },
    interaction: "Hunter tiene prioridad sobre Trends en cart final. Si ambos inactivos → cart vacío"
  },

  cartRecommendationFormulas: {
    description: "Fórmulas exactas para calcular unidades_propuestas por grupo",
    grupo1: {
      formula: "(promedio_12_meses × 1) - stock_actual",
      rationale: "Conservador - 1 mes de cobertura",
      condition: "Producto trabajado en últimos 3 meses (venta_recurrente = Y)"
    },
    grupo2: {
      formula: "(promedio_12_meses × security_stock) - stock_actual",
      securityStock: "Parámetro por farmacia [1-9], default = 4",
      fallback: "Si no trabajado: notworked_by_pharmacies.target_stock O promedio_global × 2",
      rationale: "Crítico - necesita buffer alto (4 meses típico)"
    },
    grupo3: {
      formula: "(promedio_12_meses × 2) - stock_actual",
      rationale: "Alta demanda - 2 meses de cobertura",
      condition: "Producto trabajado en últimos 3 meses"
    },
    grupos4y5: {
      formula: "Múltiplos escalados según emergencia",
      rationale: "Niveles de emergencia con factores mayores"
    },
    notWorkedFallback: {
      formula: "ceil(promedio_3_meses_global / distinct_pharmacies) × 2",
      ttl: "30 días desde última actualización",
      soloGrupo2: true
    }
  },

  timeWindows: {
    description: "Ventanas temporales usadas en cálculos",
    windows: {
      "4 días": "booking_4_dias - señales de corto plazo",
      "7 días": "booking_7_dias, bookings_semana - patrones semanales",
      "30 días": "nventas_mes - promedios mensuales",
      "3 meses": "sum_nventas_3 - filtro venta_recurrente",
      "12 meses": "sum_nventas_12 - baseline anual para recomendaciones",
      "365 días": "Ventana histórica completa procesada diariamente"
    },
    exclusions: "Excluye domingos (weekday != 6) y festivos nacionales españoles"
  },

  criticalThresholds: {
    description: "Umbrales clave que determinan comportamiento del sistema",
    stock: {
      "Z_Y entre -0.10 y -0.15": "GRUPO 1 - Inicio de problemas",
      "Z_Y entre -0.15 y -0.40": "GRUPO 2 - Desabastecimiento probable",
      "Z_Y entre -0.40 y -1.0": "GRUPO 3 - Desabastecido",
      "Z_Y < -1.0": "Crítico - más de 100% depleto",
      "Z_Y = 0": "Stock habitual (normal)",
      "Z_Y > 0": "Sobre-stock"
    },
    booking: {
      "relacion_booking_stock > 7": "Activa Grupo 2 (presión crítica de demanda)",
      "booking_7_dias ≥ 1": "Mínimo para calcular (con mediana > 900)"
    },
    mediana: {
      "Grupo 1": "≥ 600 unidades (mínimo mediana histórica)",
      "Grupos 2/3": "≥ 900 unidades (más exigente)"
    },
    ttl: {
      "notworked_by_pharmacies": "30 días (auto-limpieza)",
      "blacklist temporal": "Configurable con block_end_date",
      "bloqueo duplicados": "24 horas (pedido ayer/hoy)"
    },
    freshness: {
      "Stock válido": "MongoDB stockEvents debe tener flush=true y fecha >= ayer 7am",
      "Si stale": "TODOS los productos trends → 0 unidades (hunter no afectado)"
    }
  },

  dateRanges: {
    description: "Rangos de fechas comunes para análisis SQL",
    examples: {
      "última semana": "DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
      "último mes": "DATE_SUB(CURDATE(), INTERVAL 30 DAY)",
      "últimos 3 meses": "DATE_SUB(CURDATE(), INTERVAL 90 DAY)",
      "último año": "DATE_SUB(CURDATE(), INTERVAL 365 DAY)",
      "primer día mes actual": "DATE_FORMAT(CURDATE(), '%Y-%m-01')"
    }
  },

  processingDetails: {
    dailyUpdate: "trends_metrica_intermedia se calcula para T-1 (ayer) cada día",
    parallelProcessing: "1000 productos por chunk, hasta 16 CPUs",
    dataVolume: "stockEvents_* son tablas masivas (20GB+) particionadas por mes",
    mongoConnection: "Pool persistente (2-10 conexiones) para validación de frescura"
  }
};

/**
 * Generate a comprehensive prompt context for the LLM
 */
export function generateDomainPrompt(): string {
  return `
# SISTEMA DE ANÁLISIS FARMACÉUTICO - CONTEXTO DEL DOMINIO

Eres un asistente experto en análisis de datos farmacéuticos. Tu objetivo es traducir preguntas en lenguaje natural a consultas SQL precisas.

## CONTEXTO DEL NEGOCIO

Este sistema gestiona:
- **Inventario y ventas** de farmacias en tiempo real
- **Detección de riesgos** de desabastecimiento mediante ML
- **Recomendaciones automáticas** de compra (sistema Trends)
- **Búsqueda activa** de productos escasos (sistema Hunter)
- **Gestión de pedidos** a múltiples cooperativas/proveedores

## TABLAS PRINCIPALES Y SU USO

${DOMAIN_CONTEXT.map(table => `
### ${table.name}
**Propósito**: ${table.businessPurpose}

**Campos clave**:
${table.importantFields.map(field => `- \`${field.name}\`: ${field.businessMeaning}`).join('\n')}

**Consultas comunes**:
${table.commonQueries.map(q => `- ${q}`).join('\n')}

**Relaciones**:
${table.relationships.map(rel => `- → ${rel.relatedTable}: ${rel.description} (${rel.joinCondition})`).join('\n')}
`).join('\n')}

## PATRONES DE CONSULTA FRECUENTES

${QUERY_PATTERNS.map((pattern, idx) => `
### ${idx + 1}. ${pattern.category.toUpperCase()}: ${pattern.naturalLanguage[0]}

**Variantes en lenguaje natural**:
${pattern.naturalLanguage.map(nl => `- "${nl}"`).join('\n')}

**SQL Template**:
\`\`\`sql
${pattern.sqlTemplate}
\`\`\`

**Explicación**: ${pattern.explanation}
`).join('\n')}

## REGLAS DE NEGOCIO (BASADO EN CÓDIGO REAL)

### Grupos de Riesgo - Sistema de Máquina de Estados
**Algoritmo**: ${BUSINESS_RULES.riskGroups.algorithm}

${Object.entries(BUSINESS_RULES.riskGroups.levels).map(([k, v]: [string, any]) => `
**Grupo ${k}: ${v.name}**
- Condición: ${v.condition}
- Acción: ${v.action}
${v.minMediana ? `- Mediana mínima: ${v.minMediana} unidades` : ''}
${v.filterEFG !== undefined ? `- Filtro EFG: ${v.filterEFG ? 'SÍ aplica' : 'NO aplica'}` : ''}
${v.usesNotWorkedFallback ? '- Usa fallback notworked_by_pharmacies para productos nuevos' : ''}
${v.hysteresis ? `- ${v.hysteresis}` : ''}`).join('\n')}

**Máquina de Estados**: ${BUSINESS_RULES.riskGroups.stateMachine}

### Fórmula Z_Y - Métrica de Stock Normalizado
**${BUSINESS_RULES.zScoreFormula.description}**
- **Fórmula**: \`${BUSINESS_RULES.zScoreFormula.formula}\`
- **Cálculo Mediana**: ${BUSINESS_RULES.zScoreFormula.medianaCalculation}
- **Caso Especial**: ${BUSINESS_RULES.zScoreFormula.specialCase}

**Interpretación de valores**:
${Object.entries(BUSINESS_RULES.zScoreFormula.interpretation).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

**Métricas relacionadas**:
${Object.entries(BUSINESS_RULES.zScoreFormula.relatedMetrics).map(([k, v]) => `- \`${k}\`: ${v}`).join('\n')}

**Umbrales críticos**:
${Object.entries(BUSINESS_RULES.zScoreFormula.criticalThresholds).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

### Bookings - Concepto y Métricas
**${BUSINESS_RULES.bookingConcept.description}**
- ${BUSINESS_RULES.bookingConcept.relationship}

**Métricas calculadas**:
${Object.entries(BUSINESS_RULES.bookingConcept.metrics).map(([k, v]) => `- \`${k}\`: ${v}`).join('\n')}

**Umbral crítico**: ${BUSINESS_RULES.bookingConcept.criticalThreshold}
**Amplificación**: ${BUSINESS_RULES.bookingConcept.amplification}

### Venta Recurrente - Historial de Farmacia
**${BUSINESS_RULES.ventaRecurrente.description}**
- Periodo de cálculo: ${BUSINESS_RULES.ventaRecurrente.calculationPeriod}
- Lógica de negocio: ${BUSINESS_RULES.ventaRecurrente.businessLogic}

${Object.entries(BUSINESS_RULES.ventaRecurrente.values).map(([k, v]: [string, any]) => `
**'${k}': ${v.meaning}**
- Recomendación: ${v.recommendation}
- Confianza: ${v.confidence}
${v.ttl ? `- TTL: ${v.ttl}` : ''}
${v.onlyForGroup2 ? '- Solo aplicable a Grupo 2' : ''}`).join('\n')}

### Sistemas Trends vs Hunter

**${BUSINESS_RULES.systemTypes.trends.name}**
- ${BUSINESS_RULES.systemTypes.trends.description}
- Activación: ${BUSINESS_RULES.systemTypes.trends.activation}
- Input: ${BUSINESS_RULES.systemTypes.trends.input}
- Output: ${BUSINESS_RULES.systemTypes.trends.output}
- Filtros aplicados:
${BUSINESS_RULES.systemTypes.trends.filters.map((f: string) => `  - ${f}`).join('\n')}

**${BUSINESS_RULES.systemTypes.hunter.name}**
- ${BUSINESS_RULES.systemTypes.hunter.description}
- Activación: ${BUSINESS_RULES.systemTypes.hunter.activation}
- Input: ${BUSINESS_RULES.systemTypes.hunter.input}
- Output: ${BUSINESS_RULES.systemTypes.hunter.output}
- Filtros: ${BUSINESS_RULES.systemTypes.hunter.filters}
- **PRIORIDAD**: ${BUSINESS_RULES.systemTypes.hunter.priority}

**Interacción**: ${BUSINESS_RULES.systemTypes.interaction}

### Fórmulas de Recomendación por Grupo
**${BUSINESS_RULES.cartRecommendationFormulas.description}**

${Object.entries(BUSINESS_RULES.cartRecommendationFormulas).filter(([k]) => k !== 'description').map(([k, v]: [string, any]) => `
**${k.toUpperCase()}**:
- Fórmula: \`${v.formula}\`
- Rationale: ${v.rationale}
${v.condition ? `- Condición: ${v.condition}` : ''}
${v.securityStock ? `- Security Stock: ${v.securityStock}` : ''}
${v.fallback ? `- Fallback: ${v.fallback}` : ''}
${v.ttl ? `- TTL: ${v.ttl}` : ''}
${v.soloGrupo2 ? '- Solo para Grupo 2' : ''}`).join('\n')}

### Ventanas Temporales
**${BUSINESS_RULES.timeWindows.description}**
${Object.entries(BUSINESS_RULES.timeWindows.windows).map(([k, v]) => `- **${k}**: ${v}`).join('\n')}
- **Exclusiones**: ${BUSINESS_RULES.timeWindows.exclusions}

### Umbrales Críticos del Sistema
**${BUSINESS_RULES.criticalThresholds.description}**

**Stock (Z_Y)**:
${Object.entries(BUSINESS_RULES.criticalThresholds.stock).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

**Bookings**:
${Object.entries(BUSINESS_RULES.criticalThresholds.booking).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

**Mediana**:
${Object.entries(BUSINESS_RULES.criticalThresholds.mediana).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

**TTL y Expiraciones**:
${Object.entries(BUSINESS_RULES.criticalThresholds.ttl).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

**Frescura de Datos**:
${Object.entries(BUSINESS_RULES.criticalThresholds.freshness).map(([k, v]) => `- ${k}: ${v}`).join('\n')}

## INSTRUCCIONES PARA GENERAR SQL

1. **Identifica la intención**: ¿ventas? ¿riesgo? ¿pedidos? ¿disponibilidad?
2. **Usa las tablas correctas**: Consulta la sección de tablas arriba
3. **Aplica filtros relevantes**: fechas recientes por defecto (último mes)
4. **Incluye JOINs necesarios**: Siempre JOIN con \`items\` para nombres legibles
5. **Ordena resultados**: Por relevancia (ventas DESC, riesgo DESC, etc.)
6. **Limita resultados**: LIMIT 20-50 para evitar sobrecarga
7. **Usa nombres descriptivos**: Alias claros en SELECT

## TIPS IMPORTANTES

- **Fechas**: stockEvents_YYYY_MM está particionado por mes. Para consultas actuales usa la tabla del mes actual
- **Performance**: Para rangos largos, usa \`trends_consolidado\` en vez de \`stockEvents_*\`
- **Riesgo**: Combina \`trends_metrica_intermedia\` + \`trends_consolidado\` para análisis completo
- **Productos**: Siempre busca por \`description LIKE '%término%'\` (case insensitive)
- **Farmacias**: Usa \`pharmacy_id\` para identificar, pero JOIN con \`pharmacies.description\` para nombres

## EJEMPLOS DE TRADUCCIÓN

Usuario: "¿Qué medicamentos están en riesgo crítico?"
→ SELECT con trends_metrica_intermedia WHERE id_grupo = 4

Usuario: "Ventas del paracetamol este mes"
→ SELECT con trends_consolidado + items WHERE description LIKE '%paracetamol%' AND fecha >= primer día del mes

Usuario: "¿Qué debe comprar la farmacia FAR123?"
→ SELECT de carrito_compras WHERE pharmacy_id = 'FAR123'

Usuario: "Proveedores más confiables"
→ SELECT de historico_pedidos + cooperativas GROUP BY cooperativa calculando tasa cumplimiento
`;
}
