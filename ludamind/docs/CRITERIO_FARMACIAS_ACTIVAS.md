# ✅ CRITERIO DE FARMACIAS ACTIVAS - VALIDADO

**Fecha:** 20 Noviembre 2024

---

## 🎯 CRITERIO PROPUESTO

**"Farmacia activa en [Partner] = tiene pedido del partner en últimos 7 días"**

---

## 📊 VALIDACIÓN CON UBER

### Query Ejecutada:
```javascript
db.bookings.aggregate([
    {
        $match: {
            "thirdUser.user": "uber",
            "createdDate": { $gte: últimos_7_días }
        }
    },
    {
        $group: {
            _id: "$target",  // Farmacias únicas
            total_pedidos: { $sum: 1 },
            total_gmv: { $sum: ... }
        }
    },
    ...lookup pharmacies para verificar active...
])
```

### Resultados:

| Métrica | Valor |
|---------|-------|
| **Farmacias con pedidos Uber** | 249 |
| **Activas (active=1)** | 241 (96.8%) |
| **Inactivas (active=0)** | 8 (3.2%) |
| **Total pedidos** | 1,012 |
| **GMV total** | €25,275.40 |

### Top 10 Farmacias Uber (por pedidos):
1. FARMACIA MIGUEL REYES 24H (Madrid) - 61 pedidos, €1,431.63
2. FARMACIA JOSE VICENTE BELLVER 24H (Madrid) - 48 pedidos, €1,060.23
3. FARMACIA CLAPES 24H (Barcelona) - 31 pedidos, €1,164.73
4. FARMACIA 24H MORATALAZ (Madrid) - 29 pedidos, €687.52
5. FARMACIA MAYOR 24H (Madrid) - 26 pedidos, €978.40
... (hasta 10)

---

## ✅ CONCLUSIÓN

**CRITERIO VALIDADO:**

- ✅ **96.8%** de farmacias con pedidos recientes están activas
- ✅ Solo **3.2%** están inactivas (probablemente recién desactivadas)
- ✅ El criterio es **confiable y preciso**

**RECOMENDACIÓN:** Usar este criterio para partners SIN tags (Uber, Justeat)

---

## 🔍 COMPARACIÓN: Tags vs Pedidos Recientes

### Glovo (tiene tags):

| Criterio | Farmacias |
|----------|-----------|
| **Tag 'GLOVO' + active=1** | 1,059 |
| **Pedidos Glovo últimos 7 días** | 638 |
| **Diferencia** | 421 (40%) |

**Interpretación:**
- El **tag** indica farmacias **registradas** en Glovo
- Los **pedidos recientes** indican farmacias **realmente activas**
- 421 farmacias tienen el tag pero **no han recibido pedidos** en 7 días

---

## 💡 CRITERIOS RECOMENDADOS

### Para Partners CON Tags (Glovo, Procter, Danone, etc.):

**Opción A:** Tag + Active
```javascript
{
  tags: { $in: ["GLOVO", "GLOVO-OTC_2H", ...] },
  active: 1
}
```
**Ventaja:** Más farmacias (registradas)  
**Desventaja:** Puede incluir inactivas

**Opción B:** Tag + Active + Pedidos Recientes
```javascript
{
  tags: { $in: ["GLOVO"] },
  active: 1,
  _id: { $in: [farmacias_con_pedidos_ultimos_7_dias] }
}
```
**Ventaja:** Solo farmacias realmente activas  
**Desventaja:** Más complejo

**Opción C:** Solo Pedidos Recientes (como Uber)
```javascript
// Farmacias con pedidos en últimos 7 días
```
**Ventaja:** Más preciso  
**Desventaja:** Ignora el tag

### Para Partners SIN Tags (Uber, Justeat):

**Único criterio:** Pedidos en últimos 7 días
```javascript
{
  bookings con thirdUser.user = "uber",
  createdDate >= últimos_7_días
}
```

---

## ❓ DECISIÓN NECESARIA

**¿Qué criterio prefieres para partners CON tags?**

- A) Tag + active=1 (más farmacias, menos preciso)
- B) Tag + active + pedidos recientes (preciso, más complejo)
- C) Solo pedidos recientes (como Uber, ignorar tags)

**¿Qué tags usar para cada partner?** (Ver TAGS_ANALYSIS_RESULT.md)

---

**Una vez decidas, actualizaré el diccionario semántico. 🙏**

---

*Validación completada el 20/11/2024*
