# Validación del detector

**Qué demuestra este documento:** que el motor de PyroGuard Micro-G no solo puntúa bonito
en una captura de pantalla. Se ejecuta un protocolo repetible, con ruido de sensor distinto
en cada repetición, y se publican detecciones, falsos positivos y ventaja frente a un
detector de umbrales fijos.

Reproducirlo:

```bash
python validation.py            # 30 repeticiones por caso
python validation.py --reps 10  # tanda corta
```

## Protocolo

| Elemento | Definición |
|---|---|
| Clase positiva | Escenarios de incendio del simulador: pirólisis de Kapton, propagación por ventilación (Saffire) y llama fría |
| Clase negativa | Operación nominal y **corte de ventilación sin fuego** (transitorio real de cabina que no es un incendio) |
| Repeticiones | 30 por caso, con semilla distinta en el generador de ruido del sensor (`seed=0..29`) |
| Alarma IA | `miri_score > 35 %` o 3 muestras consecutivas marcadas por IsolationForest |
| Detector clásico | Umbrales fijos: 45 °C de temperatura o 4 %/m de opacidad de humo |
| Atmósferas | ISS (20,9 % O₂) y Artemis/AEA (34,0 % O₂) por separado |

## Resultados (30 repeticiones por caso)

| Clase | Escenario | Atmósfera | Reps | Detecta IA | t detección (s) | Detecta clásico | Ventaja (s) | MIRI pico |
|---|---|---|---|---|---|---|---|---|
| incendio | Pirólisis de cableado (Kapton) | ISS | 30 | 30/30 | 172 ± 18 | 0/30 | — | 59 % |
| incendio | Pirólisis de cableado (Kapton) | AEA | 30 | 30/30 | 162 ± 7 | 0/30 | — | 80 % |
| incendio | Propagación por ventilación (Saffire) | ISS | 30 | 30/30 | 178 ± 7 | 30/30 | +325 ± 7 | 98 % |
| incendio | Propagación por ventilación (Saffire) | AEA | 30 | 30/30 | 172 ± 5 | 30/30 | +226 ± 6 | 98 % |
| incendio | Llama fría oxidativa | ISS | 30 | 30/30 | 186 ± 16 | 0/30 | — | 50 % |
| incendio | Llama fría oxidativa | AEA | 30 | 30/30 | 168 ± 10 | 0/30 | — | 62 % |
| negativo | Operación nominal | ISS | 30 | 0/30 | — | 0/30 | — | 19 % |
| negativo | Operación nominal | AEA | 30 | 0/30 | — | 0/30 | — | 19 % |
| negativo | Corte de ventilación sin fuego | ISS | 30 | 0/30 | — | 0/30 | — | 18 % |

AUC (MIRI pico, incendio vs negativo): **1.000**.

## Cómo leerlo (y qué no dice)

- **Detección 180/180** en los seis casos de incendio y **0 alarmas en 90 corridas sin
  fuego**, incluido el corte de ventilación: el motor no confunde un transitorio de
  cabina con un incendio.
- **El detector clásico es ciego en 4 de los 6 casos**: la pirólisis y la llama fría no
  llegan a 45 °C ni a 4 %/m. Cuando sí detecta (propagación), llega **325 ± 7 s** tarde.
- **La atmósfera Artemis cambia el resultado, no solo la etiqueta**: detección 10 s antes
  y MIRI pico 59 % → 80 % en pirólisis. La ventaja frente al clásico baja a 226 s porque
  en AEA el incendio también se hace visible antes para los umbrales fijos.
- **AUC = 1.000 en este banco no es un resultado de campo.** Los positivos son los
  regímenes que el propio simulador modela; la separación es limpia por construcción.
  Lo que esta tabla mide es la **robustez al ruido y la ausencia de falsos positivos**,
  no el rendimiento sobre vuelo real. Para eso el proyecto usa PSI: la tabla de Saffire-II
  es la referencia experimental, y su lectura (silicona que se apaga sola frente a tela
  SIBAL que se consume con el mismo ~22 % de O₂) es la que sostiene el modelo físico.
