# Instrucciones para Probar ChatGPT

## 📋 Paso 1: Copiar el Prompt de Entrenamiento

Ve a ChatGPT y copia TODO el contenido del archivo:
```
C:\Users\dgfre\Documents\trends_mcp\docs\CHATGPT_TRAINING_PROMPT.md
```

Pégalo en ChatGPT con este mensaje inicial:

---

**Mensaje inicial a ChatGPT:**

```
Lee y aprende este documento de entrenamiento sobre el sistema de bases de datos LudaFarma. Es crítico que entiendas la diferencia entre MySQL y MongoDB para responder queries correctamente.

[PEGAR AQUÍ TODO EL CONTENIDO DE CHATGPT_TRAINING_PROMPT.md]

Cuando termines de leer, confirma tu entendimiento respondiendo las 6 preguntas del "Test Final" al final del documento.
```

---

## ✅ Paso 2: Validar que ChatGPT Entendió

Espera a que ChatGPT responda el "Test Final" con las 6 preguntas:

**Respuestas esperadas:**
1. "GMV de Glovo este mes" → **MongoDB**
2. "Ventas de Ibuprofeno" (sin canal) → **MySQL**
3. "Ibuprofeno en Glovo" → **MongoDB**
4. "GMV de derivaciones" → **Filtrar por origin**
5. ¿Glovo es comprador o canal? → **Canal de venta**
6. ¿Shortage es un partner? → **NO, es servicio (origin EXISTS)**

Si ChatGPT responde correctamente las 6, continúa al Paso 3.

---

## 🎯 Paso 3: Hacer la Pregunta de Prueba

Una vez validado el entrenamiento, hazle esta pregunta exacta:

```
GMV que se ha movido en Glovo la última semana
```

---

## 📊 Paso 4: Evaluar la Respuesta

### ✅ Respuesta Correcta Esperada:

ChatGPT debería decir algo como:

```
Para responder esta pregunta, necesito usar MongoDB (no MySQL) porque
mencionas "Glovo", que es un canal de venta/partner.

El proceso es:

1. Buscar en la colección 'users' el partner Glovo:
   db.users.findOne({ idUser: "glovo" })
   Esto me dará el ObjectId del usuario Glovo

2. Con ese ObjectId, buscar todos los bookings creados por Glovo
   en la última semana en la colección 'bookings':
   - Filtrar por: creator = glovo_id
   - Filtrar por: createdDate >= hace 7 días
   - Excluir cancelados: state != "5a54c525b2948c860f00000d"

3. Calcular el GMV sumando pvp * quantity de todos los items:
   GMV = SUM(items[i].pvp * items[i].quantity)

Query MongoDB:
[Debería mostrar un aggregate similar al del documento de entrenamiento]
```

**Puntos clave que DEBE mencionar:**
- ✅ Usar MongoDB (no MySQL)
- ✅ Glovo es un partner/canal
- ✅ Buscar en users primero
- ✅ Luego bookings con creator = glovo_id
- ✅ Calcular GMV de items (pvp * quantity)

---

### ❌ Respuesta Incorrecta (lo que NO debería hacer):

```
Para calcular el GMV de Glovo, necesito consultar la base de datos
MySQL en la tabla de ventas...

SELECT SUM(importe) FROM ventas_diarias WHERE proveedor = 'Glovo'...
```

**Errores que indicarían falta de entrenamiento:**
- ❌ Usar MySQL en vez de MongoDB
- ❌ Buscar en tablas de ventas
- ❌ Tratar a Glovo como un producto
- ❌ No mencionar la colección users
- ❌ No calcular GMV de items

---

## 📝 Paso 5: Documentar Resultados

Copia la respuesta completa de ChatGPT y evalúa:

### Checklist de Evaluación:

- [ ] ¿Eligió MongoDB? (SÍ/NO)
- [ ] ¿Mencionó que Glovo es un partner/canal? (SÍ/NO)
- [ ] ¿Dijo que buscaría en `users` primero? (SÍ/NO)
- [ ] ¿Mencionó `bookings.creator`? (SÍ/NO)
- [ ] ¿Explicó cálculo de GMV de items? (SÍ/NO)
- [ ] ¿Mencionó excluir cancelados? (SÍ/NO)
- [ ] ¿Evitó mencionar MySQL/ventas_*? (SÍ/NO)

**Puntuación:**
- 7/7 → ✅ Entrenamiento perfecto
- 5-6/7 → ⚠️ Entrenamiento bueno, pequeñas correcciones
- 3-4/7 → ⚠️ Necesita refuerzo
- 0-2/7 → ❌ Entrenamiento no funcionó

---

## 🔄 Paso 6: Si Falló el Entrenamiento

Si ChatGPT no respondió correctamente, usa este prompt de corrección:

```
Tu respuesta es incorrecta. Has cometido estos errores:

[Listar los errores específicos]

Por favor, revisa la sección "[SECCIÓN ESPECÍFICA]" del documento de
entrenamiento y vuelve a responder la pregunta correctamente.

Recuerda la REGLA DE ORO:
¿Menciona CANAL (Glovo, Uber, shortage)? → MongoDB bookings
¿NO menciona canal? → MySQL trends_consolidado
```

---

## 📊 Comparación: Claude vs ChatGPT

### Mi Respuesta (Claude):
- ✅ Database: MongoDB
- ✅ Razonamiento: Glovo = partner/canal
- ✅ Proceso: users → bookings
- ✅ Cálculo: SUM(items[].pvp * quantity)
- ✅ Filtros: creator, createdDate, state

### Respuesta de ChatGPT (registrar aquí):
- Database: _______
- Razonamiento: _______
- Proceso: _______
- Cálculo: _______
- Filtros: _______

---

## 🎯 Preguntas Adicionales de Prueba (Opcional)

Si ChatGPT responde correctamente la primera, prueba con estas:

1. **"Ventas totales de Ibuprofeno"**
   - Esperado: MySQL trends_consolidado

2. **"Cuántas unidades de Paracetamol se vendieron en Glovo"**
   - Esperado: MongoDB bookings (canal + producto)

3. **"GMV de derivaciones del último mes"**
   - Esperado: MongoDB bookings WHERE origin EXISTS

4. **"Comparar ventas de Aspirina en Glovo vs shortage"**
   - Esperado: 2 queries MongoDB (una por canal)

5. **"Top 10 productos más vendidos en Uber Eats"**
   - Esperado: MongoDB bookings WHERE creator = uber

---

## ✅ Conclusión

**El entrenamiento es exitoso si:**
- ChatGPT distingue correctamente cuándo usar MongoDB vs MySQL
- Identifica partners como canales de venta
- Entiende que shortage se identifica por `origin`
- Calcula GMV correctamente de items
- Usa el proceso de 2 pasos (users → bookings)

**Resultado del test:**
- [ ] ✅ Entrenamiento exitoso
- [ ] ⚠️ Necesita correcciones menores
- [ ] ❌ Necesita reentrenamiento completo

**Fecha del test**: _________________
**Versión de ChatGPT**: _________________
**Notas adicionales**: _________________
