"""Protocolo de validación del detector, reproducible y sin datos etiquetados externos.

Qué mide, sobre el simulador físico con ruido de sensor distinto en cada repetición:

  * **Detección**: en cuántas de las N repeticiones de cada escenario de incendio
    salta la alarma (MIRI > 35 % o 3 muestras seguidas de IsolationForest).
  * **Falsos positivos**: alarmas en el escenario nominal y en un transitorio
    operacional real (corte de ventilación sin fuego), que no son incendio.
  * **Ventaja**: segundos de adelanto sobre el detector de umbrales fijos
    (45 °C o 4 %/m de opacidad), el mismo que usa la app como referencia.

Uso:
    python validation.py            # 30 repeticiones por caso, tabla + AUC
    python validation.py --reps 10  # tanda corta

Los positivos son sintéticos: el resultado dice cuánto aguanta el motor ante el ruido
y los regímenes que modela, **no** es una validación sobre vuelo real.
"""
from __future__ import annotations

import argparse
import statistics as stats

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

import anomaly_engine as ae
import physics_simulator as ps

ISS = list(ps.ATM)[0]
AEA = [a for a in ps.ATM if "Artemis" in a][0]
UMBRAL_MIRI = 35.0
N_REPS = 30

# Escenarios de incendio del simulador (clase positiva)
POSITIVOS = {
    1: "Pirólisis de cableado (Kapton)",
    2: "Propagación por ventilación (Saffire)",
    3: "Llama fría oxidativa",
}


def _primera_alarma_ia(d: pd.DataFrame) -> int | None:
    """Primer segundo con MIRI sobre umbral o con 3 muestras seguidas de anomalía."""
    persistente = pd.Series(d["ia_alerta"].to_numpy()).rolling(3).sum().fillna(0).to_numpy() >= 3
    idx = np.flatnonzero((d["miri_score"].to_numpy() > UMBRAL_MIRI) | persistente)
    return int(d["timestamp_sec"].iloc[idx[0]]) if idx.size else None


def _primera_alarma_tradicional(d: pd.DataFrame) -> int | None:
    """Detector de referencia: umbrales fijos de temperatura y opacidad de humo."""
    m = ((d["temp_c"] > 45.0) | (d["smoke_obscuration_pct_m"] > 4.0)).to_numpy()
    idx = np.flatnonzero(m)
    return int(d["timestamp_sec"].iloc[idx[0]]) if idx.size else None


def _corrida(escenario: int, atmosfera: str, corte: int, seed: int) -> dict:
    raw = ps.simular_escenario(escenario, atmosfera, corte, seed=seed)
    d = ae.detectar_anomalias(raw)
    return {"t_ia": _primera_alarma_ia(d), "t_trad": _primera_alarma_tradicional(d),
            "miri": float(d["miri_score"].max())}


def evaluar(reps: int = N_REPS) -> dict:
    """Corre el protocolo completo y devuelve filas de resultados + AUC."""
    casos = []
    for esc, nombre in POSITIVOS.items():
        for atm, etiqueta in ((ISS, "ISS"), (AEA, "AEA")):
            casos.append({"clase": "incendio", "escenario": nombre, "atm": etiqueta,
                          "esc": esc, "corte": 0, "positivo": 1})
    casos += [
        {"clase": "negativo", "escenario": "Operación nominal", "atm": "ISS",
         "esc": 0, "corte": 0, "positivo": 0},
        {"clase": "negativo", "escenario": "Operación nominal", "atm": "AEA",
         "esc": 0, "corte": 0, "positivo": 0},
        # Transitorio real de cabina que NO es un incendio: si esto dispara, hay falsos positivos.
        {"clase": "negativo", "escenario": "Corte de ventilación sin fuego", "atm": "ISS",
         "esc": 0, "corte": 300, "positivo": 0},
    ]

    filas, y_true, y_score = [], [], []
    for caso in casos:
        corridas = [_corrida(caso["esc"], ISS if caso["atm"] == "ISS" else AEA,
                             caso["corte"], seed) for seed in range(reps)]
        t_ia = [c["t_ia"] for c in corridas]
        t_trad = [c["t_trad"] for c in corridas]
        detectados = [t for t in t_ia if t is not None]
        ventajas = [tr - ta for ta, tr in zip(t_ia, t_trad) if ta is not None and tr is not None]
        filas.append({
            "Clase": caso["clase"],
            "Escenario": caso["escenario"],
            "Atmósfera": caso["atm"],
            "Reps": reps,
            "Detecta IA": f"{len(detectados)}/{reps}",
            "t detección (s)": (f"{stats.mean(detectados):.0f} ± {stats.pstdev(detectados):.0f}"
                                if detectados else "—"),
            "Detecta clásico": f"{sum(t is not None for t in t_trad)}/{reps}",
            "Ventaja (s)": (f"{stats.mean(ventajas):+.0f} ± {stats.pstdev(ventajas):.0f}"
                            if ventajas else "—"),
            "MIRI pico": f"{stats.mean([c['miri'] for c in corridas]):.0f} %",
        })
        y_true += [caso["positivo"]] * reps
        y_score += [c["miri"] for c in corridas]

    auc = float(roc_auc_score(y_true, y_score)) if len(set(y_true)) > 1 else float("nan")
    return {"filas": filas, "auc": auc, "reps": reps}


def tabla_markdown(res: dict) -> str:
    df = pd.DataFrame(res["filas"])
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    out += ["| " + " | ".join(str(v) for v in fila) + " |" for fila in df.itertuples(index=False)]
    out.append("")
    out.append(f"AUC (MIRI pico, incendio vs negativo): **{res['auc']:.3f}** · "
               f"{res['reps']} repeticiones por caso.")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Protocolo de validación del detector")
    ap.add_argument("--reps", type=int, default=N_REPS)
    args = ap.parse_args()
    print(tabla_markdown(evaluar(args.reps)))


if __name__ == "__main__":
    main()
