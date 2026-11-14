# Checklist de entrega

> Todo lo que hay que comprobar y pegar antes del **domingo a las 23:59**.
> Cada cosa está verificada salvo lo marcado como *tu parte*.

## Enlaces

| Qué | Enlace |
|---|---|
| **App en vivo** | https://pyrogaurdmicrog.streamlit.app |
| **Repositorio** | https://github.com/gaelopr/pyroguard-micro-g |
| Guion de 5 min | [GUION_DEMO.md](GUION_DEMO.md) |
| Wireframe | [docs/img/wireframe.png](docs/img/wireframe.png) · [versión navegable](docs/wireframe.html) |
| Dataset de demo | [demo_saffire_sintetico.csv](demo_saffire_sintetico.csv) |

## 30 minutos antes

- [ ] Abrir la app y dejarla despierta: si lleva horas sin visitas, el primer acceso tarda 30–60 s.
- [ ] Comprobar que carga el veredicto y las tres pestañas (`ESTADO`, `DETECCIÓN`, `RESPUESTA`).
- [ ] Comprobar que el repo abre en una ventana de incógnito (es público, pero conviene verlo sin sesión).
- [ ] Ver el badge de tests en verde en la portada del repo.
- [ ] Tener el wireframe y una captura de la app descargados, por si falla la red en la presentación.
- [ ] **No hacer `git push` durante la presentación**: cada push redespliega la app.

## Lo que se envía

| Campo del formulario | Qué poner |
|---|---|
| Título | **PyroGuard Micro-G** |
| Enlace al proyecto | la URL de la app |
| Repositorio | la URL del repo |
| Vídeo / demo | *(tu parte: si el formulario pide vídeo, grábalo con el guion de 5 min)* |
| Evidencia de participación del sábado | *(tu parte: fotos, capturas o el registro del equipo)* |

## Texto corto (para "descripción" o "resumen")

> PyroGuard Micro-G detecta el inicio de un incendio en microgravedad antes de que lo
> note cualquier sensor térmico. Sin gravedad no hay convección: el calor no sube hasta
> el detector, pero la química del aire cambia primero. La app puntúa CO, CO2, HCN y
> radiación con un modelo entrenado a bordo sobre los primeros 60 s de operación
> nominal, y en el escenario de propagación tipo Saffire avisa en el segundo 180 frente
> al 503 de un detector convencional: **323 segundos de ventaja**. Incluye telemetría
> real de la ISS, protocolo de respuesta en cinco pasos y lectura de CSV con validación
> de unidades y rangos.

## Texto largo (para "¿qué hace tu proyecto?")

> En la ISS no hay flotabilidad: el aire caliente no asciende, así que un cable que
> empieza a arder no calienta el techo, calienta el propio cable. Los detectores de humo
> y temperatura llegan tarde. PyroGuard Micro-G ataca ese retraso mirando lo que cambia
> antes: la firma química.
>
> La app simula 600 s de telemetría a 1 Hz de un EXPRESS Rack (inercia térmica,
> ventilación forzada, corte de ventilación y dos atmósferas: ISS y Artemis), entrena un
> IsolationForest **sin datos etiquetados** sobre los primeros 60 s de operación normal,
> y combina esa puntuación con MIRI, un índice determinista y explicable que pesa CO,
> pérdida de O2, HCN, radiación y caudal de ventilación.
>
> El resultado se compara con un detector tradicional de temperatura y humo: en la
> propagación tipo Saffire, el modelo avisa en el segundo 180 y el convencional en el
> 503. En pirólisis de cableado y en llama fría el detector convencional **nunca**
> avisa, porque la temperatura no sube. El corte de ventilación en el segundo 220 baja
> el CO de 192 a 33 ppm: en 0 g, cerrar el aire es la maniobra de supresión más eficaz.
>
> La app lee además el feed público **ISSLIVE** de NASA JSC y declara en pantalla qué
> canales publica la NASA de verdad (temperatura y presión) y cuáles no existen en
> abierto: no rellena huecos ni presenta datos inferidos como medidos.

## Texto para "¿cómo usa datos de la NASA?"

> Se usa un recurso de datos de la NASA **en vivo**: el feed público de NASA JSC
> (`push.lightstreamer.com`, adapter set `ISSLIVE`), del que la app suscribe temperatura
> (`USLAB000059`) y presión (`USLAB000058`) de cabina del US Lab, con marca temporal
> GMT. Se consulta desde el servidor de la app, sin credenciales.
>
> Como referencia de comportamiento —no como dataset crudo— se citan las campañas
> **Saffire I–VI** y **BASS** sobre propagación de llama en microgravedad. El dataset de
> demostración del repositorio es sintético y se llama así a propósito.

## English (si el formulario está en inglés)

> **PyroGuard Micro-G** spots the onset of a fire in microgravity before any thermal
> sensor does. Without buoyancy the heat never rises to the detector, but the air
> chemistry changes first. The app scores CO, CO2, HCN and radiative flux with a model
> trained onboard-style on the first 60 s of nominal operation, and in a Saffire-like
> spread it alerts at second 180 versus 503 for a conventional detector — **323 seconds
> of lead time**. It also streams live NASA ISSLIVE telemetry, generates a five-step
> response protocol, and refuses to analyse CSVs missing mandatory channels.

## Comprobado hoy

- App desplegada y verificada **desde una sesión anónima** (ventana de incógnito): carga el veredicto y las tres pestañas. Modo LIVE y subida de CSV probados a mano en el dominio público.
- Repositorio público en `master`, 8 commits, README con badges y 12 secciones.
- **23 tests** en verde en local (3 s) y en GitHub Actions (`success`).
- Documentación: persona, diseño, arquitectura, modelo físico, motor IA, mapeo de datos, LIVE (7 documentos) + wireframe.
- Cifras del guion fijadas por la suite: 19,9 / 59,1 / 98,0 / 50,1 · +323 s · CO 192→33 · CSV +72 s.

## Riesgos y plan B

| Riesgo | Plan B |
|---|---|
| La app está dormida al enseñarla | Abrirla 30 min antes; si aun así tarda, narrar mientras carga |
| La URL dice `pyrogaurd` (typo) | Compartir el enlace, nunca dictarlo; está tal cual en el formulario |
| El feed LIVE no publica valores | Es el punto de honestidad del guion: la app lo declara y no inventa |
| Se cae la red en la presentación | Capturas descargadas + wireframe + guion impreso |
| `curl` devuelve **303** hacia `share.streamlit.io/-/auth/app` | Es normal: Streamlit crea la sesión y vuelve a la app. Comprobado en incógnito: carga bien. No significa que sea privada |
| Preguntan por la validación | "Formato sí, dataset real de Saffire todavía no" — está en los límites del README |
