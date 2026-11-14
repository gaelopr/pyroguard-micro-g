import re

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

CANON = [
    "timestamp_sec", "temp_c", "o2_pct", "co_ppm", "co2_ppm", "hcn_ppm",
    "airflow_cms", "smoke_obscuration_pct_m", "radiative_heat_flux_kwm2",
]

DEFAULTS = {
    "temp_c": 22.5, "o2_pct": 20.9, "co_ppm": 0.0, "co2_ppm": 4000.0, "hcn_ppm": 0.0,
    "airflow_cms": 12.0, "smoke_obscuration_pct_m": 0.0, "radiative_heat_flux_kwm2": 0.0,
}

# Coincidencia por token: \bco2\b no puede capturar la columna de O2 (el bug del substring).
PATTERNS = {
    "temp_c": r"\b(temp\w*|tc\d*|temperature|thermocouple\w*)\b",
    "co2_ppm": r"\bco2\b|\bcarbon dioxide\b",
    "co_ppm": r"\bco\b|\bcarbon monoxide\b",
    "o2_pct": r"\bo2\b|\boxygen\b|\bpo2\b",
    "hcn_ppm": r"\bhcn\b|\bcyanide\b|\bhydrogen cyanide\b",
    "airflow_cms": r"\bflow\b|\bairflow\b|\bair flow\b|\bvelocity\b|\bventilation\b",
    "smoke_obscuration_pct_m": r"\bsmoke\b|\bobscuration\b|\bopacity\b|\boptical\b",
    "radiative_heat_flux_kwm2": r"\brad\w*\b|\bheat flux\b",
}
ORDER = ["temp_c", "co2_ppm", "co_ppm", "o2_pct", "hcn_ppm", "airflow_cms",
         "smoke_obscuration_pct_m", "radiative_heat_flux_kwm2"]
KIND = {"temp_c": "temp", "o2_pct": "pct", "hcn_ppm": "ppm", "co_ppm": "ppm",
        "co2_ppm": "ppm", "airflow_cms": "cms", "smoke_obscuration_pct_m": "raw",
        "radiative_heat_flux_kwm2": "kwm2"}
RANGES = {"temp_c": (-60, 400), "o2_pct": (0, 45), "co_ppm": (0, 20000),
          "co2_ppm": (0, 200000), "hcn_ppm": (0, 2000), "airflow_cms": (0, 200),
          "smoke_obscuration_pct_m": (0, 200), "radiative_heat_flux_kwm2": (0, 200)}
UNIT_RE = re.compile(r"[\(\[]\s*([^\)\]]+)\s*[\)\]]")


def _split_header(header):
    raw = str(header)
    units = " ".join(UNIT_RE.findall(raw))
    name = UNIT_RE.sub(" ", raw)
    clean = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    return clean(name), clean(units)


# Banda físicamente plausible por canal: desempata fracción / % / ppm cuando el encabezado no lo dice.
PLAUSIBLE = {"o2_pct": (5.0, 45.0), "co2_ppm": (100.0, 50000.0),
             "co_ppm": (0.05, 2000.0), "hcn_ppm": (0.01, 200.0)}


def _convert(values, kind, units, notes, target):
    v = pd.to_numeric(values, errors="coerce").astype(float)
    med = float(np.nanmedian(v)) if np.isfinite(v).any() else 0.0
    factor, offset = 1.0, 0.0
    lo, hi = PLAUSIBLE.get(target, (-np.inf, np.inf))
    if kind == "temp":
        if re.search(r"\bk\b|kelvin", units) or med > 150:
            offset = -273.15
            notes.append("K -> °C")
        elif re.search(r"\bf\b|fahrenheit", units):
            factor, offset = 5 / 9, -17.78
            notes.append("°F -> °C")
    elif kind in ("pct", "ppm"):
        if "fraction" in units or "mol" in units:
            candidates = [(100.0 if kind == "pct" else 1e6,
                           "fracción -> %" if kind == "pct" else "fracción -> ppm")]
        elif "%" in units or "percent" in units:
            candidates = [(1.0 if kind == "pct" else 1e4,
                           "%" if kind == "pct" else "% -> ppm")]
        else:
            candidates = ([(100.0, "fracción -> %"), (1.0, "%")] if kind == "pct"
                          else [(1e6, "fracción -> ppm"), (1e4, "% -> ppm"), (1.0, "ppm")])
        for cand, note in candidates:
            if lo <= med * cand <= hi:
                factor = cand
                notes.append(note)
                break
    elif kind == "cms":
        if re.search(r"\bmm\b|mm s|mm/s", units):
            factor = 0.1
            notes.append("mm/s -> cm/s")
        elif re.search(r"(?<![a-z])m\s*/?\s*s\b", units):
            factor = 100.0
            notes.append("m/s -> cm/s")
    elif kind == "kwm2":
        if re.search(r"\bw\b|w m2|w/m2", units) and "kw" not in units:
            factor = 0.001
            notes.append("W/m² -> kW/m²")
    return v * factor + offset, factor, offset


def mapear_dataset(df):
    """Mapea un CSV externo con unidades y rangos validados.

    Devuelve (DataFrame canónico, informe). El informe declara por canal el origen, el factor
    aplicado y el estado; `ok` es False si faltan los canales mínimos para analizar.
    """
    used, channels, missing = set(), [], []
    out = pd.DataFrame(index=df.index)

    for target in ORDER:
        src, units, notes = None, "", []
        for col in df.columns:
            if col in used:
                continue
            name, u = _split_header(col)
            if re.search(PATTERNS[target], name):
                src, units = col, u
                break
        if src is None:
            missing.append(target)
            out[target] = DEFAULTS[target]
            channels.append({"canal": target, "origen": "—", "unidad": "", "factor": "",
                             "estado": "default", "nota": "sin columna: se usa el nominal"})
            continue

        used.add(src)
        vals, factor, offset = _convert(df[src], KIND[target], units, notes, target)
        lo, hi = RANGES[target]
        med = float(np.nanmedian(vals)) if np.isfinite(vals).any() else np.nan
        if not np.isfinite(med) or not (lo <= med <= hi):
            missing.append(target)
            out[target] = DEFAULTS[target]
            channels.append({"canal": target, "origen": str(src), "unidad": units,
                             "factor": f"{factor:g}", "estado": "rechazado",
                             "nota": f"mediana {med:.3g} fuera de [{lo}, {hi}]"})
            continue

        out[target] = vals
        channels.append({"canal": target, "origen": str(src), "unidad": units,
                         "factor": f"{factor:g}" + (f" {offset:+g}" if offset else ""),
                         "estado": "mapeado", "nota": ", ".join(notes) or "sin conversión"})

    ts_col = next((c for c in df.columns if c not in used
                   and re.search(r"\btime\b|\btimestamp\b|\bsec\b|\belapsed\b|\bmet\b",
                                 _split_header(c)[0])), None)
    if ts_col is not None:
        t = pd.to_numeric(df[ts_col], errors="coerce").ffill().bfill()
        out["timestamp_sec"] = (t - t.min()).fillna(0).round().astype(int)
    else:
        out["timestamp_sec"] = np.arange(len(out), dtype=int)

    out = out.interpolate(limit_direction="both").fillna(pd.Series(DEFAULTS)).reset_index(drop=True)
    out = out.sort_values("timestamp_sec").reset_index(drop=True)
    # Los tiempos reales se conservan: remapearlos a 0..n mentiría sobre la cadencia del dataset.
    out["timestamp_sec"] = out["timestamp_sec"].round().astype(int)

    mapped = {c["canal"] for c in channels if c["estado"] == "mapeado"}
    core_ok = "temp_c" in mapped and ({"o2_pct"} & mapped or {"co2_ppm"} & mapped)
    report = {
        "ok": bool(core_ok),
        "channels": channels,
        "mapped": sorted(mapped),
        "missing": [c for c in ORDER if c not in mapped],
        "rows": int(len(out)),
        "core_missing": [c for c in ("temp_c",) if c not in mapped],
    }
    return out[["timestamp_sec", *ORDER]], report


def mapear_columnas(df):
    """Compatibilidad: solo el DataFrame canónico."""
    return mapear_dataset(df)[0]


W = 15


def _rate(s, w=W):
    """Tasa por segundo sobre ventana suavizada: rechaza el ruido de 1 Hz del sensor."""
    return s.rolling(w, min_periods=1).mean().diff(w - 1).fillna(0.0) / (w - 1)


def _features(df, w=W):
    d = df
    f = pd.DataFrame(index=d.index)
    f["dCO"] = _rate(d["co_ppm"], w)
    f["dO2"] = _rate(d["o2_pct"], w)
    f["dCO2"] = _rate(d["co2_ppm"], w)
    f["ratio"] = d["co_ppm"] / d["co2_ppm"].clip(lower=1.0) * 100.0
    f["airflow"] = d["airflow_cms"]
    f["rad"] = d["radiative_heat_flux_kwm2"]
    f["hcn"] = d["hcn_ppm"]
    return f.replace([np.inf, -np.inf], 0.0).fillna(0.0)


def detectar_anomalias(df, baseline_seg=60, contaminacion=0.03):
    if len(df) == 0:
        raise ValueError("se requiere telemetría no vacía para entrenar el baseline")
    d = df.reset_index(drop=True).copy()
    w = min(W, max(3, len(d) // 4))  # ventana adaptativa: series cortas no se aplanan
    X = _features(d, w)
    base = X[d["timestamp_sec"] <= baseline_seg]
    if len(base) < 10:  # dataset con cadencia mayor que 6 s por muestra
        base = X.iloc[: max(10, min(baseline_seg, len(X)))]
    sc = StandardScaler().fit(base)
    Zb, Za = sc.transform(base), sc.transform(X)

    modelo = IsolationForest(n_estimators=220, contamination=contaminacion, random_state=42).fit(Zb)
    raw, base_raw = -modelo.score_samples(Za), -modelo.score_samples(Zb)
    # Escala relativa al baseline: 0 % = mediana nominal, 100 % = percentil 99 nominal
    ref = max(float(np.quantile(base_raw, 0.99) - np.median(base_raw)), 1e-6)
    score = np.clip((raw - np.median(base_raw)) / ref, 0.0, 1.0) * 100.0

    # Umbral en la propia distribución del baseline: 4 sigma evita falsos positivos de ruido
    # Suelo en la dispersión: con baseline constante (std=0) el umbral sería la media y todo alertaría.
    sd = max(float(base_raw.std(ddof=0)), 0.02 * abs(float(base_raw.mean())), 1e-9)
    umbral = float(base_raw.mean() + 4.0 * sd)
    d["anomaly_score"] = np.round(pd.Series(score).rolling(3, min_periods=1).mean().to_numpy(), 2)
    d["ia_alerta"] = (raw > umbral)

    pit = np.clip(X["dCO"].to_numpy() / 0.50, 0, 1)
    o2f = np.clip(-X["dO2"].to_numpy() / 0.006, 0, 1)
    hcnf = np.clip(X["hcn"].to_numpy() / 12.0, 0, 1)
    radf = np.clip(X["rad"].to_numpy() / 4.5, 0, 1)
    air = X["airflow"].to_numpy()
    viento = np.clip(np.exp(-((air - 15.0) / 9.0) ** 2), 0.05, 1.0)

    miri = 100.0 * (0.35 * pit + 0.25 * o2f + 0.15 * hcnf + 0.15 * radf + 0.10 * viento)
    d["miri_score"] = np.round(pd.Series(miri).rolling(5, min_periods=1).mean().to_numpy(), 2)
    return d


def _primero(mask):
    idx = np.flatnonzero(np.asarray(mask, dtype=bool))
    return int(idx[0]) if idx.size else None


def calcular_ventaja_deteccion(d):
    ts = d["timestamp_sec"].to_numpy()
    ia = d["ia_alerta"].to_numpy()
    persistente = pd.Series(ia).rolling(3).sum().fillna(0).to_numpy() >= 3
    i_ia = _primero((d["miri_score"].to_numpy() > 35) | persistente)
    i_trad = _primero((d["temp_c"].to_numpy() > 45.0) | (d["smoke_obscuration_pct_m"].to_numpy() > 4.0))
    # Índice de fila -> segundo real del dataset (con 1 Hz coincide, con CSV irregular no).
    t_ia = None if i_ia is None else int(ts[i_ia])
    t_trad = None if i_trad is None else int(ts[i_trad])

    if t_ia is None:
        ver, ventaja = f"Sin evento detectado ({len(d)} s analizados)", None
    elif t_trad is None:
        ver, ventaja = "Detector Tradicional Ciego (Fallo de Detección)", None
    else:
        ventaja = t_trad - t_ia
        ver = (f"+{ventaja} s de anticipación" if ventaja > 0
               else f"El detector tradicional se adelantó {-ventaja} s (revisar umbrales)")
    return {
        "pyroguard_seg": t_ia,
        "tradicional_seg": t_trad,
        "ventaja_seg": ventaja,
        "veredicto": ver,
    }


def _pendiente(y, n=30):
    y = np.asarray(y, dtype=float)[-n:]
    x = np.arange(len(y), dtype=float)
    if len(y) < 3:
        return 0.0
    return float(np.polyfit(x, y, 1)[0])


def generar_protocolo_respuesta(df, atmosfera_o2="ISS Standard (20.9% O2 | 14.7 psi)", corte_ventilacion_seg=0):
    d = df.reset_index(drop=True)
    co_p, co2_p, hcn_p = d["co_ppm"].max(), d["co2_ppm"].max(), d["hcn_ppm"].max()
    temp_p, rad_p, smoke_p = d["temp_c"].max(), d["radiative_heat_flux_kwm2"].max(), d["smoke_obscuration_pct_m"].max()
    o2_min = d["o2_pct"].min()
    ratio = float((co_p / max(co2_p, 1.0)) * 100.0)
    co_f, hcn_f = float(d["co_ppm"].iloc[-1]), float(d["hcn_ppm"].iloc[-1])
    temp_b = float(d["temp_c"].iloc[0])
    ts = d["timestamp_sec"].to_numpy(dtype=float)
    dt = float(np.median(np.diff(ts))) if len(ts) > 1 else 1.0
    dt = dt if dt > 0 else 1.0  # _pendiente va por muestra: se pasa a unidades por segundo
    s_co = max(_pendiente(d["co_ppm"]) / dt, 0.0)
    s_hcn = max(_pendiente(d["hcn_ppm"]) / dt, 0.0)

    if co_p < 6 and hcn_p < 1.2 and rad_p < 0.6:
        tipo, nivel = "Estado Nominal", "NOMINAL"
    elif smoke_p < 0.6 and temp_p < 26.0 and co2_p > 4400 and o2_min < 20.6:
        tipo, nivel = "Llama Fría Oxidativa (Cool Flame)", "PRE-IGNICIÓN"
    elif rad_p > 2.0 or (co_p > 120 and smoke_p > 3.0):
        tipo, nivel = "Combustión Sostenida por Convección Forzada", (
            "CRÍTICO" if (co_p > 120 or rad_p > 2.5) else "PRE-IGNICIÓN")
    elif hcn_p >= 3.0 or (ratio > 1.2 and temp_p < 38.0):
        tipo, nivel = "Pirólisis de Polímeros / Aislamiento Eléctrico", (
            "CRÍTICO" if (hcn_p > 8 or co_p > 100) else "PRE-IGNICIÓN")
    else:
        tipo, nivel = "Combustión Sostenida por Convección Forzada", (
            "CRÍTICO" if (co_p > 120 or rad_p > 2.5) else "PRE-IGNICIÓN")

    candidatos = []
    if s_co > 1e-3:
        candidatos.append((1200.0 - co_f) / s_co)
    if s_hcn > 1e-4:
        candidatos.append((50.0 - hcn_f) / s_hcn)
    candidatos = [c for c in candidatos if c > 0]
    t_critico = int(min(candidatos)) if candidatos else None

    acciones = []
    if corte_ventilacion_seg and corte_ventilacion_seg > 0:
        acciones.append(
            f"1. Aislamiento de Ventilación: corte ejecutado en t={int(corte_ventilacion_seg)} s (airflow "
            f"{d['airflow_cms'].iloc[-1]:.1f} cm/s). Mantener shutters cerrados y ventiladores del rack OFF.")
    else:
        acciones.append(
            "1. Aislamiento de Ventilación: apagar ventiladores del rack afectado y cerrar compuertas "
            "(shutters) para suprimir la convección forzada.")
    acciones += [
        "2. Aislamiento Eléctrico: desenergizar las barras de potencia RPCM del rack implicado y verificar "
        "ausencia de arco antes de cualquier acceso.",
        f"3. Protección de Tripulación: máscaras PBA {'INMEDIATAS (HCN/CO sobre umbral)' if (hcn_p > 5 or co_p > 50) else 'en prevención'} "
        f"— HCN {hcn_p:.1f} ppm, CO {co_p:.0f} ppm.",
        "4. Supresión Activa: descargar extintor de CO2 (PFE) en el puerto de acceso del rack sin abrir la "
        "puerta, evitando el ingreso de O2 fresco.",
        "5. Monitoreo Post-Supresión: verificar atmósfera con CSA-CP antes de reactivar los depuradores CDRA "
        "y autorizar reingreso al módulo.",
    ]

    quimica = (
        f"CO/CO2 = {ratio:.2f} % con CO {co_p:.0f} ppm indica combustión incompleta y "
        f"{'pirólisis de polímeros (Kapton/PVC/Teflón)' if ratio > 1.0 else 'oxidación superficial limitada'}. "
        f"HCN {hcn_p:.1f} ppm confirma degradación térmica de aislamientos nitrogenados; "
        f"flujo radiativo {rad_p:.2f} kW/m² frente a ΔT de solo {temp_p - temp_b:.1f} °C demuestra llama "
        f"esférica fría con emisión IR dominante y caso térmico pasivo."
    )
    fisica = (
        "Sin gravedad no existe flotabilidad: el aire caliente no asciende ni renueva la zona de reacción, "
        "por lo que el O2 llega solo por difusión molecular salvo que la ventilación forzada lo transporte. "
        f"Con {atmosfera_o2} la presión parcial de O2 y el límite de inflamabilidad cambian el régimen "
        "(×1.65 en atmósfera AEA), y el corte de ventilación vuelve la combustión limitada por difusión, "
        "sofocándola en sus propios productos y desacoplando la firma química de la firma térmica."
    )
    return {
        "tipo_combustion": tipo,
        "nivel_amenaza": nivel,
        "tiempo_critico_seg": t_critico,
        "co_ppm_pico": round(float(co_p), 1),
        "hcn_ppm_pico": round(float(hcn_p), 2),
        "co2_ppm_pico": round(float(co2_p), 0),
        "ratio_co_co2_pct": round(ratio, 2),
        "radiative_peak_kwm2": round(float(rad_p), 2),
        "temp_peak_c": round(float(temp_p), 2),
        "temp_baseline_c": round(temp_b, 2),
        "o2_min_pct": round(float(o2_min), 2),
        "analisis_quimico": quimica,
        "acciones_inmediatas": acciones,
        "explicacion_fisica": fisica,
    }
