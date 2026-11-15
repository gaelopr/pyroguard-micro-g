"""Cliente TLCP mínimo (sin dependencias) para el feed público ISSLIVE de la NASA.

En modo streaming, create_session.txt abre directamente el canal de eventos:
  1. GET create_session.txt  -> CONOK,<sid>,...  (la conexión queda abierta)
  2. control.txt (conexión aparte) -> add <suscripción>
  3. los eventos llegan por la conexión del paso 1

Solo se muestran como medidos los canales que el feed publica de verdad: cuando NASA
deja de emitir, llegan frames nulos (`#`) y se cuentan como nulos, no como datos.
"""
from __future__ import annotations

import http.client
import socket
import threading
import time
import urllib.parse
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

HOST = "push.lightstreamer.com"
PATH = "/lightstreamer"
PROTOCOL = "TLCP-2.4.0"
CID = "mgQkwtwdysogQz2BJ4Ji-kOj2Bg"

# Catálogo de canales públicos reales (NASA JSC -> Lightstreamer, adapter set ISSLIVE).
# Nombres de item tomados del diccionario de símbolos público del feed.
PUBLIC_SENSORS = {
    "cabin_temp_c":        ("USLAB000059", "°C",   "Temp. de cabina · US Lab"),
    "cabin_pressure_mmhg": ("USLAB000058", "mmHg", "Presión de cabina · US Lab"),
    "pp_o2_torr":          ("USLAB000053", "torr", "Presión parcial O2 · Lab"),
    "pp_co2_torr":         ("USLAB000055", "torr", "Presión parcial CO2 · Lab"),
    "pp_n2_torr":          ("USLAB000054", "torr", "Presión parcial N2 · Lab"),
    "avionics_fluid_c":    ("USLAB000060", "°C",   "Fluido de aviónica · Lab"),
    "air_cooling_fluid_c": ("USLAB000061", "°C",   "Fluido refrigerante de aire"),
    "coolant_lt_kg":       ("USLAB000056", "kg",   "Refrigerante circuito LT"),
    "coolant_mt_kg":       ("USLAB000057", "kg",   "Refrigerante circuito MT"),
    "urine_tank_pct":      ("NODE3000005", "%",    "Depósito de orina · Node 3"),
    "waste_water_pct":     ("NODE3000008", "%",    "Aguas residuales · Node 3"),
    "clean_water_pct":     ("NODE3000009", "%",    "Agua limpia · Node 3"),
}

# Grupos para suscribir de una vez
PACKS = {
    "Atmósfera (fuego)": ["cabin_temp_c", "cabin_pressure_mmhg", "pp_o2_torr",
                          "pp_co2_torr", "pp_n2_torr"],
    "Térmico (refrigerantes)": ["avionics_fluid_c", "air_cooling_fluid_c",
                                "coolant_lt_kg", "coolant_mt_kg"],
    "Soporte vital (agua)": ["urine_tank_pct", "waste_water_pct", "clean_water_pct"],
}
DEFAULT_CHANNELS = PACKS["Atmósfera (fuego)"]

# Canales que exige el análisis de incendio y que NO existen en el feed público
UNAVAILABLE = [
    ("CO", "ppm"), ("HCN", "ppm"),
    ("Caudal de ventilación del rack", "cm/s"),
    ("Opacidad de humo", "%/m"),
    ("Flujo radiativo", "kW/m²"),
]

NULL = "#"


@dataclass
class FeedStatus:
    state: str = "idle"          # idle | connecting | streaming | error | closed
    detail: str = ""
    session: str = ""
    updates: int = 0
    started_utc: str = ""
    last_update_utc: str = ""
    items: list = field(default_factory=list)


class LightstreamerTLCP:
    def __init__(self, items: dict = None, schema: str = "value",
                 on_update: Callable | None = None, on_status: Callable | None = None,
                 adapter_set: str = "ISSLIVE", protocol: str = PROTOCOL, debug: bool = False,
                 max_frequency_hz: float | None = None, snapshot: bool = True):
        self.items = dict(items or {item: col for col, (item, _, _) in PUBLIC_SENSORS.items()})
        self.schema = schema
        self.on_update = on_update
        self.on_status = on_status
        self.adapter_set = adapter_set
        self.protocol = protocol
        self.debug = debug
        self.max_frequency_hz = max_frequency_hz
        self.snapshot = snapshot
        self.status = FeedStatus(items=list(self.items))
        self._session = ""
        self._stop = threading.Event()
        self._req_id = 0
        self._lock = threading.Lock()
        self._lifecycle = threading.Lock()
        self._started = False

    # ---------------------------------------------------------------- HTTP
    def _open(self, endpoint: str, params: dict, method: str = "GET", timeout: float = 25.0):
        qs = urllib.parse.urlencode(params)
        conn = http.client.HTTPSConnection(HOST, timeout=timeout)
        if method == "GET":
            conn.request("GET", f"{PATH}/{endpoint}?{qs}")
        else:
            conn.request("POST", f"{PATH}/{endpoint}", body=qs,
                         headers={"Content-Type": "application/x-www-form-urlencoded"})
        return conn, conn.getresponse()

    def _set(self, state: str, detail: str = "") -> None:
        self.status.state = state
        self.status.detail = detail
        if self.on_status:
            try:
                self.on_status(self.status)
            except Exception:  # noqa: BLE001
                pass

    def _log(self, tag: str, text: str) -> None:
        if self.debug:
            print(f"[{tag}] {text[:180]}", flush=True)

    # ---------------------------------------------------------- lifecycle
    def start(self) -> None:
        """Idempotente: dos clics seguidos no abren dos streams sobre la misma sesión."""
        with self._lifecycle:
            if self._started:
                return
            self._started = True
        self._stop.clear()
        threading.Thread(target=self._run, name="tlcp", daemon=True).start()

    def stop(self) -> None:
        with self._lifecycle:
            self._started = False
        self._stop.set()
        if self._session:
            try:
                self._command({"LS_op": "destroy"})
            except Exception:  # noqa: BLE001
                pass
        self._set("closed", "sesión cerrada")

    # ---------------------------------------------------------- commands
    def _command(self, payload: dict) -> str:
        if not self._session:
            self._log("cmd", "sin sesión: comando descartado")
            return ""
        with self._lock:
            self._req_id += 1
            conn, resp = self._open("control.txt", {
                "LS_session": self._session, "LS_protocol": self.protocol,
                "LS_reqId": str(self._req_id), **payload}, method="GET", timeout=12)
            try:
                body = resp.read().decode("utf-8", "replace")
            except Exception as exc:  # noqa: BLE001
                body = f"READ {exc}"
            conn.close()
        self._log("cmd", f"HTTP {resp.status} {resp.reason} | {body.replace(chr(13) + chr(10), ' | ')} | hdr={dict(list(resp.getheaders())[:6])}")
        return body

    def _subscribe(self) -> None:
        deadline = time.time() + 12
        while not self._session and time.time() < deadline and not self._stop.is_set():
            time.sleep(0.2)
        payload = {"LS_op": "add", "LS_subId": "1", "LS_mode": "MERGE",
                   "LS_group": ",".join(self.items), "LS_schema": self.schema,
                   "LS_snapshot": "true" if self.snapshot else "false"}
        if self.max_frequency_hz:
            payload["LS_requested_max_frequency"] = str(self.max_frequency_hz)
        self._command(payload)

    # ------------------------------------------------------------- stream
    def _run(self) -> None:
        backoff = 3
        while not self._stop.is_set():
            conn = None
            try:
                self._set("connecting", "abriendo stream")
                conn, resp = self._open("create_session.txt", {
                    "LS_protocol": self.protocol, "LS_cid": CID,
                    "LS_adapter_set": self.adapter_set, "LS_polling": "false",
                    "LS_streaming_millis": "120000"}, method="GET", timeout=35)
                if resp.status != 200:
                    raise RuntimeError(f"HTTP {resp.status}")
                threading.Thread(target=self._subscribe, daemon=True).start()
                self._consume(resp)
            except Exception as exc:  # noqa: BLE001
                self._set("error", f"{type(exc).__name__}: {exc}")
            finally:
                self._session = ""
                if conn:
                    conn.close()
            if self._stop.is_set():
                break
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 20)

    def _consume(self, resp) -> None:
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = resp.read1(2048)
            except (socket.timeout, TimeoutError):
                continue
            except Exception as exc:  # noqa: BLE001
                self._set("error", f"stream: {exc}")
                return
            if not chunk:
                return
            buf += chunk
            while b"\r\n" in buf:
                raw, buf = buf.split(b"\r\n", 1)
                self._line(raw.decode("utf-8", "replace"))

    def _line(self, line: str) -> None:
        if not line:
            return
        self._log("stream", line)
        head = line.split(",")[0]
        if head == "CONOK":
            parts = line.split(",")
            if len(parts) > 1:
                self._session = parts[1]
                self.status.session = parts[1]
                self.status.started_utc = time.strftime("%H:%M:%SZ", time.gmtime())
            self._set("streaming", "sesión abierta · suscribiendo")
            return
        if head == "SUBOK":
            parts = line.split(",")
            self.status.items = parts[4:] or list(self.items)
            self._set("streaming", "suscripción activa")
            return
        if head == "SYNC":
            return
        if head in ("CONS", "CONF", "PROBE", "LOOP", "SERVNAME", "CLIENTIP", "UNSUBOK", "END",
                    "REQOK", "NOOP"):
            return
        if head in ("ERROR", "CONERR", "SUBERR", "REQERR", "SYNC ERROR"):
            self._set("error", line[:160])
            return
        if head != "U":
            return
        self.status.updates += 1
        self.status.last_update_utc = time.strftime("%H:%M:%SZ", time.gmtime())
        if self.status.state != "streaming":
            self._set("streaming", "eventos recibidos")
        if self.on_update:
            try:
                self.on_update(line)
            except Exception:  # noqa: BLE001
                pass


class LiveISS:
    """Sesión ISSLIVE + buffer de muestras reales (sin inventar canales ausentes)."""

    def __init__(self, maxlen: int = 2400, debug: bool = False,
                 channels: list | None = None, max_frequency_hz: float | None = None,
                 snapshot: bool = True):
        cols = [c for c in (channels or DEFAULT_CHANNELS) if c in PUBLIC_SENSORS]
        self.channels = cols or list(DEFAULT_CHANNELS)
        self._lock = threading.Lock()
        self._seq = 0
        self._rows: deque = deque(maxlen=maxlen)
        self._stats = {c: {"item": PUBLIC_SENSORS[c][0], "unit": PUBLIC_SENSORS[c][1],
                           "label": PUBLIC_SENSORS[c][2], "events": 0, "nulls": 0,
                           "last": None, "last_utc": "", "first_utc": ""}
                       for c in self.channels}
        self.client = LightstreamerTLCP(
            items={PUBLIC_SENSORS[c][0]: c for c in self.channels},
            on_update=self._on_update, debug=debug,
            max_frequency_hz=max_frequency_hz, snapshot=snapshot)

    # ---------------------------------------------------------- ingestion
    def _on_update(self, line: str) -> None:
        parts = line.split(",")
        if parts[0] != "U" or len(parts) < 4:
            return
        item = parts[2]
        # Una coma decimal europea ("23,4") añade campos: se reensambla en vez de truncar a 23.
        value = ",".join(parts[3:]) if len(parts) > 4 else parts[3]
        col = next((c for c, (i, _, _) in PUBLIC_SENSORS.items() if i == item), None)
        if col is None:
            return
        stamp = time.strftime("%H:%M:%SZ", time.gmtime())
        st = self._stats.get(col)
        if value.strip() in (NULL, "", None):
            if st is not None:
                st["nulls"] += 1
                st["last_utc"] = stamp
            return
        num = str(value).replace(" ", "").replace("\u00a0", "")
        if num.count(",") == 1 and "." in num:      # 1,234.5
            num = num.replace(",", "")
        elif num.count(",") == 1 and "." not in num:  # 23,4
            num = num.replace(",", ".")
        else:
            num = num.replace(",", "")
        try:
            val = float(num)
        except ValueError:
            return
        with self._lock:
            self._seq += 1
            self._rows.append({"seq": self._seq, "utc": time.time(), "channel": col, "value": val})
        if st is not None:
            st["events"] += 1
            st["last"] = val
            st["last_utc"] = stamp
            if not st["first_utc"]:
                st["first_utc"] = stamp

    # ------------------------------------------------------------- reading
    def start(self) -> None:
        self.client.start()

    def stop(self) -> None:
        self.client.stop()

    @property
    def status(self) -> FeedStatus:
        return self.client.status

    def frame(self) -> pd.DataFrame:
        cols = list(self.channels)
        with self._lock:
            rows = list(self._rows)
        if not rows:
            return pd.DataFrame(columns=["seq", "t", "clock", "utc", *cols])
        df = pd.DataFrame(rows)
        wide = df.pivot_table(index="seq", columns="channel", values="value", aggfunc="last")
        wide = wide.reindex(columns=cols).reset_index()
        stamps = df.groupby("seq")["utc"].first().reindex(wide["seq"]).to_numpy()
        wide.insert(1, "t", (stamps - stamps.min()).round(1))
        ts = pd.to_datetime(stamps, unit="s", utc=True)
        wide.insert(2, "clock", ts.strftime("%H:%M:%S"))
        wide.insert(3, "utc", ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
        return self._derive(wide)

    @staticmethod
    def _derive(df: pd.DataFrame) -> pd.DataFrame:
        """Concentraciones derivadas de presiones parciales medidas (nunca inventadas)."""
        if "pp_o2_torr" in df.columns:
            base = (df["cabin_pressure_mmhg"] if "cabin_pressure_mmhg" in df.columns
                    and df["cabin_pressure_mmhg"].notna().any() else 760.0)
            df["o2_pct_from_pp"] = (df["pp_o2_torr"] / base * 100).round(3)
        if "pp_co2_torr" in df.columns:
            base = (df["cabin_pressure_mmhg"] if "cabin_pressure_mmhg" in df.columns
                    and df["cabin_pressure_mmhg"].notna().any() else 760.0)
            df["co2_ppm_from_pp"] = (df["pp_co2_torr"] / base * 1e6).round(1)
        return df

    def diagnostics(self) -> pd.DataFrame:
        """Contadores por canal: eventos con número, nulos y último valor."""
        rows = []
        for col, st in self._stats.items():
            last = st["last"]
            rows.append({
                "canal": st["label"], "item": st["item"], "unidad": st["unit"],
                "numeros": st["events"], "nulos": st["nulls"],
                "ultimo": "" if last is None else f"{last:.2f}",
                "hora": st["last_utc"] or "—",
            })
        return pd.DataFrame(rows)

    def coverage(self) -> dict:
        df = self.frame()
        measured = [c for c in self.channels if c in df.columns and df[c].notna().any()]
        return {"measured": measured, "available": len(self.channels),
                "missing_required": len(UNAVAILABLE), "samples": int(len(df))}


def probe(channels: list | None = None, seconds: float = 10.0,
          max_frequency_hz: float | None = None, snapshot: bool = True) -> dict:
    """Sonda el feed durante N segundos con una sesión temporal y devuelve el recuento.

    Sirve para comprobar, aquí y ahora, qué canales publican números y cuáles llegan
    nulos: no estima nada.
    """
    cols = [c for c in (channels or DEFAULT_CHANNELS) if c in PUBLIC_SENSORS]
    counts = {c: {"numeros": 0, "nulos": 0, "ultimo": None} for c in cols}

    def on_update(line: str) -> None:
        parts = line.split(",")
        if parts[0] != "U" or len(parts) < 4:
            return
        item = parts[2]
        value = ",".join(parts[3:]) if len(parts) > 4 else parts[3]
        col = next((c for c, (i, _, _) in PUBLIC_SENSORS.items() if i == item), None)
        if col is None or col not in counts:
            return
        if value.strip() in (NULL, ""):
            counts[col]["nulos"] += 1
            return
        try:
            counts[col]["ultimo"] = float(value.replace(",", "."))
            counts[col]["numeros"] += 1
        except ValueError:
            counts[col]["nulos"] += 1

    client = LightstreamerTLCP(items={PUBLIC_SENSORS[c][0]: c for c in cols},
                               on_update=on_update, max_frequency_hz=max_frequency_hz,
                               snapshot=snapshot)
    client.start()
    time.sleep(seconds)
    state = client.status.state
    items = list(client.status.items)
    client.stop()
    rows = []
    for col in cols:
        item, unit, label = PUBLIC_SENSORS[col]
        rows.append({"canal": label, "item": item, "unidad": unit,
                     "numeros": counts[col]["numeros"], "nulos": counts[col]["nulos"],
                     "ultimo": "" if counts[col]["ultimo"] is None else f"{counts[col]['ultimo']:.2f}"})
    return {"estado": state, "items": items, "segundos": seconds,
            "canales": rows, "con_dato": sum(1 for c in rows if c["numeros"] > 0)}


if __name__ == "__main__":
    def _show(line):
        print(f"{time.strftime('%H:%M:%S')}  EVENT  {line}", flush=True)

    c = LightstreamerTLCP(on_update=_show, debug=True)
    c.start()
    end = time.time() + 30
    try:
        while time.time() < end:
            time.sleep(1)
            print(f"  estado={c.status.state} updates={c.status.updates} "
                  f"detail={c.status.detail}", flush=True)
    finally:
        c.stop()
