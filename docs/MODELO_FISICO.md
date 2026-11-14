# Modelo físico

`physics_simulator.py` genera 600 s de telemetría a 1 Hz para un EXPRESS Rack
presurizado. No es un CFD: es un modelo fenomenológico calibrado a mano con las
tendencias publicadas de Saffire I–VI y BASS. La semilla es fija (`seed=7`), así que
las cifras son reproducibles bit a bit.

## Ecuaciones

Arranque exponencial (una quema no empieza instantáneamente):

```
_on(t, t0, τ) = 1 − exp(−(t − t0)/τ)     para t ≥ t0
```

Potencial de combustión por escenario, escalado por la atmósfera:

```
pot_raw(esc, t)          ·  f_atm          →  pot_eff
acc(t) = clip(Σ pot_eff / max Σ pot_raw·f_atm, 0, 1.6)
```

Inercia térmica del sensor (convolución exponencial, τ = 165 s):

```
temp(t) = 22.5 + lag(temp_gain · pot_eff, 165 s) + 0.22·sin(2πt/180)
```

**Ese retardo es el punto físico central**: sin convección natural el calor no sube
hacia el sensor, se acumula en el rack. De ahí que la temperatura vaya siempre por
detrás de la química.

Gases y radiación escalan con `acc` (y la radiación con `pot_eff`):

```
o2  = o2_atm − o2_drop·acc
co  = 1.4 + co_amp·acc
co2 = 4000 + co2_amp·acc
hcn = hcn_amp·acc
smoke = 0.05 + smoke_amp·acc
rad   = 0.02 + rad_amp·pot_eff
```

## Escenarios (ganancias)

| Esc | Nombre | temp_gain | CO | CO2 | HCN | humo | rad | ΔO2 |
|---|---|---|---|---|---|---|---|---|
| 1 | Operación nominal | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | Pirólisis de cableado Kapton | 9,0 | 86 | 950 | 12 | 1,15 | 0,55 | 0,9 |
| 3 | Propagación por ventilación | 9,5 | 190 | 5 650 | 25 | 5,40 | 4,50 | 2,6 |
| 4 | Llama fría | 2,0 | 58 | 2 200 | 2,2 | 0,11 | 0,24 | 1,7 |

Cada canal lleva ruido gaussiano proporcional a su nivel (0,11 °C en temperatura,
0,45 ppm + 1,2 % en CO, etc.), de modo que el detector tenga que suavizar de verdad.

## Atmósferas

| Atmósfera | O2 | Presión | Factor |
|---|---|---|---|
| ISS Standard | 20,9 % | 101,3 kPa | 1,0 |
| Lunar Gateway / Artemis | 34,0 % | 56,5 kPa | 1,65 |

El factor 1,65 multiplica el potencial: con más O2 y menos presión parcial de
nitrógeno, la inflamabilidad y la propagación crecen. No es un valor medido en vuelo,
es un parámetro de sensibilidad del modelo.

## Corte de ventilación

Con `corte = t_c` (1 … 599 s):

```
airflow(t ≥ t_c) = airflow(t_c) · exp(−(t − t_c)/14)
pot_eff(t ≥ t_c) = pot_eff(t_c) · exp(−(t − t_c)/75)
```

La ventilación muere en decenas de segundos; la combustión se apaga mucho más despacio
porque pasa a estar limitada por difusión. Resultado en el escenario 3 con corte a
220 s: CO 192 → 33 ppm, radiación 4,51 → 3,60 kW/m², temperatura 25,3 °C.
**En 0 g, cerrar el aire es la maniobra de supresión más eficaz.**

## Qué NO modela

- No hay dinámica de fluidos: la ventilación es un escalar, no un campo.
- No hay llama visible ni dinámica de gotas/char.
- No hay acoplamiento térmico entre rack y cabina.
- La humedad, la presión parcial de CO2 y la estratificación no intervienen.
