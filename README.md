# PyroGuard Micro-G

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pyrogaurdmicrog.streamlit.app)
[![tests](https://github.com/gaelopr/pyroguard-micro-g/actions/workflows/tests.yml/badge.svg)](https://github.com/gaelopr/pyroguard-micro-g/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

### ▶️ [pyrogaurdmicrog.streamlit.app](https://pyrogaurdmicrog.streamlit.app)

**Detección temprana de incendio en microgravedad con telemetría química.**
Prototipo de análisis y alerta para un rack del US Lab de la ISS: demuestra por qué
los detectores convencionales (temperatura y humo) llegan tarde en 0 g, y cuánto
tiempo se gana mirando la firma química en su lugar.

![Dashboard](docs/img/dashboard.png)

## Qué hace

- **Simula** la física de una quema en microgravedad: inercia térmica, ausencia de
  convección natural, ventilación forzada y corte de ventilación.
- **Puntúa el riesgo** con un motor no supervisado (IsolationForest sobre tasas
  suavizadas) más un índice determinista, MIRI.
- **Compara** su alerta con un detector tradicional (temperatura > 45 °C o humo > 4 %/m)
  y cuantifica la ventaja en segundos.
- **Traduce** el diagnóstico a un protocolo de respuesta estilo flight rules.
- **Lee** telemetría real: el feed público de la ISS (Lightstreamer) y CSV externos
  con unidades crudas, validando rangos y negándose a analizar si falta lo mínimo.

## Arranque rápido

```bash
python -m pip install -r requirements.txt
streamlit run app.py --server.address 127.0.0.1
```

El bind a `127.0.0.1` es deliberado: por defecto Streamlit escucha en toda la red local.

Para servirlo fuera de tu equipo con un túnel temporal:

```bash
cloudflared tunnel --url http://127.0.0.1:8501
streamlit run app.py --server.address 127.0.0.1 \
  --server.enableCORS false --server.enableXsrfProtection false
```

Los dos overrides de CORS/XSRF solo hacen falta detrás de un proxy TLS: sin ellos la
app se queda en "Please wait". No están en el `config.toml` a propósito, para no
romper el despliegue en la nube.

## Despliegue en Streamlit Community Cloud

1. Entra en [share.streamlit.io](https://share.streamlit.io) con tu cuenta de GitHub.
2. **New app** → repositorio `pyroguard-micro-g`, rama `master`, main file `app.py`.
3. Opcional: en *Advanced settings* elige Python 3.12 y pega tu clave de NASA si algún
día añades canales privados (hoy no hace falta ninguna).
4. **Deploy**. La primera construcción tarda unos minutos.

Atajo con el formulario ya relleno:
<https://share.streamlit.io/deploy?repository=gaelopr/pyroguard-micro-g&branch=master&mainModule=app.py>

Si el build falla en una dependencia, relaja el pin correspondiente en
`requirements.txt` (`pandas==3.1.1` → `pandas>=3.0`): las versiones están fijadas a las
que se probaron, no a las únicas compatibles.

## Qué es dato y qué no

| Panel | Origen | Etiqueta en la app |
|---|---|---|
| Escenarios del simulador | `physics_simulator` (modelo físico) | simulación |
| Live ISS | feed público NASA JSC vía Lightstreamer | medido |
| Canales ausentes en Live | `physics_simulator` | inferido (trazo discontinuo) |
| CSV subido | tu fichero, normalizado | informe de mapeo |

El feed público solo publica temperatura y presión de cabina del US Lab. No hay CO,
CO2, HCN, humo ni radiación en abierto: la app **no puntúa MIRI sobre datos reales**
y lo dice en pantalla en lugar de rellenar los huecos.

## Cifras de referencia (reproducibles)

| Escenario | MIRI | Temp | CO | Nota |
|---|---|---|---|---|
| Operación nominal | 19,9 % | 23,0 °C | 2,8 ppm | NOMINAL |
| Pirólisis de cableado | 59,1 % | 26,7 °C | 88 ppm | HCN 12,4 ppm · detector tradicional ciego |
| Propagación por ventilación | 98,0 % | 30,8 °C | 192 ppm | IA 180 s vs tradicional 503 s → **+323 s** |
| Llama fría | 50,1 % | 23,4 °C | 60 ppm | PRE-IGNICIÓN, humo 0,21 %/m |
| Artemis + corte a 220 s | — | 25,3 °C | 33 ppm | CO 192 → 33 ppm, radiación 4,51 → 3,60 kW/m² |

## Tests

```bash
python -m unittest discover -s tests -v
```

Se ejecuta también en cada push con GitHub Actions. 23 comprobaciones en unos 4 s, sin dependencias nuevas: magnitudes de los cuatro
escenarios, la ventaja de +323 s, el corte de ventilación, las conversiones del mapeador,
el rechazo de datasets incompletos y las cifras exactas que se dicen en la demo. Si un
cambio mueve un número del guion, la suite falla.

## Estructura

```
app.py                 UI Streamlit (Mission Control dark), 4 pestañas y modo LIVE
physics_simulator.py   Modelo físico: escenarios, atmósferas, corte de ventilación
anomaly_engine.py      Mapeo de CSV con unidades, IsolationForest, MIRI, protocolo
iss_live.py            Cliente TLCP propio + buffer de muestras reales
demo_saffire_sintetico.csv   Dataset de demostración (sintético, unidades crudas)
tests/test_pyroguard.py     Regresión de las cifras del guion y de los escenarios
GUION_DEMO.md          Guion de presentación de 5 minutos
docs/                  Documentación técnica
```

## Documentación

- [Arquitectura y flujo de datos](docs/ARQUITECTURA.md)
- [Modelo físico](docs/MODELO_FISICO.md)
- [Motor de detección: IsolationForest y MIRI](docs/MOTOR_IA.md)
- [Mapeo y validación de CSV](docs/MAPEO_DATOS.md)
- [Modo LIVE: qué publica la NASA de verdad](docs/LIVE_ISS.md)

## Límites conocidos

- MIRI es un índice compuesto ponderado, determinista y auditable, **no** un modelo
  validado en vuelo.
- La telemetría de los escenarios es simulación física, no datos de misión.
- Sin canales de CO/HCN/humo en el feed público, el motor no puede puntuar datos reales.
- El modo LIVE depende de un servicio de terceros; si NASA no publica valores, la app
  lo declara y no inventa cifras.

## Créditos

Datos de referencia: campañas **Saffire I–VI** y **BASS** de la NASA. El feed LIVE usa
el servicio público `ISSLIVE` de NASA JSC vía Lightstreamer. Este proyecto no está
afiliado a la NASA.

## Licencia

MIT — ver [LICENSE](LICENSE).
