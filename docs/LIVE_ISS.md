# Modo LIVE

`iss_live.py` implementa un cliente **TLCP** (el protocolo de Lightstreamer sobre HTTP)
con `http.client`, sin dependencias añadidas. Se conecta al feed público de la NASA
(`push.lightstreamer.com`, adapter set `ISSLIVE`), sin credenciales.

## Protocolo, paso a paso

1. `GET /lightstreamer/create_session.txt` con `LS_polling=false` **abre el stream**:
   la respuesta queda conectada y por ahí llegan los eventos. Sin `LS_polling=false`
   la sesión es de sondeo y no sirve.
2. Sobre esa primera línea llega `CONOK,<session>,...`.
3. En una conexión aparte, `GET /lightstreamer/control.txt` con
   `LS_op=add&LS_subId=1&LS_group=...&LS_schema=value&LS_data_adapter=` → `SUBOK,1,1,1`.
   (`LS_data_adapter` debe omitirse: con valor vacío el servidor responde `REQERR,17`.)
4. Cada actualización llega como `U,1,<item>,<value>`. Un valor nulo llega como `#`.

Detalles que costaron encontrar: los POST a `.txt` devuelven 400 (hay que usar GET), y
`create_session` es en sí mismo el canal de eventos.

## Canales

El catálogo público (`PUBLIC_SENSORS` en `iss_live.py`) cubre 12 ítems agrupados en tres
packs que se pueden suscribir por separado:

| Pack | Canales | Ítems |
|---|---|---|
| **Atmósfera (fuego)** | temp. de cabina, presión de cabina, ppO2, ppCO2, ppN2 | `USLAB000059`, `USLAB000058`, `USLAB000053`, `USLAB000055`, `USLAB000054` |
| **Térmico** | fluido de aviónica, fluido de refrigeración de aire, refrigerante LT y MT | `USLAB000060`, `USLAB000061`, `USLAB000056`, `USLAB000057` |
| **Soporte vital** | depósito de orina, aguas residuales, agua limpia (Node 3) | `NODE3000005`, `NODE3000008`, `NODE3000009` |

**Derivados.** Con `ppO2` / `ppCO2` y la presión de cabina se calculan O2 en % y CO2 en ppm
(`o2_pct_from_pp`, `co2_ppm_from_pp`): son conversiones de magnitudes medidas, no sensores,
y la app las presenta como derivadas.

Los canales que el modelo de incendio necesita y **no** existen en el feed público son CO,
HCN, caudal de ventilación, opacidad de humo y flujo radiativo. La app lo declara en la
tarjeta de cobertura y en la nota de la pestaña.

## Opciones de prueba

- **Grupo de canales** (tres packs o «Todo») y selección manual de canales: cambiar la
  lista cierra la sesión anterior y abre una nueva con esa suscripción.
- **Frecuencia máxima**: sin límite, 2, 1 o 0.2 Hz (`LS_requested_max_frequency`).
- **Snapshot inicial**: pide el último valor conocido al suscribir.
- **Probar (10 s)**: abre una sesión temporal contra NASA y devuelve, por canal, cuántos
  frames traen número y cuántos llegan nulos. Es la forma de saber si el feed está
  emitiendo *ahora mismo*, sin esperar a la gráfica.
- **Diagnóstico por canal**: tabla con contadores de la sesión en curso —números, nulos,
  último valor y hora— para distinguir «suscrito pero mudo» de «sin datos todavía».

## Datos nulos

La NASA abre el feed pero a veces publica `#` en lugar de valores: la suscripción se
acepta y no llega ninguna muestra. La app lo dice ("enlace abierto y suscripción
aceptada, pero NASA no está publicando valores") y no inventa cifras. Por eso
`0 muestras medidas · 360 filas inferidas` es un estado normal, no un error.

## Buffer y reconexión

- Cada muestra se guarda como `{seq, utc, channel, value}`; `seq` es un contador
  incremental porque `time.time()` en Windows tiene resolución de ~15 ms y colisionaría.
- `frame()` pivota el buffer a formato ancho y calcula `t` (segundos desde la primera
  muestra) y `utc` ISO 8601.
- Ante error de socket, el cliente reintenta con backoff exponencial hasta 20 s y
  vuelve a suscribir; `stop()` envía `LS_op=destroy` y cierra la sesión.
- `start()` es idempotente y la instancia se comparte por servidor
  (`st.cache_resource`): recargar la página no abre otra sesión contra NASA.

## Inferencia (opcional y etiquetada)

Si se activa el interruptor, los canales ausentes se estiman con `physics_simulator`:

- Van en **trazo discontinuo**, en una tarjeta ámbar titulada "Inferencia del modelo ·
  no son mediciones".
- La temperatura se ancla al último valor realmente medido, si existe.
- Las métricas de esa sección se etiquetan como de modelo.
- Los canales medidos **nunca** se sustituyen.

## Registro de sesión

Exportable a CSV en formato largo, una fila por muestra y canal:

`utc`, `elapsed_s`, `channel`, `unit`, `value`, `source` (`measured` / `inferred`),
`detail` (ítem de NASA, sesión, estado).

En las filas inferidas `utc` va vacío a propósito: no existe hora de pared para algo
que no se midió.

## Límites

- Depende de un servicio de terceros sin SLA: si Lightstreamer cambia, el modo LIVE cae
  (la app muestra el error y reintenta).
- El feed no trae CO/HCN/humo/radiación: sin ellos **no se puede** puntuar MIRI sobre
  datos reales, y la app no lo finge.
