# Motor de detección

Dos puntuaciones complementarias sobre el mismo DataFrame: una **estadística**
(IsolationForest) y otra **determinista y explicable** (MIRI). La alerta operativa
combina ambas.

## Features (7)

| Feature | Cálculo | Por qué |
|---|---|---|
| `dCO` | tasa de CO suavizada (ventana adaptativa) | firma más temprana de combustión incompleta |
| `dO2` | tasa de O2 | consumo de oxidante |
| `dCO2` | tasa de CO2 | producción de combustión |
| `ratio` | CO/CO2 · 100 | distingue pirólisis (alto) de oxidación limpia |
| `airflow` | valor directo | la ventilación sostiene la reacción en 0 g |
| `rad` | valor directo | emisión IR: el calor que sí sale del material |
| `hcn` | valor directo | degradación de aislamientos nitrogenados |

La ventana de suavizado es `min(15, max(3, n//4))` muestras: en series cortas no se
aplanan las tasas, y en series de 1 Hz elimina el ruido del sensor.

## IsolationForest

- 220 árboles, `contamination=0.03`, `random_state=42`.
- Se entrena **solo con el baseline**: las muestras cuyo `timestamp_sec ≤ 60`
  (con un mínimo de 10 filas). No hay datos etiquetados de incendios reales en 0 g,
  así que el modelo aprende lo nominal, no lo peligroso.
- Score normalizado contra el propio baseline: 0 % = mediana nominal,
  100 % = percentil 99 del baseline. Así el número es comparable entre datasets.
- Umbral de alerta: `media + 4σ` del baseline, con suelo de dispersión
  `max(σ, 0.02·|media|, 1e-9)`. Sin ese suelo, un baseline perfectamente constante
  haría que cualquier desviación disparara todas las muestras.

## MIRI — Microgravity Ignition Risk Index

Índice compuesto, determinista y auditable (0–100):

```
MIRI = 100 · [ 0.35·clip(dCO/0.50)
             + 0.25·clip(−dO2/0.006)
             + 0.15·clip(HCN/12)
             + 0.15·clip(rad/4.5)
             + 0.10·clip(exp(−((airflow−15)/9)²), 0.05, 1) ]
```

Los denominadores son los valores de saturación de cada canal (0,50 ppm/s de CO,
0,006 %/s de pérdida de O2, 12 ppm de HCN, 4,5 kW/m²). El término de ventilación
penaliza el caudal nulo: sin flujo, los productos se acumulan en la zona de reacción.
Se suaviza con media móvil de 5 muestras.

Umbrales de presentación: **< 35 %** nominal · **35–65 %** pre-ignición · **> 65 %** crítico.

MIRI no es un modelo validado en vuelo: es un índice de priorización con pesos
elegidos a mano y documentados aquí para que cualquiera pueda discutirlos.

## Detector tradicional (referencia)

Se declara alerta cuando `temp_c > 45 °C` **o** `smoke_obscuration_pct_m > 4 %/m`.
Es una aproximación honesta al comportamiento de un detector de rack: los umbrales son
los típicos de alarma térmica y de obscuración, no una caricatura.

## Ventaja temporal

- Alerta IA = primer instante con `MIRI > 35` **o** 3 muestras consecutivas de
  `ia_alerta` (histéresis contra falsos positivos).
- Alerta tradicional = primer instante que cruza los umbrales anteriores.
- La ventaja se informa en **segundos reales** del dataset, no en índices de fila.

Resultados con los escenarios por defecto:

| Escenario | IA | Tradicional | Ventaja |
|---|---|---|---|
| Nominal | — | — | sin evento |
| Pirólisis de cableado | 170 s | nunca | **detector tradicional ciego** |
| Propagación por ventilación | 180 s | 503 s | **+323 s** |
| Llama fría | 182 s | nunca | **detector tradicional ciego** |

## Protocolo de respuesta

`generar_protocolo_respuesta` clasifica con reglas explícitas (nominal, llama fría,
propagación sostenida, pirólisis) y calcula el tiempo hasta el umbral IDLH
(CO 1 200 ppm / HCN 50 ppm) extrapolando la pendiente **por segundo** de los últimos
30 s. Devuelve cinco acciones ordenadas: aislamiento de ventilación, aislamiento
eléctrico, protección de tripulación, supresión con CO2 y monitoreo post-supresión.

## Límites

- El baseline son 60 s: si el dataset arranca ya en fuego, no hay referencia nominal y
  la comparación con el detector tradicional pierde sentido (la app lo muestra igual).
- Con menos de 12 muestras el baseline no es estimable y el análisis se rechaza.
- Los pesos de MIRI no están optimizados contra ningún conjunto de datos de vuelo.
