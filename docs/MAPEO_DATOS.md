# Mapeo y validación de CSV

El mapeador acepta telemetría externa con nombres y unidades arbitrarios y la lleva al
contrato canónico de 9 columnas. Si no puede garantizar los canales mínimos, **se niega
a analizar**.

## Orden de resolución

Cada canal canónico se busca en este orden, consumiendo cada columna del fichero una
sola vez (una columna no puede alimentar dos canales):

1. `temp_c` → `temp*`, `tc`, `temperature`, `thermocouple*`
2. `co2_ppm` → `co2`, `carbon dioxide`
3. `co_ppm` → `co`, `carbon monoxide`
4. `o2_pct` → `o2`, `oxygen`, `po2`
5. `hcn_ppm` → `hcn`, `cyanide`, `hydrogen cyanide`
6. `airflow_cms` → `flow`, `airflow`, `air flow`, `velocity`, `ventilation`
7. `smoke_obscuration_pct_m` → `smoke`, `obscuration`, `opacity`, `optical`
8. `radiative_heat_flux_kwm2` → `rad*`, `heat flux`

La coincidencia es **por tokens con límites de palabra**, no por substring. Ese detalle
importa: con substring, `co2` capturaba la columna de O2 y una quema real se clasificaba
como "estado nominal".

La columna de tiempo se busca aparte (`time`, `timestamp`, `sec`, `elapsed`, `met`) y
sus valores se usan como eje X real, restándoles el mínimo.

## Unidades

| Canal | Detección | Conversión |
|---|---|---|
| temperatura | `K`/`kelvin` o mediana > 150 | −273,15 |
| temperatura | `F`/`fahrenheit` | ×5/9 −17,78 |
| O2 / CO2 / CO / HCN | `fraction`/`mol` | ×100 (O2) · ×10⁶ (ppm) |
| O2 / CO2 / CO / HCN | `%`/`percent` | ×1 · ×10⁴ |
| caudal | `m/s` | ×100 → cm/s |
| caudal | `mm/s` | ×0,1 → cm/s |
| radiación | `W/m²` | ×0,001 → kW/m² |

Cuando el encabezado no declara unidad, no se adivina por umbral fijo: se prueban los
factores candidatos y se elige el que deja la mediana dentro de la banda físicamente
plausible del canal (O2 5–45 %, CO2 100–50 000 ppm, CO 0,05–2 000 ppm,
HCN 0,01–200 ppm). Con eso, una columna `O2` con valores 0,209 se interpreta como
fracción y no como 0,2 %.

## Validación

Tras convertir, la mediana debe caer en el rango admitido del canal (ver
[ARQUITECTURA](ARQUITECTURA.md#contrato-de-datos)). Si no, el canal se marca
**rechazado** y se declara el motivo; nunca se usa en silencio.

## Informe

`mapear_dataset(df)` devuelve `(DataFrame, informe)`. El informe contiene:

| Campo | Contenido |
|---|---|
| `ok` | `True` solo si hay `temp_c` y al menos `o2_pct` o `co2_ppm` |
| `channels` | por canal: `canal`, `origen`, `unidad`, `factor`, `estado`, `nota` |
| `mapped` / `missing` | canales resueltos y ausentes |
| `rows` | filas leídas |

`estado` toma tres valores: **mapeado**, **rechazado** (fuera de rango) y **default**
(sin columna: se usa el valor nominal, declarado en la propia tabla).

La app muestra el informe en un desplegable y, si `ok` es `False`, detiene el análisis
con un mensaje explícito en lugar de producir un diagnóstico.

## Ejemplo

```csv
Time (s),TC1 (K),Rad1 (kW/m2),CO2 mole fraction,O2 mole fraction,Flow (cm/s),CO (ppm),HCN (ppm)
0,296.5,0.02,0.0041,0.209,20,0.4,0.0
120,318.7,1.80,0.0072,0.203,20,45.0,3.4
```

Resultado: `temp_c` 23,35 → 45,55 °C · `o2_pct` 20,9 → 20,3 % · `co2_ppm` 4 100 → 7 200 ·
`radiative_heat_flux_kwm2` 0,02 → 1,80 · `airflow_cms` 20 (sin conversión) ·
7 de 8 canales mapeados, `smoke` declarado como nominal.

## Límites

- Máximo 25 MB y 200 000 filas por fichero (se recorta y se avisa).
- Mínimo 12 filas para poder estimar un baseline.
- Sin columna de tiempo se usa el índice de fila como segundos.
- No se interpretan columnas categóricas ni texto: un valor no numérico se descarta.
