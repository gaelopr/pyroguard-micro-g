import numpy as np
import pandas as pd

N = 600
DT = 1.0
T = np.arange(N, dtype=float)

ATM = {
    "ISS Standard (20.9% O2 | 14.7 psi)": {"o2": 20.9, "kpa": 101.3, "factor": 1.0},
    "Lunar Gateway / Artemis (34.0% O2 | 8.2 psi)": {"o2": 34.0, "kpa": 56.5, "factor": 1.65},
}

ESCENARIOS = [
    "Nominal Operations (Operación Nominal)",
    "Smoldering Avionics (Pirólisis Latente de Cableado Kapton)",
    "Ventilation-Driven Flame Spread (Propagación Estilo NASA Saffire)",
    "Cool Flame / Low-Temperature Oxidation (Llama Fría Invisible)",
]

COLS = [
    "timestamp_sec", "temp_c", "o2_pct", "co_ppm", "co2_ppm", "hcn_ppm",
    "airflow_cms", "smoke_obscuration_pct_m", "radiative_heat_flux_kwm2",
]


def _on(t, t0, tau):
    return np.where(t >= t0, 1.0 - np.exp(-np.clip(t - t0, 0, None) / tau), 0.0)


def _lag(x, tau):
    k = np.exp(-DT / tau)
    return np.convolve(x, (1.0 - k) * k ** np.arange(len(x)))[: len(x)]


def _airflow_base(esc, t):
    if esc == 3:
        return 8.0 + 12.0 * _on(t, 150, 45) + 0.9 * np.sin(2 * np.pi * t / 70)
    if esc == 2:
        return 12.0 + 1.8 * np.sin(2 * np.pi * t / 95) + 0.7 * np.sin(2 * np.pi * t / 37)
    if esc == 4:
        return 11.0 + 1.6 * np.sin(2 * np.pi * t / 110) + 0.5 * np.sin(2 * np.pi * t / 29)
    return 12.0 + 1.5 * np.sin(2 * np.pi * t / 95) + 0.6 * np.sin(2 * np.pi * t / 37)


def _potencial(esc, t):
    if esc == 2:
        return _on(t, 120, 170) * 0.55
    if esc == 3:
        return _on(t, 150, 105) * 1.00
    if esc == 4:
        return _on(t, 100, 260) * 0.34
    return np.zeros_like(t)


GAINS = {
    # esc: (temp_gain, co_amp, co2_amp, hcn_amp, smoke_amp, rad_amp, o2_drop)
    1: (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    2: (9.0, 86.0, 950.0, 12.0, 1.15, 0.55, 0.9),
    3: (9.5, 190.0, 5650.0, 25.0, 5.4, 4.5, 2.6),
    4: (2.0, 58.0, 2200.0, 2.2, 0.11, 0.24, 1.7),
}


def simular_escenario(escenario=0, atmosfera=list(ATM)[0], corte_ventilacion_seg=0, seed=7):
    """Genera 600 s de telemetría sintética (1 Hz) de un EXPRESS Rack presurizado."""
    rng = np.random.default_rng(seed)
    esc = int(escenario) + 1
    atmo = ATM.get(atmosfera, ATM[list(ATM)[0]])
    f_atm = atmo["factor"]
    t = T.copy()

    pot_raw = _potencial(esc, t)
    # Normalización SIEMPRE contra la atmósfera de referencia: si se normaliza con el
    # factor de la atmósfera activa, ese factor se cancela y AEA no cambiaría los gases.
    ref = np.cumsum(pot_raw).max() or 1.0

    corte = int(corte_ventilacion_seg)
    pot_eff = pot_raw.copy()
    airflow = _airflow_base(esc, t)
    if 1 <= corte <= N - 1:
        pot_eff = np.where(t < corte, pot_raw, pot_raw[corte] * np.exp(-(t - corte) / 75.0))
        airflow = np.where(t < corte, airflow, airflow[corte] * np.exp(-(t - corte) / 14.0))

    pot_eff = pot_eff * f_atm
    acc = np.clip(np.cumsum(pot_eff) / ref, 0, 1.7)

    tg, co_a, co2_a, hcn_a, smoke_a, rad_a, o2_d = GAINS[esc]
    # El sensor de rack sufre inercia térmica: sin convección natural el calor no llega al techo/pared.
    temp = 22.5 + _lag(tg * pot_eff, 165.0) + 0.22 * np.sin(2 * np.pi * t / 180)
    o2 = atmo["o2"] - o2_d * acc
    co = 1.4 + co_a * acc
    co2 = 4000.0 + co2_a * acc
    hcn = hcn_a * acc
    smoke = 0.05 + smoke_a * acc
    rad = 0.02 + rad_a * pot_eff

    df = pd.DataFrame({
        "timestamp_sec": T.astype(int),
        "temp_c": temp + rng.normal(0, 0.11, N),
        "o2_pct": o2 + rng.normal(0, 0.035, N),
        "co_ppm": np.clip(co + rng.normal(0, 0.45 + 0.012 * co), 0, None),
        "co2_ppm": co2 + rng.normal(0, 12 + 0.006 * co2),
        "hcn_ppm": np.clip(hcn + rng.normal(0, 0.11 + 0.01 * hcn), 0, None),
        "airflow_cms": np.clip(airflow + rng.normal(0, 0.35, N), 0, None),
        "smoke_obscuration_pct_m": np.clip(smoke + rng.normal(0, 0.02 + 0.005 * smoke), 0, None),
        "radiative_heat_flux_kwm2": np.clip(rad + rng.normal(0, 0.008 + 0.004 * rad), 0, None),
    })
    return df[COLS]
