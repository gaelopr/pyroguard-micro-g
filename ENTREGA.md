# Checklist de entrega

> Todo lo que hay que comprobar y pegar antes del **domingo a las 23:59**.
> Cada cosa está verificada salvo lo marcado como *tu parte*.

## Paso 0 · Renombrar el subdominio (2 min, hazlo primero)

La app se desplegó como `pyrogaurdmicrog` (con errata) y la documentación ya apunta a
`pyroguard-micro-g`. Streamlit **no redirige** la URL vieja, así que el renombrado tiene
que hacerse antes de enviar o los enlaces de la entrega darán 404.

1. Entra en <https://share.streamlit.io> → tu app → menú **⋮** → **Settings**.
2. Pestaña **General** → **Custom subdomain** → escribe `pyroguard-micro-g` → **Save**.
   (Mínimo 6 caracteres; ya está comprobado que ese subdominio está libre.)
3. La app se redespliega sola. Verifica en incógnito:
   <https://pyroguard-micro-g.streamlit.app> debe abrir el veredicto.
4. Si no puedes renombrar, **revierte las 4 apariciones** de la URL nueva (README ×2,
   ENTREGA, VIDEO_DEMO) y envía con la vieja: es fea, pero funciona.

## Enlaces

| Qué | Enlace |
|---|---|
| **App en vivo** | https://pyroguard-micro-g.streamlit.app |
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
| Demo para el formulario | **30 s** con el guion corto de [VIDEO_DEMO.md](VIDEO_DEMO.md); súbelo a YouTube (público o no listado) y pega la URL completa |
| Vídeo de presentación | 3 min con el guion largo de [VIDEO_DEMO.md](VIDEO_DEMO.md): 332 palabras, 6 tomas |
| Uso de SI | marcar *Writing/Editing/Translation*, *Coding/Debugging/Troubleshooting* y *Research/Information Gathering*; la declaración está en el README, sección «Uso de herramientas de IA» |
| Datos de la NASA | ISSLIVE (Lightstreamer) y las tres investigaciones de PSI (Saffire I/II/III), con URL completa |
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
> el CO de 192 a 34 ppm: en 0 g, cerrar el aire es la maniobra de supresión más eficaz.
>
> La app lee además el feed público **ISSLIVE** de NASA JSC y declara en pantalla qué
> canales publica la NASA de verdad (temperatura, presión y las presiones parciales de
> O2 y CO2, entre otros) y cuáles no existen en abierto: no rellena huecos ni presenta
> datos inferidos como medidos.

## Texto para "¿cómo usa datos de la NASA?"

> Se usan **dos recursos de la NASA**, los dos públicos y sin credenciales:
>
> 1. **En vivo**: el feed de NASA JSC (`push.lightstreamer.com`, adapter set `ISSLIVE`).
>    La app suscribe 12 canales del US Lab y Node 3 —temperatura, presión de cabina,
>    presiones parciales de O2, CO2 y N2, refrigerantes y aguas— y declara cuáles traen
>    dato real en cada sesión.
> 2. **Histórico**: el repositorio **PSI** (`psi.nasa.gov`) sirve por API pública las
>    tablas experimentales de **Saffire-I, II y III** (licencia CC0). La app las descarga
>    en vivo, muestra el DOI, el tamaño y el SHA-256 de lo descargado, y no las mezcla
>    con el modelo porque son matrices de experimento, no telemetría de cabina.
>
> El feed de la ISS es solo en vivo: no existe histórico público. El dataset de
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
- **28 tests** en verde en local (13 s) y en GitHub Actions (`success`), incluido el protocolo
  de validación: 180/180 detecciones con 0 falsas alarmas en 90 corridas sin fuego
  (`python validation.py`, detalle en [`docs/VALIDACION.md`](docs/VALIDACION.md)).
- Documentación: persona, diseño, arquitectura, modelo físico, motor IA, mapeo de datos, LIVE (7 documentos) + wireframe.
- Cifras del guion fijadas por la suite: 19,9 / 59,1 / 98,0 / 50,1 · +323 s · CO 192→34 · CSV +72 s.

## Riesgos y plan B

| Riesgo | Plan B |
|---|---|
| La app está dormida al enseñarla | Abrirla 30 min antes; si aun así tarda, narrar mientras carga |
| Aún no has renombrado el subdominio | La URL nueva da 404: haz el **Paso 0** o revierte las 4 URLs a `pyrogaurdmicrog` antes de enviar |
| El feed LIVE no publica valores | Es el punto de honestidad del guion: la app lo declara y no inventa |
| Se cae la red en la presentación | Capturas descargadas + wireframe + guion impreso |
| `curl` devuelve **303** hacia `share.streamlit.io/-/auth/app` | Es normal: Streamlit crea la sesión y vuelve a la app. Comprobado en incógnito: carga bien. No significa que sea privada |
| Preguntan por la validación | "Formato sí, dataset real de Saffire todavía no" — está en los límites del README |
