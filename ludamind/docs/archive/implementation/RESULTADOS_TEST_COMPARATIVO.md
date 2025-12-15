# Test Comparativo - Queries FASE 1

**Fecha:** 2025-12-09T19:07:15.730366

## Resumen Ejecutivo

Este documento compara la ejecución de queries predefinidas en diferentes modos:
1. **Hardcoded**: Pipeline MongoDB directo (queries predefinidas)
2. **OpenAI**: Pipeline generado por GPT-4o-mini

---

## Farmacias por provincia

### Modo Hardcoded

**Pipeline:**
```json
[{"$match": {"active": 1}}, {"$group": {"_id": "$contact.province", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
```

- **Tiempo:** 84.44 ms
- **Resultados:** 60 registros
- **Muestra (primeros 5):**
```json
[
  {
    "_id": "Madrid",
    "count": 684
  },
  {
    "_id": "Barcelona",
    "count": 379
  },
  {
    "_id": "Valencia",
    "count": 174
  },
  {
    "_id": "Alicante",
    "count": 150
  },
  {
    "_id": "Málaga",
    "count": 101
  }
]
```

### Modo OpenAI (gpt-4o-mini)

**Query en lenguaje natural:** "Cuántas farmacias hay por provincia"

**Pipeline generado:**
```json
[{"$match": {"active": 1}}, {"$group": {"_id": "$contact.province", "count": {"$sum": 1}}}]
```

- **Tiempo:** 2999.14 ms
- **Resultados:** 60 registros
- **Muestra (primeros 5):**
```json
[
  {
    "_id": "Città metropolitana di Roma Capitale",
    "count": 2
  },
  {
    "_id": "Lérida",
    "count": 1
  },
  {
    "_id": "Castellón",
    "count": 3
  },
  {
    "_id": "Teruel",
    "count": 3
  },
  {
    "_id": "Soria",
    "count": 2
  }
]
```

---

## Porcentaje farmacias activas

### Modo Hardcoded

**Pipeline:**
```json
[{"$facet": {"activas": [{"$match": {"active": 1}}, {"$count": "count"}], "totales": [{"$count": "count"}]}}]
```

- **Tiempo:** 66.87 ms
- **Resultados:** 1 registros
- **Muestra (primeros 5):**
```json
[
  {
    "activas": [
      {
        "count": 2642
      }
    ],
    "totales": [
      {
        "count": 4848
      }
    ]
  }
]
```

### Modo OpenAI (gpt-4o-mini)

**Query en lenguaje natural:** "Qué porcentaje de farmacias están activas vs inactivas"

**Pipeline generado:**
```json
[{"$group": {"_id": "$active", "count": {"$sum": 1}}}, {"$group": {"_id": null, "activeCount": {"$sum": {"$cond": [{"$eq": ["$_id", 1]}, "$count", 0]}}, "inactiveCount": {"$sum": {"$cond": [{"$eq": ["$_id", 0]}, "$count", 0]}}}}, {"$project": {"activePercentage": {"$multiply": [{"$divide": ["$activeCount", {"$add": ["$activeCount", "$inactiveCount"]}]}, 100]}, "inactivePercentage": {"$multiply": [{"$divide": ["$inactiveCount", {"$add": ["$activeCount", "$inactiveCount"]}]}, 100]}}}]
```

- **Tiempo:** 5202.48 ms
- **Resultados:** 1 registros
- **Muestra (primeros 5):**
```json
[
  {
    "_id": null,
    "activePercentage": 54.496699669967,
    "inactivePercentage": 45.503300330033
  }
]
```

---

## Farmacias por ciudad

### Modo Hardcoded

**Pipeline:**
```json
[{"$match": {"active": 1}}, {"$group": {"_id": "$contact.city", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 20}]
```

- **Tiempo:** 67.5 ms
- **Resultados:** 20 registros
- **Muestra (primeros 5):**
```json
[
  {
    "_id": "Madrid",
    "count": 436
  },
  {
    "_id": "Barcelona",
    "count": 185
  },
  {
    "_id": "València",
    "count": 77
  },
  {
    "_id": "Sevilla",
    "count": 69
  },
  {
    "_id": "Málaga",
    "count": 40
  }
]
```

### Modo OpenAI (gpt-4o-mini)

**Query en lenguaje natural:** "Top 20 ciudades con más farmacias activas"

**Pipeline generado:**
```json
[{"$match": {"active": 1}}, {"$group": {"_id": "$contact.city", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 20}]
```

- **Tiempo:** 2621.36 ms
- **Resultados:** 20 registros
- **Muestra (primeros 5):**
```json
[
  {
    "_id": "Madrid",
    "count": 436
  },
  {
    "_id": "Barcelona",
    "count": 185
  },
  {
    "_id": "València",
    "count": 77
  },
  {
    "_id": "Sevilla",
    "count": 69
  },
  {
    "_id": "Málaga",
    "count": 40
  }
]
```

---

## Tabla Comparativa de Métricas

| Query | Hardcoded (ms) | OpenAI (ms) | Diferencia |
|-------|---------------|-------------|------------|
| Farmacias por provincia | 84.4 | 2999.1 | +2915 |
| Porcentaje farmacias activas | 66.9 | 5202.5 | +5136 |
| Farmacias por ciudad | 67.5 | 2621.4 | +2554 |
| **TOTAL** | **218.8** | **10823.0** | **+10604** |

**Speedup:** Las queries hardcodeadas son **49.5x más rápidas** que las generadas por OpenAI.

## Conclusiones

1. **Rendimiento**: Las queries hardcodeadas son significativamente más rápidas al evitar la latencia de la API de OpenAI.
2. **Consistencia**: Las queries hardcodeadas siempre producen el mismo pipeline, garantizando resultados predecibles.
3. **Costo**: Las queries hardcodeadas no consumen tokens de API, reduciendo costos operativos.
4. **Flexibilidad**: OpenAI permite queries en lenguaje natural sin programación previa.

## Recomendación

Usar el **modo híbrido**:
- Queries frecuentes → Hardcodeadas (rápidas, consistentes, sin costo)
- Queries ad-hoc/exploratorias → OpenAI (flexibles, lenguaje natural)
