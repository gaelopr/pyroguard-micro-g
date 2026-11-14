# Decisiones de diseño

Documento corto para el pitch: qué se consideró, qué se eligió y por qué la app se ve
como se ve.

## Tres direcciones antes de elegir

| Idea | Por qué se descartó |
|---|---|
| **Visión por cámara**: detectar humo con una cámara del rack | No hay dataset público de vídeo de quema en 0 g, y el humo es justo la señal tardía: resuelve el problema demasiado tarde |
| **Gemelo digital CFD**: simular el campo de flujo del rack | Coste computacional incompatible con una demo en vivo, y el resultado no es verificable por un jurado en 5 minutos |
| **Índice químico + baseline estadístico** (elegido) | Usa lo que la NASA sí publica y lo que cambia primero (CO, CO2, HCN, radiación), es explicable y se puede contrastar con un detector clásico |

## Una app, un trabajo

La app responde a **una** pregunta: *¿hay riesgo ahora y qué hago?* Todo lo demás
(exportar, tabla completa, inferencia) está detrás de un desplegable o de un modo
opcional, para que la primera pantalla no pida decisiones.

- **Tres pestañas** en el orden en que se decide: `ESTADO` → `DETECCIÓN` → `RESPUESTA`.
- **Un veredicto** en la cabecera: MIRI, nivel y ventaja temporal, con el resumen químico
  en una línea.
- **Dos gráficas** en `ESTADO` (temperatura/ventilación y firma química) más tres cifras
  (radiación, humo, O2). Se eliminaron dos subgráficas que solo añadían ruido visual.
- **Cuatro indicadores** en la tira del cursor: temperatura, CO, MIRI y estado de la IA.

## Checklist de UX (aplicada)

| Principio | Cómo se cumple |
|---|---|
| La siguiente acción es obvia | Veredicto arriba, pestañas en orden de decisión, acción nº 1 destacada |
| Etiquetas consistentes | Mismos nombres de canal en todas las vistas y en la tabla |
| Feedback tras cada acción | Cambiar escenario o cursor actualiza chips, gráficas y veredicto a la vez |
| Lenguaje accesible | "Riesgo", "nivel", "ventaja", no jerga interna; la jerga queda en los detalles |
| Diseñado para el error | Un CSV sin temperatura **no** produce un diagnóstico: se rechaza con informe |

## Móvil

El jurado puede abrir el enlace en un teléfono, así que la versión pequeña muestra lo
esencial: veredicto, dos gráficas y cuatro indicadores. La barra lateral se colapsa sola
y las figuras bajaron de 700 a 470 px de alto.

## Qué probaríamos con usuarios (pendiente)

Cinco tareas con tres personas ajenas al proyecto, midiendo tiempo y errores:

1. "Dime si hay riesgo ahora mismo." (objetivo: < 10 s)
2. "¿Qué harías primero?" (objetivo: citar el corte de ventilación)
3. "¿Cuánto antes se enteró el modelo que el detector clásico?" (objetivo: leer +323 s)
4. "Sube este CSV y dime si es analizable." (objetivo: leer el informe de mapeo)
5. "¿Qué canal falta y qué implica?" (objetivo: entender la cobertura de LIVE)

Métrica de éxito: 3 de 3 usuarios completan 1 y 2 sin ayuda.
