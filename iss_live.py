"""Cliente TLCP mínimo (sin dependencias) para el feed público ISSLIVE de la NASA.

En modo streaming, create_session.txt abre directamente el canal de eventos:
  1. GET create_session.txt  -> CONOK,<sid>,...  (la conexión queda abierta)
  2. control.txt (conexión aparte) -> add <suscripción>
  3. los eventos llegan por la conexión del paso 1
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

# Canales públicos reales (NASA JSC -> Lightstreamer, adapter set ISSLIVE)
ITEMS = {
    "USLAB000059": "cabin_temp_c",
    "USLAB000058": "cabin_pressure_mmhg",
    "TIME_000001": "gmt",
}


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
                 adapter_set: str = "ISSLIVE", protocol: str = PROTOCOL, debug: bool = False):
        self.items = dict(items or ITEMS)
        self.schema = schema
        self.on_update = on_update
        self.on_status = on_status
        self.adapter_set = adapter_set
        self.protocol = protocol
        self.debug = debug
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
        self._command({"LS_op": "add", "LS_subId": "1", "LS_mode": "MERGE",
                       "LS_group": ",".join(self.items), "LS_schema": self.schema,
                       "LS_snapshot": "true"})

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


# Canales realmente medidos en el feed público (NASA JSC -> Lightstreamer)
PUBLIC_SENSORS = {
    "cabin_temp_c": ("USLAB000059", "°C", "Temperatura de cabina US Lab"),
    "cabin_pressure_mmhg": ("USLAB000058", "mmHg", "Presión de cabina US Lab"),
}

# Canales que exige el análisis de incendio y que NO existen en el feed público
UNAVAILABLE = [
    ("CO", "ppm"), ("HCN", "ppm"), ("CO2", "ppm"),
    ("Caudal de ventilación del rack", "cm/s"),
    ("Opacidad de humo", "%/m"),
    ("Flujo radiativo", "kW/m²"),
]

NULL = "#"


class LiveISS:
    """Sesión ISSLIVE + buffer de muestras reales (sin inventar canales ausentes)."""

    def __init__(self, maxlen: int = 2400, debug: bool = False):
        self._lock = threading.Lock()
        self._seq = 0
        self._rows: deque = deque(maxlen=maxlen)
        self.client = LightstreamerTLCP(
            items={item: col for col, (item, _, _) in PUBLIC_SENSORS.items()},
            on_update=self._on_update, debug=debug)

    # ---------------------------------------------------------- ingestion
    def _on_update(self, line: str) -> None:
        parts = line.split(",")
        if parts[0] != "U" or len(parts) < 4:
            return
        item = parts[2]
        # Una coma decimal europea ("23,4") añade campos: se reensambla en vez de truncar a 23.
        value = ",".join(parts[3:]) if len(parts) > 4 else parts[3]
        col = next((c for c, (i, _, _) in PUBLIC_SENSORS.items() if i == item), None)
        if col is None or value in (NULL, "", None):
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

    # ------------------------------------------------------------- reading
    def start(self) -> None:
        self.client.start()

    def stop(self) -> None:
        self.client.stop()

    @property
    def status(self) -> FeedStatus:
        return self.client.status

    def frame(self) -> pd.DataFrame:
        with self._lock:
            rows = list(self._rows)
        if not rows:
            return pd.DataFrame(columns=["seq", "t", "clock", "utc", *PUBLIC_SENSORS])
        df = pd.DataFrame(rows)
        wide = df.pivot_table(index="seq", columns="channel", values="value", aggfunc="last")
        wide = wide.reindex(columns=list(PUBLIC_SENSORS)).reset_index()
        stamps = df.groupby("seq")["utc"].first().reindex(wide["seq"]).to_numpy()
        wide.insert(1, "t", (stamps - stamps.min()).round(1))
        ts = pd.to_datetime(stamps, unit="s", utc=True)
        wide.insert(2, "clock", ts.strftime("%H:%M:%S"))
        wide.insert(3, "utc", ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
        return wide

    def coverage(self) -> dict:
        df = self.frame()
        measured = [c for c in PUBLIC_SENSORS if c in df.columns and df[c].notna().any()]
        return {"measured": measured, "available": len(PUBLIC_SENSORS),
                "missing_required": len(UNAVAILABLE), "samples": int(len(df))}


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
