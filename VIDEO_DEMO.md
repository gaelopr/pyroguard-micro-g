# Vídeo demo · 3 minutos

Guion para grabar hoy. **332 palabras de voz** ≈ 2:20 a ritmo normal (medido); con las
pausas y las transiciones de pantalla llega a **2:55–3:00**. Grábalo en **6 tomas separadas** y
únelas: es mucho más rápido que buscar la toma perfecta.

## Antes de grabar (10 min)

- [ ] App **despierta** en la pestaña del navegador: ábrela 5 minutos antes.
- [ ] Modo **Simulador**, escenario **Nominal**, corte **0**, atmósfera **ISS**, ventana **0–599**, playback **apagado**.
- [ ] Navegador a 100 % de zoom, barra de marcadores oculta, notificaciones silenciadas, solo esa pestaña.
- [ ] Grabación a **1920 × 1080**, 30 fps. Micrófono a un palmo, sin ventilador cerca.
- [ ] Graba la voz **por separado** (después, sobre la imagen): si te trabas, repites solo el audio.
- [ ] Ten a mano `demo_saffire_sintetico.csv` para la toma 6.

> Graba sobre la **app desplegada** (`pyrogaurdmicrog.streamlit.app`) para que el vídeo
> coincida con lo que el jurado abrirá. Si va con retardo, usa la local: la interfaz es idéntica.

## Tomas

### Toma 1 · El problema (0:00 – 0:18) · pantalla: cabecera, sin tocar nada

> "En la Estación Espacial Internacional no hay gravedad, así que no hay convección: el
> aire caliente no sube. Un cable que empieza a arder no calienta el techo, calienta el
> propio cable. Por eso los detectores de humo y de temperatura llegan tarde."

### Toma 2 · La idea y el usuario (0:18 – 0:50) · pantalla: veredicto y **ESTADO**

> "PyroGuard Micro-G mira lo que cambia antes: la química del aire. Cada segundo puntúa
> CO, CO2, HCN y radiación, y lo compara con cómo era todo en los primeros 60 segundos de
> operación normal. Sin datos etiquetados: aprende lo nominal y avisa cuando se sale. Lo
> usa una controladora de carga que tiene que decidir en segundos si eso es ruido del
> sensor o el principio de un incendio."

*Acción:* mueve despacio el **cursor temporal** una vez, para que se vea que todo cambia a la vez.

### Toma 3 · El caso Saffire (0:50 – 1:30) · el momento clave

*Acción:* escenario → **Ventilation-Driven Flame Spread**. Espera a que se redibuje.
Luego tab **DETECCIÓN**.

> "Esto es una quema de propagación por ventilación, el escenario tipo Saffire: MIRI 98 %,
> crítico. Y aquí está el argumento del proyecto. La línea verde es la primera alerta del
> modelo: segundo 180. La roja, un detector convencional de temperatura y humo: segundo
> 503. Trescientos veintitrés segundos de ventaja."

*Edición:* haz **zoom al gráfico** (150 %) durante esta frase — es el número que se recuerda.

### Toma 4 · Los fuegos que nadie ve (1:30 – 2:05)

*Acción:* escenario → **Smoldering Avionics**, luego **Cool Flame**.

> "Pero el caso que importa es el que no se ve. Pirólisis de cableado: 26,7 grados,
> ningún sensor térmico se mueve, pero CO 88 ppm y HCN 12,4. El detector convencional no
> dispara nunca. Y llama fría: 23,4 grados, humo casi cero, CO2 a 6 200. El modelo lo
> marca en pre-ignición."

### Toma 5 · Qué hacer (2:05 – 2:35) · tab **RESPUESTA**, luego corte

*Acción:* tab **RESPUESTA**; después, escenario Saffire con **corte de ventilación = 220**.

> "Y no solo dice qué pasa: dice qué hacer, en orden. Cortar la ventilación es la acción
> número uno. Se puede probar: con corte en el segundo 220, el CO baja de 192 a 33 ppm.
> En microgravedad, cerrar el aire es el mejor extintor."

### Toma 6 · Honestidad y cierre (2:35 – 3:00)

*Acción:* modo **Subir Dataset Real** → sube `demo_saffire_sintetico.csv` → se ve el
informe "7 de 8 canales". Después, volver a **Simulador · Nominal**.

> "La app también lee el feed público de la NASA en vivo: doce canales, y declara cuáles
> traen dato de verdad. Los que faltan no existen en abierto, y no los inventa. Acepta
> además CSV externos, detecta unidades y se niega a analizar si falta lo mínimo. Todo es
> local, determinista y con un protocolo de 270 corridas en verde. No predice el fuego: gana los segundos en
> los que todavía puedes actuar."

**Cierre en negro con una línea de texto:** `PyroGuard Micro-G · github.com/gaelopr/pyroguard-micro-g`
y debajo, en pequeño: `NASA Space Apps Challenge 2026`.

## Reglas de grabación

- **No grabes el modo LIVE** salvo que ya tenga datos: si NASA publica nulos, en vídeo parece un fallo. Menciónalo con la voz (toma 6), no con la imagen.
- Nunca muestres la terminal ni el panel de Streamlit.
- Movimientos de ratón **lentos y en línea recta**; una pausa de medio segundo después de cada clic.
- Si te trabas en una frase, no reinicies: corta y empalma.
- Subtítulos quemados con las cifras clave: `+323 s`, `98 %`, `CO 192 → 33 ppm`. Muchos jurados ven el vídeo sin sonido.

## Exportación

MP4 · H.264 · 1080p · audio AAC 128 kbps. Nombra el archivo `pyroguard_demo.mp4`.
Súbelo a YouTube como **"no listado"** y pega el enlace en el formulario: es lo que menos
falla y lo que el jurado espera encontrar.
