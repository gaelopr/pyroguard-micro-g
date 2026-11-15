# Guion de la presentación · PyroGuard Micro-G

Dos piezas, un solo mensaje: **la química del aire avisa antes que el calor**.

| Pieza | Archivo | Duración |
|---|---|---|
| Diapositivas (7, el máximo que permite el formulario) | [`presentacion.html`](presentacion.html) | 4 min hablado |
| Guion corto para el vídeo de la demo | este documento, §3 | 30 s |

---

## 1. Cómo usar el deck

- Abre `docs/presentacion.html` en el navegador (`docs/img/…` debe quedar al lado).
- **→ / espacio** avanza, **←** retrocede, **clic** en la mitad derecha/izquierda también, **P** imprime.
- Para el PDF que se sube al formulario: **Ctrl+P → Guardar como PDF → Orientación horizontal → Márgenes: ninguno**.
  Sale una diapositiva por página (ya está forzado en el CSS).
- Si el proyector es 4:3, no cambies nada: el deck se escala solo y no recorta texto.
- **Antes de grabar:** sustituye el `01 / 07` por vuestro nombre de equipo si el formulario lo pide (una línea en el `<div class="foot">` de la primera diapositiva).

---

## 2. Versión de 4 minutos (presentación en vivo)

> Habla a ~150 palabras por minuto. Los corchetes son acciones, no texto.

### D1 · Portada — 0:00–0:20
> «Buenos días. Soy [nombre], del equipo [equipo], y esto es **PyroGuard Micro-G**.
> Detectamos incendios en microgravedad usando lo que primero cambia en una cabina presurizada:
> **la química del aire**, no el calor.
> Tres números que resumen el proyecto: **325 segundos de ventaja**, **180 de 180 detecciones**
> y **cero falsas alarmas en 90 corridas sin fuego**.»

### D2 · El problema — 0:20–1:05
> «En la Tierra el fuego se delata solo: el aire caliente sube, el humo llega al techo y el detector
> de allí lo huele. **En órbita eso no ocurre.** Sin gravedad no hay flotabilidad, así que el aire
> caliente se queda pegado al cable que arde. Un detector de techo espera un cambio físico que puede
> tardar minutos… o no llegar.
> Lo que sí cambia de inmediato es el aire: monóxido de carbono, CO₂, cianuro de hidrógeno, radiación.
> Y hay un agravante que se ve en los experimentos Saffire de la NASA: la llama **no se apaga sola**,
> se sostiene con la ventilación del rack. Veinte centímetros por segundo de corriente de aire bastan
> para alimentarla.
> Ese desfase entre "la química ya cambió" y "el detector se enteró" es exactamente lo que este
> proyecto convierte en segundos de actuación.»

### D3 · Qué construimos — 1:05–1:50
> «La app hace tres cosas y ninguna es una caja negra.
> Primero, un índice propio, **MIRI**, que combina CO, pérdida de oxígeno, HCN, radiación y caudal.
> Es determinista: con las mismas muestras da el mismo número, y se puede explicar línea a línea.
> Segundo, un **IsolationForest** que se entrena a bordo, en la propia sesión, con los primeros
> sesenta segundos nominales. No necesita datos etiquetados de incendios reales, que además no existen
> en abierto.
> Y tercero, lo que de verdad importa: el veredicto usa **solo las muestras hasta el cursor**.
> [mueve el cursor] No anuncia un incendio que todavía no ha empezado; si retrocedes, retrocede con
> vosotros. Y cuando el riesgo sube, no te deja un número: te da **la siguiente acción** del protocolo
> de cinco pasos. Cerrar el aire es el mejor extintor que hay en órbita.»

### D4 · La prueba — 1:50–2:40
> «Esto no es una demo bonita, es un protocolo que se puede repetir: `validation.py`, doscientas
> setenta corridas, treinta por caso, cada una con ruido distinto.
> [señala las barras] En una propagación tipo Saffire, la IA avisa a los **178 segundos**; un detector
> de umbrales fijos, a los 503. **325 segundos de ventaja**, y con muy poca dispersión: más menos 7.
> En aire enriquecido al 34 % de oxígeno, la ventaja baja a 226 segundos, porque todo ocurre antes.
> [señala la tabla] En los seis casos de incendio, la IA detecta los 180. El clásico **es ciego en
> cuatro de los seis**: no ve la pirólisis de Kapton ni la llama fría, que son justo los fuegos
> incipientes que queremos cazar.
> Y en las 90 corridas sin fuego —incluido el corte de ventilación, que es un transitorio real de
> cabina— hay **cero falsas alarmas**. AUC de 1,000.
> Una advertencia honesta: esto está medido sobre el simulador físico del proyecto, no sobre un
> incendio real en la ISS. Volveré a eso en la última diapositiva.»

### D5 · Datos de la NASA — 2:40–3:20
> «Dos fuentes reales, ninguna inventada.
> **ISSLIVE**: consumimos en vivo doce canales públicos del laboratorio US y del Node 3. Y cuando NASA
> no publica algo —no hay CO, no hay HCN, no hay humo— la app **lo dice en pantalla** en vez de
> rellenarlo con ruido.
> **PSI**, el programa de incendios en vuelo: las tablas de Saffire I, II y III son de dominio público,
> y las descargamos en vivo con su DOI, su tamaño y su SHA-256, para que cualquiera pueda comprobar que
> no hemos tocado nada.
> Y de ahí sale el dato que más me gusta: con el **mismo 22 % de oxígeno**, la silicona se apaga sola
> —cero centímetros quemados— y la tela SIBAL se consume entera, 29 centímetros en 145 segundos.
> **Lo que decide no es el oxígeno: es el material.**»

### D6 · Ingeniería — 3:20–3:45
> «Todo corre en local. Cero claves de API, cero telemetría saliendo de la app: se puede enseñar en
> una sala sin red.
> Cuatro modos: simulador, ISSLIVE en vivo, histórico PSI y **tu propio CSV**.
> El CSV no se acepta a ciegas: se validan unidades —kelvin o Fahrenheit, fracción o porcentaje o ppm,
> metros por segundo, vatios por metro cuadrado—, rangos y canales mínimos. Si falta lo imprescindible,
> la app **se niega a diagnosticar**. Prefiero un "no puedo" a un veredicto inventado.
> 34 tests en integración continua y el cliente del protocolo de Lightstreamer escrito a mano, sin
> dependencias.»

### D7 · Impacto y límites — 3:45–4:15
> «¿Dónde encaja? En la telemetría de un rack presurizado de la ISS, y en arquitecturas tipo Gateway o
> Artemis, donde el oxígeno sube al 34 % y los márgenes se estrechan. No pretende sustituir a los
> detectores certificados: **los adelanta**. Les da los dos minutos que hoy se pierden.
> Y los límites, dichos sin adornos: es un prototipo, **no está certificado para volar**; la telemetría
> de los escenarios es simulación física, no una medida de vuelo; y el feed público de la ISS no trae
> CO, HCN, humo ni flujo radiativo, así que en modo LIVE la app declara lo que le falta.
> Está desplegada en pyroguardmicrog punto streamlit punto app, el código es MIT y está en GitHub.
> Gracias.»

**Cierre de seguridad:** si te sobra tiempo, la frase que se queda es la de la D2:
*«en el espacio el fuego no sube, así que hay que escucharlo en el aire»*.

---

## 3. Versión de 30 segundos (vídeo de la demo)

> Una frase por diapositiva, sin respirar entre ellas. 30 s exactos.

| t | Diapositiva | Lo que dices |
|---|---|---|
| 0:00 | D1 | «En el espacio el fuego no sube: no hay flotabilidad.» |
| 0:04 | D2 | «El aire caliente se queda en el cable y el detector del techo espera.» |
| 0:09 | D2 | «Lo que sí cambia primero es la química del aire.» |
| 0:13 | D3 | «PyroGuard lee CO, oxígeno, HCN y radiación, y da un veredicto por segundo.» |
| 0:18 | D4 | «325 segundos antes que los umbrales fijos, con cero falsas alarmas en 90 pruebas.» |
| 0:24 | D6 | «Todo local, sin claves, con datos públicos de la NASA.» |
| 0:27 | D7 | «PyroGuard Micro-G: los segundos en los que todavía puedes actuar.» |

---

## 4. Demo en vivo: la ruta de clics

Si presentas con la app abierta (mejor que capturas, y si falla la red tienes el vídeo):

1. **Abre la app 10 minutos antes** y deja que despierte: <https://pyroguardmicrog.streamlit.app>.
2. Empieza en **Simulador**, escenario *Nominal Operations*: el veredicto dice **NOMINAL, ~6 %**.
   Ese es el estado sano, y conviene enseñarlo para que el contraste signifique algo.
3. Activa **Pico MIRI**: el anillo salta a **98 %**, el estado pasa a **CRÍTICO** y aparece la acción
   recomendada. Un clic, un cambio de estado, cero explicaciones.
4. Mueve el **cursor** hacia atrás: el veredicto vuelve a NOMINAL. Es la prueba visual de que no hay
   mirar al futuro — si el fuego no ha ocurrido todavía, la app no lo sabe.
5. Si hay tiempo, **Reproducir 8×** para ver la progresión y el **corte de ventilación** para enseñar
   que un transitorio de cabina no dispara la alarma.
6. **No subas un CSV en vivo** salvo que sea el momento: es el punto más frágil de una demo con wifi.
   Menciónalo de palabra («acepta tu propio CSV y valida unidades») y sigue.

**Si algo se cuelga:** *«la app está despertando; mientras tanto, esto es lo que sale»* → capturas
`docs/img/publico.png` y `docs/img/ia.png`, que están en el deck.

---

## 5. Preguntas probables (y respuestas honestas)

**«¿Esto está validado con datos reales de incendio?»**
> «El formato sí: las tablas PSI de Saffire son reales y están citadas con DOI. La serie temporal de
> los escenarios es del simulador físico del proyecto. Un dataset público de incendio en microgravedad,
> segundo a segundo, con CO y HCN, no existe: por eso el motor aprenda sin etiquetas.»

**«¿Por qué no usáis un modelo más grande?»**
> «Porque en una cabina no quieres una caja negra. MIRI se explica con cinco términos y el
> IsolationForest se entrena en la sesión con 60 segundos de datos nominales: cero dependencia de
> datos de entrenamiento que no tenemos y cero llamadas a un servidor.»

**«¿Y si el detector clásico sí funciona?»**
> «En propagación, sí: llega a los 503 segundos y lo detecta. El problema son los otros cuatro casos de
> seis, donde es ciego. Nuestra propuesta no lo sustituye: lo adelanta. Y no sustituimos su certificación
> con una demo.»

**«¿Qué falta para volar?»**
> «Tres cosas, en este orden: un banco de datos de vuelo con CO y HCN, un análisis de falsos positivos
> con transitorios reales —cambios de filtro, maniobras de actitud— y certificación. El código está
> separado para que el índice y el detector se puedan auditar por partes.»

**«¿Cómo evitáis que la IA se equivoque con el corte de ventilación?»**
> «Ese es el caso que metimos a propósito en la validación: 30 corridas con el ventilador cortado y sin
> fuego. Cero alarmas. El caudal entra en MIRI como término, así que la app distingue "el aire se
> paró" de "el aire se está quemando".»

**«¿Usasteis IA para hacer esto?»**
> «Sí, y está declarado en el README y en el formulario: asistencia de IA en código, textos y este deck.
> Los datos son de la NASA y las cifras salen de ejecutar `validation.py`, no de una respuesta de
> modelo.»

---

## 6. Reglas de honestidad para no romper nada

- Nunca digas **«medido en la ISS»** refiriéndote a la serie temporal: es simulación.
- Di **«cero falsas alarmas en 90 corridas»**, no «cero falsas alarmas» a secas.
- La ventaja es **325 s** en atmósfera ISS y **226 s** en AEA: si alguien pregunta, distingue.
- Si te piden el dato de CO, es **192 → 34 ppm** en ISS y **316 → 54 ppm** en AEA con corte de
  ventilación. No los mezcles.
