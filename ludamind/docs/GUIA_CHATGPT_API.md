# Guía: Cómo Garantizar Routing Correcto con ChatGPT API

## 🎯 El Problema

Cuando usas ChatGPT por API, **cada llamada es independiente**. No hay memoria entre llamadas.

| Método | Memoria | Costo Tokens | Implementación |
|--------|---------|--------------|----------------|
| **Chat Web** | ✅ Guarda contexto | Solo primera vez | Manual |
| **API** | ❌ Sin memoria | En cada llamada | Automático |

**El problema**: Si entrenas ChatGPT en una conversación web, ese entrenamiento **NO se transfiere** a las llamadas API.

---

## 💡 Soluciones

### **Opción 1: System Prompt en Cada Llamada** ⭐ RECOMENDADO

**Ventajas:**
- ✅ Funciona inmediatamente
- ✅ Fácil de actualizar
- ✅ Sin costo adicional de entrenamiento
- ✅ Consistente en cada llamada

**Desventajas:**
- ⚠️ Consume ~600 tokens por llamada (~$0.001/llamada con GPT-4)
- ⚠️ Ligeramente más lento

**Cómo funciona:**
```python
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {
            "role": "system",
            "content": LUDAFARMA_SYSTEM_PROMPT  # ← Se incluye en CADA llamada
        },
        {
            "role": "user",
            "content": "GMV de Glovo última semana"
        }
    ]
)
```

**Archivo**: `EJEMPLO_USO_API.py` (líneas 17-64)

---

### **Opción 2: Fine-Tuning**

**Ventajas:**
- ✅ Modelo permanentemente entrenado
- ✅ No consume tokens del system prompt
- ✅ Respuestas más rápidas
- ✅ Más preciso para casos complejos

**Desventajas:**
- ❌ Costo inicial de entrenamiento (~$10-20)
- ❌ Necesita mínimo 10 ejemplos de calidad
- ❌ Más difícil de actualizar
- ❌ Costo por uso del modelo fine-tuneado

**Cómo funciona:**
1. Crear dataset de entrenamiento (archivo `.jsonl`)
2. Subir a OpenAI
3. Entrenar modelo (toma ~20 minutos)
4. Usar el modelo personalizado

**Archivo**: `FINE_TUNING_DATASET.jsonl` (20 ejemplos listos)

**Comandos:**
```bash
# 1. Subir dataset
openai files create -f FINE_TUNING_DATASET.jsonl -p fine-tune

# 2. Crear fine-tuning job
openai fine-tuning create -t <file-id> -m gpt-3.5-turbo

# 3. Usar modelo entrenado
openai.ChatCompletion.create(
    model="ft:gpt-3.5-turbo:tu-org:modelo-luda:abc123",
    messages=[{"role": "user", "content": "GMV de Glovo"}]
)
```

---

### **Opción 3: Híbrido** (System Prompt Compacto)

**Mejor de ambos mundos:**
- System prompt MUY corto (~100 tokens vs 600)
- Solo incluye la regla esencial

**Archivo**: `EJEMPLO_USO_API.py` (líneas 114-124)

```python
COMPACT_PROMPT = """Routing LudaFarma:
MongoDB si menciona: Glovo, Uber, Danone, Carrefour, shortage, derivación
MySQL si NO menciona canal (analytics general)

Partners (MongoDB): users.findOne({idUser}), luego bookings.creator
Shortage (MongoDB): bookings.origin EXISTS
GMV: SUM(items[].pvp * quantity)"""
```

**Ventajas:**
- ✅ Solo ~$0.0002/llamada (5x más barato)
- ✅ Suficiente para casos simples
- ✅ Más rápido que versión completa

**Desventajas:**
- ⚠️ Menos contexto, puede fallar en casos complejos

---

## 📊 Comparación de Costos

| Opción | Costo Setup | Costo por Llamada | Total (1000 llamadas) |
|--------|-------------|-------------------|----------------------|
| **System Prompt Completo** | $0 | ~$0.001 | **$1.00** |
| **System Prompt Compacto** | $0 | ~$0.0002 | **$0.20** |
| **Fine-Tuning** | $10-20 | ~$0.0005 | **$10.50** |

*Precios estimados con GPT-4. GPT-3.5-turbo es ~10x más barato.*

---

## 🎯 Recomendación por Caso de Uso

### **Si haces < 10,000 llamadas/mes:**
→ **Opción 1**: System Prompt Completo
- Más fácil de implementar
- Más flexible para actualizar
- Costo total bajo

### **Si haces > 10,000 llamadas/mes:**
→ **Opción 2**: Fine-Tuning
- Ahorro significativo en tokens
- Modelo más preciso
- Vale la pena la inversión inicial

### **Si necesitas respuesta rápida:**
→ **Opción 3**: System Prompt Compacto
- Mínimo overhead
- Funciona para casos simples
- Muy económico

---

## 🚀 Implementación Paso a Paso

### OPCIÓN 1: System Prompt (Más Simple)

**Paso 1:** Copia el system prompt
```bash
# Abre el archivo
notepad C:\Users\dgfre\Documents\trends_mcp\docs\API_SYSTEM_PROMPT.txt
```

**Paso 2:** Úsalo en tu código
```python
# Ver archivo completo: EJEMPLO_USO_API.py
from openai import ChatCompletion

SYSTEM_PROMPT = """[Copiar contenido de API_SYSTEM_PROMPT.txt]"""

response = ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query_del_usuario}
    ]
)
```

**Paso 3:** ¡Listo! Ya funciona.

---

### OPCIÓN 2: Fine-Tuning (Más Avanzado)

**Paso 1:** Preparar dataset
```bash
# Ya está listo en:
C:\Users\dgfre\Documents\trends_mcp\docs\FINE_TUNING_DATASET.jsonl
```

**Paso 2:** Subir a OpenAI
```bash
openai files create \
  -f C:\Users\dgfre\Documents\trends_mcp\docs\FINE_TUNING_DATASET.jsonl \
  -p fine-tune
```

**Paso 3:** Crear fine-tuning job
```bash
openai fine-tuning create \
  -t file-abc123 \
  -m gpt-3.5-turbo \
  --suffix "ludafarma-routing"
```

**Paso 4:** Esperar entrenamiento (~20 minutos)
```bash
# Ver progreso
openai fine-tuning list
```

**Paso 5:** Usar modelo entrenado
```python
response = openai.ChatCompletion.create(
    model="ft:gpt-3.5-turbo:tu-org:ludafarma-routing:abc123",
    messages=[
        {"role": "user", "content": "GMV de Glovo"}
    ]
)
# ← Ya no necesita system prompt, está entrenado!
```

---

## ✅ Cómo Validar que Funciona

### Test Rápido (3 preguntas):

```python
# Test 1: Debe elegir MongoDB
test_query("GMV de Glovo última semana")
# ✅ Esperado: "MongoDB porque menciona Glovo (canal)"

# Test 2: Debe elegir MySQL
test_query("Ventas totales de Ibuprofeno")
# ✅ Esperado: "MySQL porque no menciona canal"

# Test 3: Debe elegir MongoDB
test_query("Paracetamol en Glovo")
# ✅ Esperado: "MongoDB porque menciona Glovo + producto"
```

**Si las 3 respuestas son correctas → ✅ Funciona bien**

---

## 📂 Archivos de Referencia

| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `API_SYSTEM_PROMPT.txt` | System prompt completo | Opción 1 |
| `EJEMPLO_USO_API.py` | Código Python de ejemplo | Implementación |
| `FINE_TUNING_DATASET.jsonl` | Dataset para fine-tuning | Opción 2 |
| `CHATGPT_TRAINING_PROMPT.md` | Documentación completa | Referencia |

Todos en: `C:\Users\dgfre\Documents\trends_mcp\docs\`

---

## 🎓 Resumen Ejecutivo

### **Para garantizar que ChatGPT API siempre gestione bien las peticiones:**

**1. Incluir System Prompt en CADA llamada API** (Opción 1)
   - Es la solución más simple y efectiva
   - El prompt se "resetea" en cada llamada
   - Garantiza consistencia

**2. O entrenar un modelo personalizado** (Opción 2)
   - Más costoso pero permanente
   - Mejor para alto volumen

**3. El entrenamiento en chat web NO se transfiere a la API**
   - Son sistemas completamente separados
   - El chat web tiene contexto de conversación
   - La API es stateless (sin estado)

### **Solución Recomendada:**

```python
# Esto garantiza que SIEMPRE funcione:
SYSTEM_PROMPT = """[Reglas de routing]"""

# En CADA llamada:
openai.ChatCompletion.create(
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},  # ← CLAVE
        {"role": "user", "content": user_query}
    ]
)
```

**Costo**: ~$0.001 por llamada (muy económico)
**Implementación**: 5 minutos
**Mantenimiento**: Fácil actualizar el prompt

---

## 🔗 Siguiente Paso

1. **Probar Opción 1 primero** (System Prompt)
2. Si funciona bien → Listo
3. Si tienes alto volumen → Considerar Opción 2 (Fine-tuning)

**Código listo para usar**: `EJEMPLO_USO_API.py`

---

*Cualquier duda, revisa los ejemplos en los archivos mencionados.*
