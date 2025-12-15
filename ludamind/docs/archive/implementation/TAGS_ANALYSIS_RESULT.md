# 📋 ANÁLISIS DE TAGS Y VERIFICACIÓN DE QUERY

**Fecha:** 20 Noviembre 2024

---

## 1️⃣ VERIFICACIÓN: ¿Revisa active=1?

### Tu nueva query:
```
"top 10 farmacias que mas venden en glovo que estén activas y en glovo a día de hoy"
```

### Lo que GPT generó (en la explanation):

**SÍ menciona revisar active:**
```javascript
{
  "$match": {
    "pharmacyDetails.active": true  // ← SÍ lo incluyó
  }
}
```

**✅ GPT SÍ entendió que debe filtrar por active=1**

**PERO:** La pipeline está dentro de "explanation" como texto, no como pipeline ejecutable.

**Necesita corrección en el parsing para ejecutar correctamente.**

---

## 2️⃣ ANÁLISIS DEL CAMPO TAGS

### Total de tags únicos encontrados: **48**

### TAGS POR PARTNER (Identificados):

#### Glovo
- `GLOVO` - **1,105 farmacias**
- `GLOVO-OTC_2H` - 44 farmacias
- `GLOVO-OTC_48H` - 44 farmacias

#### Procter
- `PROCTER_2H` - **2,035 farmacias**
- `PROCTER_48H` - **2,035 farmacias**
- `PROCTER_BACKUP` - 5 farmacias

#### Danone
- `DANONE_2H` - 650 farmacias
- `DANONE_48H` - 650 farmacias
- `DANONE_BACKUP` - 2 farmacias

#### Nutriben
- `NUTRIBEN_2H` - 715 farmacias
- `NUTRIBEN_48H` - 714 farmacias
- `NUTRIBEN_BACKUP` - 8 farmacias

#### Enna
- `ENNA_2H` - 651 farmacias
- `ENNA_48H` - 651 farmacias
- `ENNA_BACKUP` - 2 farmacias

#### Carrefour
- `CARREFOUR_2H` - 305 farmacias
- `CARREFOUR_48H` - 305 farmacias

#### Chiesi
- `CHIESI_48H` - 79 farmacias
- `CHIESI_BACKUP` - 79 farmacias

#### Amazon
- `AMAZON_2H` - 59 farmacias
- `AMAZON_48H` - 59 farmacias

#### Nordic
- `NORDIC_2H` - 38 farmacias
- `NORDIC_48H` - 38 farmacias
- `NORDIC_BACKUP` - 2 farmacias

#### Ferrer
- `FERRER_2H` - 16 farmacias
- `FERRER_48H` - 16 farmacias
- `FERRER_BACKUP` - 1 farmacia

#### Ludaalmacen
- `LUDAALMACEN_2H` - 26 farmacias
- `LUDAALMACEN_48H` - 26 farmacias

#### Rempe
- `REMPE_2H` - 5 farmacias
- `REMPE_48H` - 5 farmacias
- `REMPE_BACKUP` - 5 farmacias

#### ProcterClearBlue
- `PROCTERCLEARBLUE_2H` - 1 farmacia
- `PROCTERCLEARBLUE_48H` - 1 farmacia
- `PROCTERCLEARBLUE_BACKUP` - 1 farmacia

### TAGS ESPECIALES:

- `TRENDS` - 102 farmacias (¿sistema interno?)
- `envio-enero` - 86 farmacias (¿campaña?)
- `envio-covid` - 60 farmacias (campaña COVID)
- `savia-piloto` - 84 farmacias (piloto)
- `savia-piloto-2` - 19 farmacias (piloto)
- `trebol` - 42 farmacias (¿grupo?)
- `mascarillas` - 45 farmacias (campaña)
- `PilotoAlmeria112019` - 7 farmacias (piloto)
- `test` - 6 farmacias (test)
- `friend` - 3 farmacias (amigos?)
- `SinInstalaciones` - 14 farmacias (sin software?)
- `SinReportar` - 7 farmacias (problema?)
- `updateNotifAndJavaTo1.1.5` - 23 farmacias (actualización)

---

## ❓ PREGUNTAS PARA TI

### 1. **Tags de Partners - ¿Cuáles usar?**

Para buscar "farmacias en Glovo actualmente":
- ¿Usar tag `GLOVO`? (1,105 farmacias)
- ¿O también `GLOVO-OTC_2H` y `GLOVO-OTC_48H`? (44 farmacias)

Para otros partners:
- ¿`PROCTER_2H` significa Procter con entrega 2H?
- ¿`PROCTER_48H` significa Procter con entrega 48H?
- ¿`PROCTER_BACKUP` es backup del servicio?

### 2. **¿Qué significa _2H y _48H?**
- ¿Son tipos de entrega (2 horas vs 48 horas)?
- ¿Una farmacia con `GLOVO` puede recibir pedidos?
- ¿O necesita `GLOVO_2H` o `GLOVO_48H`?

### 3. **Tags a IGNORAR:**
- `envio-enero`, `envio-covid`, `mascarillas` ¿Ignorar? (campañas antiguas)
- `test`, `SinInstalaciones`, `SinReportar` ¿Ignorar? (problemas)
- `updateNotifAndJavaTo1.1.5` ¿Ignorar? (actualización técnica)

### 4. **Mapeo final:**

Por favor, dime para cada partner activo:

```
GLOVO → tags: ['GLOVO', ...?]
GLOVO-OTC → tags: ['GLOVO-OTC_2H', 'GLOVO-OTC_48H', ...?]
UBER → tags: [???]  ← NO vi tag UBER
JUSTEAT → tags: [???]  ← NO vi tag JUSTEAT
CARREFOUR → tags: ['CARREFOUR_2H', 'CARREFOUR_48H', ...?]
AMAZON → tags: ['AMAZON_2H', 'AMAZON_48H', ...?]
DANONE → tags: ['DANONE_2H', 'DANONE_48H', ...?]
PROCTER → tags: ['PROCTER_2H', 'PROCTER_48H', ...?]
ENNA → tags: ['ENNA_2H', 'ENNA_48H', ...?]
NORDIC → tags: ['NORDIC_2H', 'NORDIC_48H', ...?]
CHIESI → tags: ['CHIESI_48H', ...?]
FERRER → tags: ['FERRER_2H', 'FERRER_48H', ...?]
```

**¿Incluir BACKUP en cada uno?**

---

## 🎯 CON TU RESPUESTA

Actualizaré el diccionario semántico para añadir:

```python
"pharmacy_tags": FieldMapping(
    field_path="tags",
    collection="pharmacies",
    data_type="array",
    description="Tags que indican en qué partners está activa la farmacia",
    keywords=["activa en", "en glovo", "en uber", "disponible en"],
    synonyms={
        "glovo": ["GLOVO", "GLOVO-OTC_2H", ...],
        "uber": [...],
        ...
    }
)
```

Y GPT podrá buscar:
```javascript
// Farmacias activas en Glovo
{
  active: 1,
  tags: { $in: ["GLOVO", "GLOVO-OTC_2H", "GLOVO-OTC_48H"] }
}
```

---

**Esperando tu confirmación de qué tags usar para cada partner. 🙏**
