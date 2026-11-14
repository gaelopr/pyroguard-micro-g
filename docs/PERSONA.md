# Persona y caso de uso

> Artefacto de diseño, no un hallazgo de investigación: es una hipótesis construida
> sobre cómo se opera la seguridad de carga en la ISS. Está escrita para poder ser
> rebatida — y validada con una entrevista real — antes de defenderla en el pitch.

## Marta Ibáñez · controladora de seguridad de carga (Payload Safety)

**Dónde trabaja.** Consola de seguridad de carga del ISS Flight Control Room. Turno de
8 horas cubriendo una campaña de experimentos de combustión en un EXPRESS Rack.

**Qué intenta conseguir en su turno.** Decidir, en segundos, si una variación de CO en
la telemetría de un rack es ruido del sensor o el comienzo de una quema, y si debe
cortar la alimentación y la ventilación de ese rack antes de que el experimento avance.

**Qué le frena hoy.**

- Cuarenta canales en crudo, cada uno en su unidad: kelvin, fracción molar, %/m, kW/m².
- Las alarmas que tiene dependen de temperatura y humo, y en microgravedad esas dos
  señales llegan **después** que la química.
- Cuando por fin suena algo, ya tiene que reconstruir a mano qué canal se movió primero.
- Si se equivoca por exceso, cancela un experimento de millones; si se equivoca por
  defecto, no hay segunda oportunidad.

**Qué significaría tener éxito.** Una sola cifra de riesgo, explicable en una frase, con
la acción siguiente ya escrita, y disponible en los primeros segundos — no minutos.

### Su pregunta (How Might We)

> ¿Cómo podríamos dar a la controladora **una única señal de riesgo, explicable y
> temprana**, en los primeros segundos de una quema en microgravedad, sin pedirle que
> interprete ocho canales en cuatro unidades distintas?

## Cómo usa la app (4 pasos)

1. **Abre el estado** → ve un veredicto: MIRI, nivel y ventaja frente al detector clásico.
2. **Comprueba la evidencia** en `ESTADO`: temperatura contra ventilación y firma química.
3. **Mira cuándo** en `DETECCIÓN`: la línea verde (modelo) frente a la roja (clásico).
4. **Actúa** con `RESPUESTA`: cinco acciones en orden, la primera es cortar la ventilación.

Tiempo objetivo: **menos de 10 segundos** entre abrir la app y saber qué hacer.

## Lo que se dejó fuera a propósito

- Varios racks a la vez: la persona vigila uno durante un experimento concreto.
- Histórico de misiones y comparación entre campañas: no cambia la decisión de ese turno.
- Cuentas de usuario y permisos: no aportan a la decisión y añaden fricción en la demo.
- Notificaciones push: el contexto es una consola, no un móvil en el bolsillo.
