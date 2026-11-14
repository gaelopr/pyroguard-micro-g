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

Solo tres ítems son públicos y útiles:

| Ítem | Canal | Estado real |
|---|---|---|
| `USLAB000059` | temperatura de cabina (°C) | se publica |
| `USLAB000058` | presión de cabina (mmHg) | se publica |
| `TIME_000001` | GMT | se publica |

Los otros cinco canales del modelo (CO, CO2, HCN, humo, radiación) **no existen en el
feed público**. La app lo declara en la tarjeta de cobertura y en la nota de la pestaña.

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
