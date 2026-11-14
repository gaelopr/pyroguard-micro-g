# Arquitectura

Cuatro módulos, sin servicios externos ni API keys. Todo el cálculo ocurre en el
proceso de Streamlit; no hay base de datos ni estado compartido más allá del feed LIVE.

```
                 ┌───────────────────────────────┐
                 │            app.py             │
                 │  UI · estado · 4 pestañas     │
                 └───────┬───────────────┬───────┘
                         │               │
        ┌────────────────▼──┐   ┌────────▼─────────┐
        │ physics_simulator │   │   anomaly_engine │
        │  escenarios 1 Hz  │   │ mapeo · IF · MIRI │
        └───────────────────┘   └────────┬─────────┘
                                         │ DataFrame canónico
                                ┌────────▼─────────┐
                                │     iss_live     │
                                │  TLCP + buffer   │
                                └──────────────────┘
```

## Contrato de datos

Los tres caminos de entrada convergen en el mismo DataFrame de 9 columnas:

| Columna | Unidad | Rango admitido |
|---|---|---|
| `timestamp_sec` | s | 0 … n |
| `temp_c` | °C | −60 … 400 |
| `o2_pct` | % | 0 … 45 |
| `co_ppm` | ppm | 0 … 20 000 |
| `co2_ppm` | ppm | 0 … 200 000 |
| `hcn_ppm` | ppm | 0 … 2 000 |
| `airflow_cms` | cm/s | 0 … 200 |
| `smoke_obscuration_pct_m` | %/m | 0 … 200 |
| `radiative_heat_flux_kwm2` | kW/m² | 0 … 200 |

`anomaly_engine.detectar_anomalias` añade tres columnas derivadas: `anomaly_score`,
`ia_alerta` y `miri_score`.

## Flujo de una visita

1. La barra lateral elige modo: simulador, LIVE o CSV.
2. `physics_simulator.simular_escenario` o `anomaly_engine.mapear_dataset` producen el
   DataFrame canónico; en LIVE lo produce `iss_live.LiveISS.frame()`.
3. `detectar_anomalias` entrena el baseline, puntúa y añade las columnas de IA.
4. `calcular_ventaja_deteccion` compara la primera alerta IA con la del detector
   tradicional. `generar_protocolo_respuesta` clasifica el evento y redacta el protocolo.
5. `app.py` dibuja KPIs, cuatro pestañas y el panel de inferencia si está activo.

## Decisiones de diseño

- **Un solo contrato de datos.** Simulador, CSV y LIVE comparten columnas para que el
  motor no tenga ramas por origen; lo que cambia es qué canales existen y quién lo dice.
- **El motor nunca rellena huecos en silencio.** Los canales ausentes se declaran en el
  informe de mapeo (CSV) o se estiman en un panel aparte y etiquetado (LIVE).
- **Estado de UI en `st.session_state`.** El cursor temporal, el playback y la sesión
  del feed se recuerdan entre reruns y se recortan al dataset vigente.
- **Feed compartido.** `iss_live.LiveISS` se crea con `st.cache_resource`: una sola
  sesión TLCP por servidor, con `start()` idempotente para no duplicar streams.
- **Histéresis de alerta.** El IsolationForest puede disparar en un solo punto; la
  alerta operativa exige 3 muestras consecutivas o MIRI > 35.

## Concurrencia y red

El cliente TLCP corre en un hilo daemon por sesión y escribe en un `deque` protegido
por lock; `frame()` construye el DataFrame a partir de una copia. La UI nunca bloquea
esperando al feed, y el cliente reintenta con backoff exponencial.
