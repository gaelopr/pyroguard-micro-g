# PyroGuard Micro-G · Guion de presentación (5:00)

## Antes de empezar (2 min antes, no cuenta)

- [ ] `streamlit run app.py` corriendo → abrir `http://127.0.0.1:8501` en la pestaña de la demo.
- [ ] Modo **Simulador Físico Micro-G**, escenario **Nominal**, corte de ventilación **0**, atmósfera **ISS**, ventana **0–599**, **Playback apagado**.
- [ ] Navegador a zoom 100 %, ventana maximizada, notificaciones silenciadas.
- [ ] Tener a mano `demo_saffire_sintetico.csv` (en esta carpeta) para el cierre.
- [ ] Si vas a enseñar LIVE: pulsa **Conectar feed** ahora y déjalo; no esperes en directo.

---

## 0:00 – 0:30 · El problema (sin tocar la app)

> "En la ISS no hay gravedad, así que no hay convección: el aire caliente no sube. Un cable que empieza a arder no calienta el techo, calienta el propio cable. Por eso los detectores de humo y de temperatura llegan tarde. La NASA lo estudió en Saffire I–VI y en BASS. PyroGuard Micro-G es un prototipo que **puntúa el riesgo con lo que cambia antes**: la firma química — CO, CO2, HCN — y la radiación."

Aclarar en la primera frase: **"la telemetría de los simuladores es física simulada, no datos de vuelo; los canales LIVE sí son del feed público de la NASA."**

---

## 0:30 – 1:05 · Estado nominal

**Pantalla:** cabecera + 5 tarjetas + tab **TELEMETRÍA**.

> "Este es el estado sano: 23 °C estables, CO 2,8 ppm, CO2 4 100. El índice MIRI marca 19,9 % y el nivel es NOMINAL. El motor no tiene umbrales escritos a mano: aprende el baseline de los primeros 60 s y solo avisa cuando la telemetría se sale de esa distribución estadística."

Señalar: el cursor cian, la zona sombreada y que las gráficas son 600 muestras a 1 Hz.

---

## 1:05 – 2:00 · El caso Saffire — aquí está el número

**Clic:** sidebar → *Selector de escenario* → **Ventilation-Driven Flame Spread (Propagación Estilo NASA Saffire)**.

> "Quema sostenida por la corriente de ventilación: CO 192 ppm, CO2 casi 10 000, radiación 4,5 kW/m², humo 5,5 %/m. MIRI 98 %."

**Clic:** tab **DETECCIÓN IA**.

> "La línea verde es la primera alerta del modelo: **segundo 180**. La roja es el detector tradicional, el que mira temperatura y humo: **segundo 503**. Son **323 segundos de ventaja**. A 1 Hz eso es tiempo real para cerrar el rack antes de que el fuego viaje por la corriente de ventilación."

Si preguntan por la curva: IsolationForest sobre tasas suavizadas + MIRI determinista (35 % CO, 25 % O2, 15 % HCN, 15 % radiación, 10 % ventilación).

---

## 2:00 – 2:40 · Los dos fuegos que nadie ve

**Clic:** escenario **Smoldering Avionics (Pirólisis Latente de Cableado Kapton)**.

> "Temperatura 26,7 °C: ningún sensor térmico se mueve. Pero CO 88 ppm y HCN 12,4 — cianuro, de quemar aislamiento. El detector tradicional **nunca dispara**: la app escribe 'Detector Tradicional Ciego'. Nivel: CRÍTICO."

**Clic:** escenario **Cool Flame / Low-Temperature Oxidation (Llama Fría Invisible)**.

> "Llama fría: 23,4 °C, humo prácticamente cero, y aun así CO2 a 6 200 ppm. MIRI 50 %, PRE-IGNICIÓN. Ese es el incendio que ningún detector convencional ve hasta que ya arde."

---

## 2:40 – 3:15 · Qué hacer, no solo qué pasa

**Clic:** tab **PROTOCOLO EXPERTO**.

> "No dice 'hay humo'. Dice qué se apaga y en qué orden: aislamiento de ventilación, desenergizar las barras RPCM del rack, máscaras PBA si CO o HCN pasan umbral, descarga del extintor de CO2 sin abrir la puerta, y verificación con CSA-CP antes de reingresar. Es el flight rule convertido en texto operativo, generado desde los datos de esa quema concreta."

---

## 3:15 – 3:55 · Artemis y el mejor extintor en 0g

**Clic:** sidebar → *Selector de atmósfera* → **Lunar Gateway / Artemis (34.0 % O2 | 8.2 psi)**, escenario Saffire, **Corte de ventilación = 220 s**.

> "Misma quema, pero a 34 % de oxígeno y 56 kPa: la inflamabilidad y la propagación cambian ×1,65. Y ahora el corte de ventilación en el segundo 220. El CO cae de 192 a **33 ppm**, la radiación de 4,5 a **3,6**, la temperatura a 25 °C y el caudal termina en 0,3 cm/s. Sin convección forzada, la llama se sofoca en sus propios productos. **En microgravedad el mejor extintor es cerrar el aire** — y la app te enseña el porqué en la misma pantalla."

---

## 3:55 – 4:25 · LIVE: la parte honesta

**Clic:** modo **Live ISS (NASA · Lightstreamer)**.

> "Esto es el feed público real de la estación, sin credenciales. Y aquí está lo que casi nadie hace: de los 8 canales que necesita el modelo, la NASA solo publica temperatura y presión de cabina. No hay CO, ni humo, ni radiación en abierto. Por eso la app **no puntúa MIRI sobre esto**: declara la cobertura, dice qué falta y no inventa ninguna cifra."

Si hay datos: señalar las muestras reales y la hora UTC.
Si no hay: "el enlace está abierto y suscrito, pero NASA no está publicando valores; la app lo dice en vez de rellenar el hueco."

Opcional (10 s): activar **Completar canales ausentes con el modelo físico** →

> "Y si quieres ver el motor completo, se puede: lo inferido va en trazo discontinuo, en ámbar, y las métricas se etiquetan como modelo. Nunca se mezcla con lo medido."

---

## 4:25 – 5:00 · CSV real y cierre

**Clic:** modo **Subir Dataset Real (CSV NASA OSDR / Saffire)** → subir `demo_saffire_sintetico.csv`.

> "Un fichero de fuera entra con las unidades crudas: kelvin, fracción molar, W/m². La app detecta unidades, valida rangos y publica un informe de mapeo: 7 de 8 canales, y el que falta declarado como nominal. Aquí MIRI 65 %, CO 175 ppm, y la alerta llega en el segundo 111 frente al 183 del detector tradicional: **72 segundos**."

> "Y si el fichero no trae temperatura o gases, **se niega a analizar**. Ese fue el fallo más peligroso que encontré: un CSV real que el mapeador antiguo convertía en 'estado nominal' durante una quema de verdad. Preferimos no responder a responder mal."

**Cierre:**

> "Todo corre en local, sin API keys, de forma determinista: los mismos datos dan siempre el mismo diagnóstico. El objetivo no es predecir el fuego, es ganar los segundos en los que la tripulación todavía puede actuar."

---

## Números de referencia (memorizar)

| Escenario | MIRI | Temp | CO | Dato clave |
|---|---|---|---|---|
| Nominal | 19,9 % | 23,0 °C | 2,8 ppm | NOMINAL |
| Smoldering | 59,1 % | 26,7 °C | 88 ppm | HCN 12,4 · tradicional CIEGO |
| Saffire | 98,0 % | 30,8 °C | 192 ppm | IA 180 s vs 503 s → **+323 s** |
| Cool Flame | 50,1 % | 23,4 °C | 60 ppm | humo 0,21 · PRE-IGNICIÓN |
| AEA + corte 220 s | — | 25,3 °C | 33 ppm | rad 4,51 → 3,60 |
| CSV demo | 65,5 % | 49,9 °C | 175 ppm | IA 111 s vs 183 s → **+72 s** |

## Plan B

| Si pasa esto | Haz esto | Di esto |
|---|---|---|
| NASA no publica valores | No esperes; sigue | "El feed está suscrito y sin datos: la app no rellena el hueco" |
| La app se queda rara | F5 y volver a **Simulador / Nominal** | "Recargo, el estado por defecto es el nominal" |
| Preguntan "¿son datos reales?" | Señala la etiqueta de cada panel | "Simulación física aquí, feed real aquí, tu CSV aquí" |
| Se acaba el tiempo | Salta el bloque LIVE | El cierre con CSV + ventaja temporal es lo que se recuerda |

## Preguntas probables

- **¿Por qué IsolationForest?** No existen series etiquetadas de incendios reales en 0g; el modelo aprende el baseline nominal sin supervisión y se reentrena con cada dataset.
- **¿MIRI es científico?** Es un índice compuesto ponderado (35/25/15/15/10), determinista y auditable — no un modelo validado en vuelo. Sirve para priorizar, no para certificar.
- **¿Falsos positivos?** Umbral a 4σ del baseline y exigencia de persistencia de 3 muestras antes de declarar alerta.
- **¿Sirve con datos de Saffire reales?** Sí, por CSV: el mapeador acepta el formato de PSI/Saffire con unidades crudas y rechaza lo que no puede validar.
- **¿Dónde está el límite?** No hay sensores de CO/HCN/humo en el feed público de la ISS; sin esos canales el motor no puede puntuar de verdad.
