"""Datos históricos reales de la NASA desde PSI (Physical Sciences Informatics).

PSI publica las investigaciones en microgravedad con licencia CC0 y expone dos rutas
abiertas, sin credenciales ni API key:

  * metadatos:  https://psi.nasa.gov/geode-py/ws/repo/investigations/<ACC>
  * descarga:   https://psi.nasa.gov/geode-py/ws/studies/<ACC>/download?file=<fichero>

Lo que hay aquí son las **tablas experimentales del vuelo** (material, flujo, %O2,
tiempos de ignición y combustión), no telemetría de cabina de la ISS: el feed de la
estación es solo en vivo y no tiene histórico público. Las series temporales crudas de
Saffire son archivos de imágenes y telemetría de 11 a 33 GB, fuera del alcance de la app.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import pandas as pd

META_URL = "https://psi.nasa.gov/geode-py/ws/repo/investigations/{acc}"
DOWNLOAD_URL = "https://psi.nasa.gov/geode-py/ws/studies/{acc}/download?file={name}"
UA = "PyroGuardMicroG/1.0 (NASA Space Apps; contacto en el repositorio)"

INVESTIGATIONS = {
    "PSI-98": {"label": "Saffire-I · 2016", "platform": "Cygnus (OA-6)"},
    "PSI-99": {"label": "Saffire-II · 2016", "platform": "Cygnus (OA-5)"},
    "PSI-100": {"label": "Saffire-III · 2017", "platform": "Cygnus (OA-7)"},
}

# Nombres de columna tal como llegan (con erratas incluidas) -> nombre legible
_RENAME = {
    "sample number": "muestra",
    "material": "material",
    "sample thickness (cm)": "espesor_cm",
    "sample thickness": "espesor_cm",
    "samle thickness": "espesor_cm",
    "sample length (cm)": "longitud_cm",
    "sample length": "longitud_cm",
    "sample width (cm)": "anchura_cm",
    "sample width": "anchura_cm",
    "air flow (cm/s)": "flujo_cms",
    "air flow": "flujo_cms",
    "percent o2": "o2_pct",
    "percent o2 (note 1)": "o2_pct",
    "ignition power (w)": "potencia_ignicion_w",
    "ignition time (s)": "tiempo_ignicion_s",
    "burn time (s)": "tiempo_combustion_s",
    "flow direction": "direccion",
    "direction": "direccion",
    "camera 1": "camara_1",
    "camera 2": "camara_2",
    "?-g burn length": "longitud_quemada_0g",
    "?-g spread length": "longitud_propagada_0g",
    "1-g burn length": "longitud_quemada_1g",
    "1-g spread rate": "velocidad_propagacion_1g",
}


def parse_table(text: str) -> pd.DataFrame:
    """Normaliza la tabla experimental de PSI (cabeceras sucias incluidas)."""
    df = pd.read_csv(io.StringIO(text), sep=",", engine="python")
    out = {}
    for col in df.columns:
        key = str(col).strip().lower().replace("\ufeff", "")
        out[col] = _RENAME.get(key, key.replace(" ", "_") or "col")
    df = df.rename(columns=out)
    df = df.dropna(how="all")
    if "muestra" in df.columns:
        df["muestra"] = df["muestra"].astype(str).str.strip()
        df = df[df["muestra"].str.lower() != "nan"]
    # Algunas tablas cuelan filas de «pre-test flow visualisation», que no son muestras.
    if "material" in df.columns:
        pre = df["material"].astype(str).str.lower().str.contains("pre-test|pre test", regex=True)
        df = df[~pre]
    return df.reset_index(drop=True)


def _get(url: str, timeout: float = 25.0) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch(acc: str) -> dict:
    """Descarga metadatos + tabla experimental de una investigación PSI.

    Devuelve también la trazabilidad: URL exacta, tamaño, SHA-256 y hora de descarga,
    para que la app pueda citar de dónde salió cada fila.
    """
    if acc not in INVESTIGATIONS:
        raise ValueError(f"investigación desconocida: {acc}")
    meta_raw = _get(META_URL.format(acc=acc))
    meta = json.loads(meta_raw.decode("utf-8", "replace"))
    tables = meta.get("experimentalTable") or []
    if not tables:
        raise RuntimeError(f"{acc} no publica tabla experimental descargable")
    name = tables[0]["file_name"]
    url = DOWNLOAD_URL.format(acc=acc, name=urllib.parse.quote(name))
    raw = _get(url, timeout=40.0)
    text = raw.decode("utf-8", "replace")
    return {
        "acc": acc,
        "titulo": meta.get("title") or INVESTIGATIONS[acc]["label"],
        "doi": meta.get("doi", ""),
        "licencia": meta.get("licenseName", ""),
        "licencia_url": meta.get("licenseLink", ""),
        "resumen": (meta.get("description") or meta.get("objective") or "").strip(),
        "file": name,
        "url": url,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "descargado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tabla": parse_table(text),
    }


def resumen(df: pd.DataFrame) -> dict:
    """Cifras que la tabla permite afirmar, sin inventar nada."""
    out = {"muestras": int(len(df))}
    if "material" in df.columns:
        mats = sorted({str(m).strip() for m in df["material"].dropna()
                       if str(m).strip() and str(m).strip().lower() != "nan"})
        out["materiales"] = len(mats)
        out["lista_materiales"] = mats
    if "o2_pct" in df.columns:
        o2 = pd.to_numeric(df["o2_pct"].astype(str).str.replace("~", "", regex=False),
                           errors="coerce").dropna()
        if len(o2):
            out["o2_rango"] = f"{o2.min():.1f}–{o2.max():.1f} %"
    if "flujo_cms" in df.columns:
        fl = pd.to_numeric(df["flujo_cms"].astype(str).str.replace("cm/s", "", regex=False)
                           .str.replace("~", "", regex=False), errors="coerce").dropna()
        if len(fl):
            out["flujo_rango"] = f"{fl.min():.0f}–{fl.max():.0f} cm/s"
    return out
