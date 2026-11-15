import html
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import anomaly_engine as ae
import iss_live
import nasa_psi
import physics_simulator as ps

st.set_page_config(layout="wide", page_title="PyroGuard Micro-G | NASA Fire Safety", page_icon="🛰️",
                   initial_sidebar_state="expanded")

_PAL = {
    "dark": dict(
        bg="#04070b", glow1="rgba(0,229,255,.10)", glow2="rgba(255,107,53,.075)",
        grid="rgba(255,255,255,.020)", ink="#C9D6E5", head="#EAF4FF", dim="#7FA0BF",
        dim2="#6E8AA6", dim3="#5E7A96", faint="#3E5A73", line="rgba(128,170,210,.14)",
        line2="rgba(128,170,210,.22)", hair="rgba(255,255,255,.05)", panel="rgba(10,18,28,.62)",
        panel2="rgba(8,14,24,.72)", panel3="rgba(13,27,42,.92)", side="#070c13",
        header="linear-gradient(90deg, rgba(0,229,255,.07), rgba(6,10,16,.45) 58%, rgba(255,107,53,.06))",
        btn="rgba(12,22,34,.92)", btnink="#DCE8F5", hover="rgba(0,229,255,.09)", shadow="rgba(0,0,0,.55)",
        ringbg="rgba(255,255,255,.07)", cyan="#00E5FF", cyanline="rgba(0,229,255,.26)", cyansoft="#8FD8E8",
        green="#39FF88", greenline="rgba(57,255,136,.4)", yellow="#FFD166", red="#FF3B30",
        orange="#FF6B35", violet="#B47CFF", plot="rgba(8,14,24,.55)", template="plotly_dark",
    ),
    "light": dict(
        bg="#f2f6fb", glow1="rgba(0,150,190,.10)", glow2="rgba(255,107,53,.07)",
        grid="rgba(11,26,43,.045)", ink="#22364b", head="#0a1a2b", dim="#46617f",
        dim2="#58718d", dim3="#6a829c", faint="#94a8bd", line="rgba(16,48,80,.14)",
        line2="rgba(16,48,80,.26)", hair="rgba(16,48,80,.10)", panel="rgba(255,255,255,.86)",
        panel2="rgba(255,255,255,.92)", panel3="#ffffff", side="#ffffff",
        header="linear-gradient(90deg, rgba(0,137,167,.10), rgba(255,255,255,.75) 58%, rgba(255,107,53,.08))",
        btn="#ffffff", btnink="#14304b", hover="rgba(0,137,167,.10)", shadow="rgba(9,30,60,.14)",
        ringbg="rgba(16,48,80,.10)", cyan="#0089a7", cyanline="rgba(0,137,167,.35)", cyansoft="#0b6b82",
        green="#15803d", greenline="rgba(21,128,61,.45)", yellow="#b45309", red="#c1121f",
        orange="#c2530a", violet="#6d28d9", plot="#ffffff", template="plotly_white",
    ),
}


def _sistema() -> str:
    """Preferencia del sistema operativo/navegador ('light' o 'dark')."""
    try:
        tipo = getattr(st.context.theme, "type", None)
        if tipo in ("light", "dark"):
            return tipo
    except Exception:
        pass
    return "dark"


_PREF = st.query_params.get("theme", "auto")
if _PREF not in ("auto", "light", "dark"):
    _PREF = "auto"
TEMA = _sistema() if _PREF == "auto" else _PREF   # tema efectivo
T = _PAL[TEMA]
PLOT = {"template": T["template"], "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": T["plot"]}
_VARS = ":root{" + "".join(f"--{k}:{v};" for k, v in T.items() if k != "template") + "}"

RED, ORANGE, CYAN, GREEN, YELLOW, VIOLET = (T["red"], T["orange"], T["cyan"], T["green"],
                                            T["yellow"], T["violet"])
PCFG = {"displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines",
                                   "hoverClosestCartesian", "hoverCompareCartesian"]}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;800&display=swap');
.stApp { background-color:var(--bg);
  background-image:
    radial-gradient(900px 420px at 14% -8%, var(--glow1), transparent 62%),
    radial-gradient(720px 380px at 88% -2%, var(--glow2), transparent 62%),
    linear-gradient(var(--grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: auto, auto, 46px 46px, 46px 46px;
  background-attachment: fixed; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--ink); }
h1, h2, h3, h4 { font-family: 'Share Tech Mono', monospace !important; letter-spacing: .05em; color: var(--head); }
.block-container { padding-top: 3.2rem; padding-bottom: 2.4rem; max-width: 1320px; }
.pg-header { display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;
  border:1px solid var(--cyanline); border-radius:12px; padding:14px 18px;
  background: var(--header); }
.pg-title { font-family:'Share Tech Mono',monospace; font-size:24px; color:var(--head); letter-spacing:.04em; }
.pg-sub { color:var(--dim); font-size:10.5px; letter-spacing:.2em; text-transform:uppercase; margin-top:5px; }
.pg-tags { display:flex; gap:6px; flex-wrap:wrap; }
.pg-tag { border:1px solid var(--cyanline); color:var(--cyansoft); border-radius:4px; padding:2px 8px;
  font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.1em; }
.pg-tag-live { border-color:var(--greenline); color:var(--green); }
[data-testid="stWidgetLabel"] p { font-family:'Share Tech Mono',monospace; font-size:10px !important;
  letter-spacing:.13em; text-transform:uppercase; color:var(--dim2) !important; }
.pg-card { border:1px solid var(--line); border-radius:10px; padding:11px 14px;
  background:var(--panel); min-height:92px; display:flex; flex-direction:column; justify-content:space-between; }
.pg-kpi-label { font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.13em;
  color:var(--dim2); text-transform:uppercase; }
.pg-kpi { font-family:'Share Tech Mono',monospace; font-size:21px; color:var(--head); line-height:1.15;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.pg-kpi-sm { font-size:15px; }
.pg-nom { color:var(--green); } .pg-pre { color:var(--yellow); } .pg-crit { color:var(--red); }
.pg-strip { display:flex; gap:6px; flex-wrap:wrap; margin:2px 0 10px 0; }
.pg-chip { flex:1 1 92px; border:1px solid var(--line); border-radius:8px;
  padding:6px 9px; background:var(--panel2); }
.pg-chip-l { display:block; font-family:'Share Tech Mono',monospace; font-size:8.5px;
  letter-spacing:.12em; color:var(--dim3); text-transform:uppercase; }
.pg-chip-v { display:block; font-family:'Share Tech Mono',monospace; font-size:15px; color:var(--head); }
.pg-chip-v i { font-style:normal; font-size:9.5px; color:var(--dim); margin-left:3px; }
.pg-step { border-left:2px solid var(--orange); padding-left:11px; margin-bottom:8px;
  font-size:13px; color:var(--ink); line-height:1.45; }
.pg-note { font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.14em; color:var(--faint);
  text-align:center; margin-top:16px; }
/* ---------- veredicto: tarjeta principal con anillo ---------- */
.pg-hero { display:grid; grid-template-columns:132px 1fr; gap:24px; align-items:center;
  margin:4px 0 14px; border:1px solid var(--line2); border-radius:16px;
  padding:16px 20px; background:linear-gradient(135deg, var(--panel3), var(--panel2));
  box-shadow:0 24px 50px -34px var(--shadow), inset 0 1px 0 var(--ringbg); }
.pg-ring { position:relative; width:124px; height:124px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; }
.pg-ring svg { position:absolute; inset:0; transform:rotate(-90deg); }
.pg-ring-bg { fill:none; stroke:var(--ringbg); stroke-width:9; }
.pg-ring-fg { fill:none; stroke-width:9; stroke-linecap:round; transition:stroke-dashoffset .7s ease; }
.pg-ring-v { font-family:'Share Tech Mono',monospace; font-size:25px; color:var(--head); line-height:1;
  display:flex; align-items:baseline; gap:1px; }
.pg-ring-l { display:block; margin-top:5px; font-family:'Share Tech Mono',monospace; font-size:7.5px;
  letter-spacing:.18em; color:var(--dim3); text-transform:uppercase; }
.pg-hero-top { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.pg-pill { font-family:'Share Tech Mono',monospace; font-size:10.5px; letter-spacing:.15em;
  padding:4px 11px; border-radius:999px; border:1px solid currentColor; }
.pg-hero-sub { font-size:12.5px; color:var(--dim); }
.pg-hero-kpis { display:flex; gap:26px; flex-wrap:wrap; margin:11px 0 2px; }
.pg-hero-kpis > div { display:flex; flex-direction:column; gap:2px; }
.pg-hero-kpis span { font-family:'Share Tech Mono',monospace; font-size:8.5px; letter-spacing:.12em;
  color:var(--dim3); text-transform:uppercase; }
.pg-hero-kpis b { font-family:'Share Tech Mono',monospace; font-size:17px; font-weight:400; color:var(--head); }
.pg-hero-cta { margin-top:10px; font-size:12.5px; color:var(--ink); border-left:2px solid var(--cyan);
  padding-left:10px; line-height:1.5; }
.pg-hero-cta b { color:var(--head); }
@keyframes pgpulse { 0%,100%{opacity:1} 50%{opacity:.42} }
.pg-pulse { animation:pgpulse 1.9s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) { .pg-pulse { animation:none; } }
@media (max-width: 680px) {
  .pg-hero { grid-template-columns:1fr; justify-items:start; gap:14px; padding:14px 15px; }
  .pg-ring { width:104px; height:104px; }
  .pg-ring-v { font-size:22px; }
  .pg-hero-kpis { gap:16px; }
  div[data-testid="stHorizontalBlock"] { flex-wrap:wrap !important; }
  div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { min-width:44% !important; }
  div[data-testid="stButton"] button { white-space:nowrap; }
}
/* ---------- controles ---------- */
div[data-testid="stButton"] button { border-radius:9px; border:1px solid var(--line2);
  background:var(--btn); color:var(--btnink); font-family:'Share Tech Mono',monospace;
  font-size:11px; letter-spacing:.07em; padding:7px 13px; transition:.16s ease; }
div[data-testid="stButton"] button:hover { border-color:var(--cyanline); color:var(--head);
  background:var(--hover); transform:translateY(-1px); }
div[data-testid="stButton"] button:focus-visible { outline:2px solid var(--cyan); outline-offset:2px; }
div[data-testid="stMetric"] { border:1px solid var(--line); border-radius:10px;
  padding:9px 12px; background:var(--panel2); }
div[data-testid="stMetricValue"] { font-family:'Share Tech Mono',monospace; color:var(--head) !important;
  font-size:19px; }
[data-testid="stMetricDelta"] { background:transparent !important; color:var(--green) !important; }
[data-testid="stMetricDelta"] svg { fill:var(--green) !important; }
div[data-testid="stMetricLabel"] p { font-size:10px !important; letter-spacing:.1em; text-transform:uppercase;
  color:var(--dim2) !important; }
[data-testid="stAlertContainer"] { background:var(--panel2) !important; }
[data-testid="stAlertContainer"] p { color:var(--ink) !important; }
div[data-testid="stAlert"] { border-radius:10px; background:var(--panel) !important;
  border:1px solid var(--line2) !important; }
div[data-testid="stAlert"] p, div[data-testid="stAlert"] li { color:var(--ink) !important; }
div[data-testid="stSidebar"] { background:var(--side); border-right:1px solid var(--cyanline); }
.pg-side-h { font-family:'Share Tech Mono',monospace; font-size:15px; color:var(--head); letter-spacing:.04em; }
.pg-side-s { color:var(--dim2); font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; margin-top:4px; }
.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-family:'Share Tech Mono',monospace; font-size:12px;
  letter-spacing:.1em; padding:8px 14px; color:var(--dim2); }
.stTabs [aria-selected="true"] { color:var(--cyan) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:var(--cyan); }
/* ---------- superficies de widgets (siguen el tema activo) ---------- */
div[data-baseweb="select"] > div { background-color:var(--panel2) !important;
  border-color:var(--line2) !important; color:var(--head) !important; }
div[data-baseweb="popover"] div[role="listbox"], div[data-baseweb="popover"] ul { background-color:var(--panel3) !important; }
div[data-baseweb="popover"] li, div[data-baseweb="popover"] div[role="option"] { color:var(--ink) !important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="popover"] div[role="option"]:hover { background-color:var(--hover) !important; }
[data-testid="stFileUploader"] section { background:var(--panel2); border-color:var(--line2); }
[data-testid="stFileChip"] { background:var(--panel2) !important; border:1px solid var(--line2) !important; }
[data-testid="stFileChip"] *, [data-testid="stFileChipName"] { color:var(--ink) !important; }
[data-testid="stFileChip"] svg { fill:var(--ink) !important; }
[data-testid="stCodeBlock"], [data-testid="stMarkdownContainer"] code {
  background:var(--panel2) !important; color:var(--head) !important; border-color:var(--line2) !important; }
[data-testid="stFileUploader"] section small, [data-testid="stFileUploader"] section span { color:var(--dim); }
[data-testid="stExpander"] details { background:var(--panel2); border-color:var(--line2); }
[data-testid="stExpander"] summary { color:var(--head); }
[data-testid="stCaptionContainer"] p { color:var(--dim2) !important; }
[data-testid="stToggle"] p, [data-testid="stRadio"] p, [data-testid="stCheckbox"] p,
[data-testid="stToggle"] span, [data-testid="stRadio"] span { color:var(--ink) !important; }
[data-testid="stToggle"] svg, [data-testid="stRadio"] svg { color:var(--cyan); }
div[data-testid="stButton"] button, div[data-testid="stButton"] button:focus:not(:active) {
  background:var(--btn) !important; color:var(--btnink) !important; border-color:var(--line2) !important; }
div[data-testid="stButton"] button:hover { background:var(--hover) !important; color:var(--head) !important;
  border-color:var(--cyanline) !important; }
section[data-testid="stSidebar"], div[data-testid="stSidebar"] { background:var(--side) !important; }
header[data-testid="stHeader"], div[data-testid="stToolbar"] { background:transparent !important; }
[data-testid="stAlertContentSuccess"], [data-testid="stAlertContentInfo"],
[data-testid="stAlertContentWarning"], [data-testid="stAlertContentError"] {
  background:transparent !important; color:var(--ink) !important; }
[data-testid="stAlert"] svg { fill:currentColor !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong, [data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] code { color:var(--ink) !important; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5, [data-testid="stMarkdownContainer"] h6 {
  color:var(--head) !important; }
.pg-tblwrap { overflow-x:auto; border:1px solid var(--line); border-radius:10px; margin-top:6px; }
.pg-tbl { width:100%; border-collapse:collapse; font-family:'Share Tech Mono',monospace; font-size:11.5px; }
.pg-tbl thead th { text-align:left; padding:7px 10px; background:var(--panel2); color:var(--dim2);
  font-weight:400; letter-spacing:.1em; text-transform:uppercase; font-size:9.5px;
  border-bottom:1px solid var(--line); white-space:nowrap; }
.pg-tbl tbody td { padding:6px 10px; color:var(--ink); border-bottom:1px solid var(--line);
  white-space:nowrap; }
.pg-tbl tbody tr:last-child td { border-bottom:none; }
.pg-tbl tbody tr:hover td { background:var(--hover); }
.pg-h3 { font-family:'Share Tech Mono',monospace; font-size:19px; color:var(--head);
  letter-spacing:.03em; line-height:1.3; margin:0 0 6px; }
.pg-p { font-size:13.5px; color:var(--ink); line-height:1.6; margin-bottom:10px; }
div[data-testid="stDownloadButton"] button {
  background:var(--btn) !important; color:var(--btnink) !important; border-color:var(--line2) !important; }
"""
st.markdown(f"<style>{_VARS}" + CSS + "</style>", unsafe_allow_html=True)

st.markdown("""
<div class="pg-header">
  <div>
    <div class="pg-title">PyroGuard Micro-G</div>
    <div class="pg-sub">Autonomous Microgravity Fire Safety &amp; Combustion Analytics</div>
  </div>
  <div class="pg-tags">
    <span class="pg-tag">SAFFIRE I–VI</span><span class="pg-tag">BASS / ISS</span>
    <span class="pg-tag">EXPRESS RACK</span><span class="pg-tag pg-tag-live">ONBOARD AI · LOCAL</span>
  </div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="pg-side-h">🛰️ PyroGuard Micro-G</div>'
                '<div class="pg-side-s">Microgravity Combustion Telemetry &amp; AI Early Warning</div>',
                unsafe_allow_html=True)
    st.divider()
    _labels = {"auto": "Sistema", "light": "Claro", "dark": "Oscuro"}
    _pick = st.radio("Tema", list(_labels.values()), index=list(_labels).index(_PREF),
                     horizontal=True,
                     help="«Sistema» sigue la preferencia del sistema operativo. "
                          "La elección se guarda en la URL y se recuerda al recargar.")
    _new = next(k for k, v in _labels.items() if v == _pick)
    if _new != _PREF:
        st.query_params["theme"] = _new
        st.rerun()
    st.caption(f"Sistema: {'claro' if _sistema() == 'light' else 'oscuro'} · "
               f"aplicando: {'claro' if TEMA == 'light' else 'oscuro'}")
    st.divider()
    modo = st.radio("Modo de datos", ["Simulador Físico Micro-G",
                                      "Live ISS (NASA · Lightstreamer)",
                                      "Histórico NASA (PSI · Saffire)",
                                      "Subir Dataset Real (CSV NASA OSDR / Saffire)"])
    es_live = modo.startswith("Live")
    es_psi = modo.startswith("Histórico")
    es_csv = modo.startswith("Subir")
    up = None
    escenario, corte = ps.ESCENARIOS[0], 0
    atmosfera = list(ps.ATM)[0]
    ventana = (0, 599)
    if es_csv:
        up = st.file_uploader("CSV de telemetría", type=["csv"])
    elif not es_live and not es_psi:
        escenario = st.selectbox("Selector de escenario", ps.ESCENARIOS)
        corte = st.slider("Corte de ventilación (s) · 0 = sin intervención", 0, 550, 0, 5)

    if not es_live and not es_psi:
        st.divider()
        atmosfera = st.selectbox("Selector de atmósfera", list(ps.ATM))
        aea = "Artemis" in atmosfera
        st.caption("AEA 34.0 % O2 / 56.5 kPa · inflamabilidad más baja y ×1.65 en propagación y gases."
                   if aea else "ISS 20.9 % O2 / 101.3 kPa · referencia nominal de cabina.")
    st.divider()
    if es_live:
        st.info("🔗 Feed público NASA JSC → Lightstreamer (`ISSLIVE`). Sin credenciales. "
                "Solo se muestran como medidos los canales que el feed publica de verdad.")
    elif es_psi:
        st.info("📚 Datos históricos reales del repositorio **PSI** de la NASA "
                "(`psi.nasa.gov`), licencia CC0, sin credenciales. Son tablas del experimento "
                "Saffire, no telemetría de cabina.")
    elif es_csv:
        st.info("📂 Dataset externo: el mapeador normaliza columnas y el motor IA re-entrena su baseline "
                "con los primeros 60 s.")
    elif corte == 0:
        st.success("Sin intervención · la ventilación sostiene la convección forzada.")
    else:
        st.error(f"Corte en t={corte} s · airflow → 0 cm/s en ~30 s. Combustión limitada por difusión.")
    if not es_live:
        st.divider()
        ventana = st.slider("Ventana de análisis (s)", 0, 599, (0, 599), 5,
                            help="Limita el eje temporal de todas las gráficas.")
    st.caption("Motor determinista local · IsolationForest + MIRI · sin API keys")

def _tone(state: str) -> str:
    return {"streaming": GREEN, "connecting": YELLOW, "idle": T["dim2"]}.get(state, RED)


def _session_log(df_live: pd.DataFrame, sim, scenario: str, status) -> pd.DataFrame:
    """Log auditable en formato largo: cada fila declara su procedencia."""
    rows = []
    for col, (item, unit, _label) in iss_live.PUBLIC_SENSORS.items():
        if col not in df_live.columns:
            continue
        for _, r in df_live[df_live[col].notna()].iterrows():
            rows.append({"utc": r.get("utc", ""), "elapsed_s": r.get("t", ""),
                         "channel": col, "unit": unit, "value": round(float(r[col]), 4),
                         "source": "measured",
                         "detail": f"ISSLIVE {item} · sesión {status.session[:12] or '—'} · "
                                   f"estado {status.state}"})
    if sim is not None:
        spec = [("temp_c", "°C"), ("co_ppm", "ppm"), ("co2_ppm", "ppm"),
                ("hcn_ppm", "ppm"), ("smoke_obscuration_pct_m", "%/m"),
                ("radiative_heat_flux_kwm2", "kW/m²")]
        for _, r in sim.iterrows():
            for col, unit in spec:
                rows.append({"utc": "", "elapsed_s": int(r["timestamp_sec"]), "channel": col,
                             "unit": unit, "value": round(float(r[col]), 5),
                             "source": "inferred",
                             "detail": f"physics_simulator · {scenario} · sin hora de pared"})
    return pd.DataFrame(rows, columns=["utc", "elapsed_s", "channel", "unit", "value",
                                       "source", "detail"])


def _infer_panel(df_live: pd.DataFrame):
    """Canales ausentes estimados por modelo, siempre separados de lo medido."""
    esc = st.selectbox("Escenario para la inferencia", ps.ESCENARIOS, key="live_infer_esc")
    sim = ps.simular_escenario(ps.ESCENARIOS.index(esc), list(ps.ATM)[0], 0).copy()
    n = max(30, min(len(df_live) if len(df_live) else 60, len(sim)))
    sim = sim.iloc[:n].reset_index(drop=True)

    real_temp = None
    if not df_live.empty and "cabin_temp_c" in df_live.columns and df_live["cabin_temp_c"].notna().any():
        real_temp = float(df_live["cabin_temp_c"].dropna().iloc[-1])
        sim["temp_c"] = sim["temp_c"] + (real_temp - float(sim["temp_c"].iloc[-1]))

    anclaje = (f"La temperatura está anclada al último valor realmente medido ({real_temp:.2f} °C)."
               if real_temp is not None else
               "Sin datos reales disponibles: este panel es simulación pura, sin anclaje.")
    st.markdown(
        '<div class="pg-card" style="border-color:var(--yellow);background:var(--panel)">'
        '<div class="pg-kpi-label" style="color:var(--yellow)">Inferencia del modelo · no son mediciones</div>'
        '<div style="font-size:12.5px;line-height:1.7;margin-top:6px">'
        'CO, CO2, HCN, caudal de ventilación, humo y flujo radiativo los genera <b>physics_simulator</b>: '
        'describen el modelo, no la atmósfera real de la ISS. ' + anclaje +
        ' Los canales medidos del panel superior nunca se sustituyen.</div></div>',
        unsafe_allow_html=True)

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.11,
                        row_heights=[0.34, 0.36, 0.30],
                        specs=[[{}], [{"secondary_y": True}], [{"secondary_y": True}]],
                        subplot_titles=("TEMPERATURA · medido (feed NASA) vs inferido (modelo)",
                                        "INFERIDO · gases (modelo)",
                                        "INFERIDO · humo y flujo radiativo (modelo)"))
    if real_temp is not None and "cabin_temp_c" in df_live.columns:
        fig.add_trace(go.Scatter(x=df_live["t"], y=df_live["cabin_temp_c"], name="medido (°C)",
                                 mode="markers+lines", line=dict(color=GREEN, width=2),
                                 marker=dict(size=5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim.temp_c, name="temp inferida (°C)",
                             line=dict(color=YELLOW, width=1.6, dash="dash")), row=1, col=1)
    if real_temp is None:
        fig.add_annotation(text="sin muestras reales del feed", row=1, col=1, showarrow=False,
                           font=dict(size=10, color=T["dim"]), xref="x domain", yref="y domain",
                           x=0.5, y=0.06)
    for col, color, label in [("co_ppm", RED, "CO inferido (ppm)"),
                              ("hcn_ppm", VIOLET, "HCN inferido (ppm)")]:
        fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim[col], name=label,
                                 line=dict(color=color, width=1.6, dash="dash")), row=2, col=1)
    fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim.co2_ppm, name="CO2 inferido (ppm)",
                             line=dict(color=YELLOW, width=1.1, dash="dot")), row=2, col=1,
                  secondary_y=True)
    fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim.smoke_obscuration_pct_m,
                             name="humo inferido (%/m)",
                             line=dict(color=T["dim"], width=1.6, dash="dash")), row=3, col=1)
    fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim.radiative_heat_flux_kwm2,
                             name="flujo radiativo inferido (kW/m²)",
                             line=dict(color=ORANGE, width=1.6, dash="dash")), row=3, col=1,
                  secondary_y=True)
    fig.update_layout(**PLOT, height=560,
                      margin=dict(l=62, r=62, t=92, b=36), hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0, font=dict(size=9.5, color=T["ink"])),
                      font=dict(family="Consolas, monospace", size=10.5, color=T["ink"]))
    fig.update_xaxes(gridcolor=T["hair"], title_text="t (s)", row=3, col=1,
                     tickfont=dict(color=T["ink"]), title_font=dict(color=T["dim"]))
    fig.update_yaxes(gridcolor=T["hair"], tickfont=dict(color=T["ink"]),
                     title_font=dict(color=T["dim"]))
    fig.update_yaxes(title_text="CO2 ppm", row=2, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text="kW/m²", row=3, col=1, secondary_y=True, showgrid=False)
    st.plotly_chart(fig, config=PCFG, width="stretch")

    d = ae.detectar_anomalias(sim[ps.COLS])
    vent = ae.calcular_ventaja_deteccion(d)
    m1, m2, m3 = st.columns(3)
    m1.metric("MIRI (modelo)", f"{float(d['miri_score'].max()):.1f} %")
    m2.metric("Ventaja IA (modelo)",
              f"+{vent['ventaja_seg']} s" if vent["ventaja_seg"] is not None else "—")
    m3.metric("Anomalías (modelo)", f"{int(d['ia_alerta'].sum())} s")
    st.caption("Estas métricas se calculan sobre los canales inferidos: sirven para demostrar el motor, "
               "no para afirmar nada sobre el estado real de la ISS.")
    return sim, esc


DERIVED = {
    "o2_pct_from_pp": ("O2 derivado de ppO2", "%"),
    "co2_ppm_from_pp": ("CO2 derivado de ppCO2", "ppm"),
}

SHORT = {
    "cabin_temp_c": "Temp cabina", "cabin_pressure_mmhg": "Presión",
    "pp_o2_torr": "ppO2", "pp_co2_torr": "ppCO2", "pp_n2_torr": "ppN2",
    "avionics_fluid_c": "Fluido aviónica", "air_cooling_fluid_c": "Fluido aire",
    "coolant_lt_kg": "Refrig. LT", "coolant_mt_kg": "Refrig. MT",
    "urine_tank_pct": "Orina N3", "waste_water_pct": "Agua residual",
    "clean_water_pct": "Agua limpia",
}


def _var_meta(col: str) -> tuple[str, str]:
    if col in iss_live.PUBLIC_SENSORS:
        _, unit, label = iss_live.PUBLIC_SENSORS[col]
        return label, unit
    return DERIVED.get(col, (col, ""))


def _tbl(df: pd.DataFrame) -> None:
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row) + "</tr>"
                   for row in df.itertuples(index=False))
    st.markdown(f'<div class="pg-tblwrap"><table class="pg-tbl"><thead><tr>{head}</tr></thead>'
                f'<tbody>{body}</tbody></table></div>', unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def _shared_feed(channels: tuple, freq: float | None, snap: bool) -> "iss_live.LiveISS":
    """Una sesión TLCP por configuración: recargar no abre otra contra NASA."""
    return iss_live.LiveISS(channels=list(channels), max_frequency_hz=freq, snapshot=snap)


def render_live_mode() -> None:
    st.markdown("#### Live ISS Telemetry · NASA JSC → Lightstreamer")
    st.caption("Telemetría pública real del feed de la NASA. Solo se pinta lo que llega: cuando "
               "NASA corta la emisión los frames vienen nulos y la app lo declara, no rellena huecos.")

    with st.expander("Canales y opciones de prueba", expanded=True):
        pack = st.radio("Grupo de canales", [*iss_live.PACKS, "Todo"], horizontal=True,
                        help="Grupos del diccionario público del feed. «Todo» suscribe los 12 canales.")
        default = (list(iss_live.PUBLIC_SENSORS) if pack == "Todo"
                   else iss_live.PACKS.get(pack, iss_live.DEFAULT_CHANNELS))
        canales = st.multiselect(
            "Canales a suscribir", options=list(iss_live.PUBLIC_SENSORS), default=default,
            format_func=lambda c: iss_live.PUBLIC_SENSORS[c][2],
            help="Cada canal es un item del feed público. Cambiar la lista abre una sesión nueva.")
        c1, c2, c3 = st.columns([1.3, 1, 1.2])
        freq_lbl = c1.selectbox("Frecuencia máxima", ["Sin límite", "2 Hz", "1 Hz", "0.2 Hz"],
                                index=0, help="Throttle que se pide al servidor "
                                              "(LS_requested_max_frequency).")
        freq = {"Sin límite": None, "2 Hz": 2.0, "1 Hz": 1.0, "0.2 Hz": 0.2}[freq_lbl]
        snap = c2.toggle("Snapshot", value=True,
                         help="Pide el último valor conocido en el momento de suscribir.")
        probar = c3.button("🔎 Probar", width="stretch", disabled=not canales,
                           help="Abre una sesión temporal contra NASA y cuenta valores y nulos "
                                "por canal. No estima nada.")
        if probar:
            with st.spinner("Sondeando el feed durante 10 s…"):
                st.session_state["probe_res"] = iss_live.probe(canales, 10.0, freq, snap)

    if not canales:
        st.warning("Selecciona al menos un canal para abrir la sesión.")
        return

    key = (tuple(canales), freq, snap)
    prev_key = st.session_state.get("live_key")
    if prev_key is not None and prev_key != key:
        try:
            _shared_feed(*prev_key).stop()
        except Exception:  # noqa: BLE001
            pass
    st.session_state["live_key"] = key
    feed = _shared_feed(*key)

    res = st.session_state.get("probe_res")
    if res:
        head = (f"**Sondeo del feed**: {res['con_dato']} de {len(res['canales'])} canales devolvieron "
                f"números en {res['segundos']:.0f} s · estado `{res['estado']}`.")
        (st.success if res["con_dato"] else st.warning)(head)
        _tbl(pd.DataFrame(res["canales"]))
        if res["con_dato"]:
            st.caption("Hay emisión en este momento: esos canales son los que verás graficarse abajo.")
        else:
            st.caption("El servidor acepta la suscripción pero NASA no está publicando valores ahora "
                       "mismo (frames `#`). Reintenta más tarde o usa el simulador.")

    stt = feed.status
    live_now = stt.state in ("connecting", "streaming")
    b1, b2 = st.columns([1.6, 1.6])
    with b1:
        if st.button("Conectar feed", disabled=live_now, width="stretch"):
            feed.start()
            st.rerun()
    with b2:
        if st.button("Desconectar", disabled=not live_now, width="stretch"):
            feed.stop()
            st.rerun()

    @st.fragment(run_every=2.0 if live_now else None)
    def body() -> None:
        s = feed.status
        df_live = feed.frame()
        cov = feed.coverage()
        st.markdown(
            f'<div class="pg-chip" style="max-width:none;margin-bottom:8px">'
            f'<span class="pg-chip-l">Estado del enlace · sesión {html.escape(s.session[:12]) or "—"} · '
            f'última actualización {html.escape(s.last_update_utc or "—")}</span>'
            f'<span class="pg-chip-v" style="color:{_tone(s.state)}">{s.state.upper()}</span>'
            f'<span class="pg-chip-l" style="margin-top:4px">{html.escape(s.detail or "—")}</span></div>',
            unsafe_allow_html=True)

        chips = []
        for col in feed.channels:
            _, unit, _label = iss_live.PUBLIC_SENSORS[col]
            if not df_live.empty and col in df_live.columns and df_live[col].notna().any():
                val, tone = f"{df_live[col].dropna().iloc[-1]:.2f}", ""
            else:
                val, tone = "—", "pg-pre"
            chips.append((SHORT.get(col, col), val, unit, tone))
        chips += [("Muestras reales", f"{cov['samples']}", "", ""),
                  ("Actualizaciones", f"{s.updates}", "", "")]
        st.markdown(
            '<div class="pg-strip">' + "".join(
                f'<div class="pg-chip"><span class="pg-chip-l">{lab}</span>'
                f'<span class="pg-chip-v {tone}">{val}<i>{unit}</i></span></div>'
                for lab, val, unit, tone in chips) + "</div>", unsafe_allow_html=True)

        medidos = [c for c in df_live.columns
                   if c not in ("seq", "t", "clock", "utc") and df_live[c].notna().any()]
        if df_live.empty or not medidos:
            if s.state == "idle":
                st.info("Pulsa **Conectar feed** para abrir la sesión TLCP contra el servidor de NASA "
                        "y suscribir los canales elegidos.")
            elif s.state == "connecting":
                st.info("Abriendo sesión TLCP y suscribiendo canales…")
            else:
                st.warning("Enlace abierto y suscripción aceptada, pero NASA no está publicando valores "
                           "para estos canales (llegan frames nulos `#`). No se inventa ninguna cifra: "
                           "la pestaña queda a la espera y reintenta sola. Usa **Probar** para "
                           "confirmar qué devuelve el feed ahora mismo.")
        else:
            vc1, vc2 = st.columns([2, 1.2])
            var = vc1.selectbox("Variable a representar", medidos,
                                format_func=lambda c: _var_meta(c)[0], key="live_var")
            vc2.caption(f"{len(medidos)} de {cov['available']} canales suscritos con datos "
                        f"· {cov['samples']} muestras")
            label, unit = _var_meta(var)
            fig = go.Figure(go.Scatter(x=df_live.t, y=df_live[var], name=label,
                                       mode="lines+markers",
                                       line=dict(color=ORANGE, width=2), marker=dict(size=4)))
            fig.update_layout(**PLOT, height=320, margin=dict(l=64, r=40, t=46, b=38),
                              font=dict(family="Consolas, monospace", size=11, color=T["ink"]),
                              hovermode="x unified", showlegend=False,
                              title=dict(text=f"{label} ({unit})", x=0.01, xanchor="left",
                                         font=dict(size=12, color=T["dim"])))
            fig.update_xaxes(title_text="segundos desde la primera muestra", gridcolor=T["hair"],
                             tickfont=dict(color=T["ink"]), title_font=dict(color=T["dim"]))
            fig.update_yaxes(title_text=unit, gridcolor=T["hair"], tickfont=dict(color=T["ink"]),
                             title_font=dict(color=T["dim"]))
            st.plotly_chart(fig, config=PCFG, width="stretch")

        with st.expander("Diagnóstico por canal · qué llega y qué no", expanded=df_live.empty):
            _tbl(feed.diagnostics())
            st.caption("«Numeros» = frames con valor; «nulos» = frames `#`. Un canal con muchos nulos "
                       "y cero números está suscrito pero sin emisión.")
            if df_live.empty or not any(
                    df_live[c].notna().any() for c in df_live.columns
                    if c not in ("seq", "t", "clock", "utc")):
                st.caption("Ningún canal tiene datos todavía: el gráfico aparece en cuanto llegue el "
                           "primer valor numérico.")

        medidos_n = len(cov["measured"])
        st.markdown(
            '<div class="pg-card" style="margin-top:10px">'
            '<div class="pg-kpi-label">Cobertura · qué es real y qué no</div>'
            f'<div style="margin-top:8px;font-size:12.5px;line-height:1.7">'
            f'<b style="color:{GREEN}">Canales públicos suscritos:</b> {cov["available"]} '
            f'({medidos_n} con datos en esta sesión).<br>'
            f'<b style="color:{CYAN}">Derivados de lo medido:</b> O2 en % y CO2 en ppm, calculados desde '
            f'las presiones parciales y la presión de cabina (no son sensores directos).<br>'
            f'<b style="color:{RED}">Sin sensor público:</b> '
            + " · ".join(f"{n} ({u})" for n, u in iss_live.UNAVAILABLE) +
            '</div></div>', unsafe_allow_html=True)
        st.info("MIRI y el detector IsolationForest **no se calculan sobre datos reales**: necesitan CO, HCN, "
                "caudal de ventilación, humo y flujo radiativo, y ninguno existe en el feed público. "
                "Puntuarlos como si fueran mediciones sería inventar.")
        infer = st.toggle("Completar canales ausentes con el modelo físico (inferencia)",
                          key="live_infer",
                          help="Los canales que NASA no publica se estiman con physics_simulator y se "
                               "dibujan aparte, en trazo discontinuo, sin tocar los medidos.")
        if infer:
            st.divider()
            st.session_state["live_sim"] = _infer_panel(df_live)
        else:
            st.session_state["live_sim"] = None

        st.divider()
        st.markdown("#### Registro de sesión")
        sim_saved = st.session_state.get("live_sim")
        log = _session_log(df_live, sim_saved[0] if sim_saved else None,
                           sim_saved[1] if sim_saved else "", s)
        n_meas = int((log["source"] == "measured").sum())
        n_inf = int((log["source"] == "inferred").sum())
        lc1, lc2 = st.columns([2, 1])
        lc1.caption(f"{n_meas} muestras medidas · {n_inf} filas inferidas · columna `source` "
                    "(measured / inferred) y hora UTC en cada fila medida.")
        lc2.download_button(
            "⬇️ Exportar registro",
            log.to_csv(index=False).encode("utf-8"),
            file_name=f"pyroguard_live_{time.strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv", disabled=log.empty, width="stretch")

        if s.state == "error":
            st.error(f"Feed caído: {s.detail}. El cliente reintenta con backoff automático.")

    body()
    st.markdown('<div class="pg-note">FUENTE: NASA JSC VIA LIGHTSTREAMER · ISSLIVE · SOLO CANALES PÚBLICOS</div>',
                unsafe_allow_html=True)


@st.cache_data(show_spinner=False, ttl=3600)
def _psi_fetch(acc: str) -> dict:
    return nasa_psi.fetch(acc)


def render_psi_mode() -> None:
    st.markdown("#### Histórico NASA · PSI (Saffire)")
    st.caption("Tablas experimentales reales de las quemas en microgravedad de la NASA, "
               "descargadas de psi.nasa.gov (CC0) por su API pública, sin credenciales. El feed "
               "de la ISS es solo en vivo: esto es el registro del experimento, no telemetría de cabina.")

    acc = st.selectbox("Investigación", list(nasa_psi.INVESTIGATIONS),
                       format_func=lambda a: f"{nasa_psi.INVESTIGATIONS[a]['label']} · {a}")
    st.caption(f"Plataforma: {nasa_psi.INVESTIGATIONS[acc]['platform']} · descarga directa desde PSI")

    if st.button("⬇️ Descargar de psi.nasa.gov", width="stretch"):
        st.session_state["psi_req"] = acc
    if st.session_state.get("psi_req") != acc:
        st.info("Pulsa **Descargar** para traer la tabla oficial del experimento. Se cachea una "
                "hora, así que puedes volver a mirarla sin golpear otra vez el servidor de NASA.")
        return
    try:
        with st.spinner("Descargando metadatos y tabla desde PSI…"):
            res = _psi_fetch(acc)
    except Exception as exc:  # noqa: BLE001
        st.error(f"**No se pudo descargar {acc}**: {type(exc).__name__}: {exc}")
        st.caption("PSI ha tenido caídas puntuales este año. Reintenta en un minuto; mientras "
                   "tanto el simulador y el modo Live siguen funcionando.")
        return

    df = res["tabla"]
    sm = nasa_psi.resumen(df)
    chips = [("Muestras", f"{sm['muestras']}", "", "")]
    if "materiales" in sm:
        chips.append(("Materiales", f"{sm['materiales']}", "", ""))
    if "o2_rango" in sm:
        chips.append(("O2", sm["o2_rango"].split(" ")[0], "%", ""))
    if "flujo_rango" in sm:
        chips.append(("Flujo", sm["flujo_rango"].split(" ")[0], "cm/s", ""))
    chips.append(("Fichero", f"{res['bytes'] / 1024:.1f}", "kB", ""))
    st.markdown(
        '<div class="pg-strip">' + "".join(
            f'<div class="pg-chip"><span class="pg-chip-l">{lab}</span>'
            f'<span class="pg-chip-v">{val}<i>{unit}</i></span></div>'
            for lab, val, unit, tone in chips) + "</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="pg-card" style="margin-top:8px">'
        '<div class="pg-kpi-label">Procedencia · verificable fila a fila</div>'
        f'<div style="margin-top:8px;font-size:12.5px;line-height:1.85">'
        f'<b>{html.escape(res["titulo"])}</b><br>'
        f'DOI: <a href="https://doi.org/{html.escape(res["doi"])}" target="_blank">'
        f'{html.escape(res["doi"])}</a> · Licencia: {html.escape(res["licencia"])}<br>'
        f'Fichero: <code>{html.escape(res["file"])}</code> · {res["bytes"]:,} bytes · '
        f'SHA-256 <code>{res["sha256"][:16]}…</code><br>'
        f'Descargado {html.escape(res["descargado_utc"])} desde '
        f'<a href="{html.escape(res["url"])}" target="_blank">psi.nasa.gov</a>'
        '</div></div>', unsafe_allow_html=True)

    _tbl(df)
    st.caption("Las series temporales crudas de Saffire —imágenes y telemetría de los sensores— "
               "pesan entre 11 y 33 GB por experimento y no se descargan aquí: esta es la matriz "
               "experimental del vuelo.")
    st.info("Estos datos **no se puntúan con MIRI**: describen el experimento (material, flujo, "
            "%O2, tiempos de ignición y combustión), no la atmósfera de un rack de la ISS. La app "
            "los muestra como fuente real citada, no como entrada del modelo.")
    st.markdown('<div class="pg-note">FUENTE: NASA PSI · CC0 · DESCARGA DIRECTA SIN CREDENCIALES</div>',
                unsafe_allow_html=True)


if es_live:
    render_live_mode()
    st.stop()

if es_psi:
    render_psi_mode()
    st.stop()

MAX_MB, MAX_ROWS, MIN_ROWS = 25, 200_000, 12

up_rep = None
if up is not None:
    corte = 0
    if up.size > MAX_MB * 1024 * 1024:
        st.error(f"**Fichero rechazado**: {up.size / 1048576:.1f} MB supera el límite de {MAX_MB} MB.")
        st.stop()
    try:
        externo = pd.read_csv(up)
    except Exception as exc:
        st.error(f"**CSV ilegible** ({type(exc).__name__}): revisa el separador y la codificación.")
        st.stop()
    if externo.empty:
        st.error("**CSV vacío**: no contiene filas de telemetría.")
        st.stop()
    if len(externo) > MAX_ROWS:
        st.warning(f"Dataset recortado a las primeras {MAX_ROWS:,} filas de {len(externo):,}.")
        externo = externo.iloc[:MAX_ROWS]
    raw, up_rep = ae.mapear_dataset(externo)
else:
    raw = ps.simular_escenario(ps.ESCENARIOS.index(escenario), atmosfera, corte)

if up_rep is not None:
    mapped = set(up_rep["mapped"])
    if not up_rep["ok"]:
        st.error("**Dataset rechazado**: faltan canales mínimos para analizar. Se necesita temperatura "
                 "(`temp_c`, en °C o K) y al menos oxígeno o CO2 (en % o frase mol). No se calcula nada "
                 "para no producir un diagnóstico con datos inventados.")
        st.dataframe(pd.DataFrame(up_rep["channels"]), width="stretch", hide_index=True)
        st.caption(f"{up_rep['rows']} filas leídas · {len(mapped)} de 8 canales mapeados.")
        st.stop()
    faltan = [c for c in up_rep["missing"]]
    st.warning(f"**Informe de mapeo**: {len(mapped)} de 8 canales mapeados desde el fichero"
               + (f" · sin columna: {', '.join(faltan)} (se usan valores nominales declarados en el informe)"
                  if faltan else " · cobertura completa"))
    with st.expander("Ver informe de mapeo, unidades y validación"):
        st.dataframe(pd.DataFrame(up_rep["channels"]), width="stretch", hide_index=True)
        st.caption("Cada fila declara la columna de origen, el factor aplicado (detección de K/°F, "
                   "fracción/%/ppm, m/s, W/m²) y el estado: mapeado, rechazado por rango o nominal por defecto.")

if len(raw) < MIN_ROWS:
    st.error(f"**Dataset demasiado corto**: {len(raw)} muestras; el baseline necesita al menos {MIN_ROWS}.")
    st.stop()

df = ae.detectar_anomalias(raw)
bench = ae.calcular_ventaja_deteccion(df)
proto = ae.generar_protocolo_respuesta(df, atmosfera, corte)

nivel = proto["nivel_amenaza"]
cls = {"NOMINAL": "pg-nom", "PRE-IGNICIÓN": "pg-pre", "CRÍTICO": "pg-crit"}[nivel]
miri_max = float(df["miri_score"].max())
ventaja_txt = (f"+{bench['ventaja_seg']} s" if bench["ventaja_seg"] is not None
               else ("CIEGO" if bench["tradicional_seg"] is None and bench["pyroguard_seg"] is not None else "—"))

tone_ventaja = "pg-nom" if (bench["ventaja_seg"] or 0) > 0 else "pg-crit"
ring = {"NOMINAL": GREEN, "PRE-IGNICIÓN": YELLOW, "CRÍTICO": RED}[nivel]
pct = max(0.0, min(100.0, miri_max))
_c = 2 * 3.141592653589793 * 52
pulso = " pg-pulse" if nivel == "CRÍTICO" else ""
first = proto["acciones_inmediatas"][0].split(":")[0].split(". ", 1)[-1]
trad_txt = (f"{bench['tradicional_seg']} s" if bench["tradicional_seg"] is not None else "nunca")
st.markdown(
    f'<div class="pg-hero">'
    f'<div class="pg-ring">'
    f'<svg viewBox="0 0 120 120"><circle class="pg-ring-bg" cx="60" cy="60" r="52"/>'
    f'<circle class="pg-ring-fg" cx="60" cy="60" r="52" stroke="{ring}" '
    f'stroke-dasharray="{_c:.1f}" stroke-dashoffset="{_c * (1 - pct / 100):.1f}"/></svg>'
    f'<span class="pg-ring-v" style="color:{ring}">{pct:.0f}<span style="font-size:13px">%</span></span>'
    f'<span class="pg-ring-l">MIRI</span></div>'
    f'<div><div class="pg-hero-top">'
    f'<span class="pg-pill {cls}{pulso}">{nivel}</span>'
    f'<span class="pg-hero-sub">{proto["tipo_combustion"]}</span></div>'
    f'<div class="pg-hero-kpis">'
    f'<div><span>Ventaja IA</span><b class="{tone_ventaja}">{ventaja_txt}</b></div>'
    f'<div><span>Detector clásico</span><b>{trad_txt}</b></div>'
    f'<div><span>CO pico</span><b>{proto["co_ppm_pico"]:.0f}<span style="font-size:9px"> ppm</span></b></div>'
    f'<div><span>Radiación</span><b>{proto["radiative_peak_kwm2"]:.2f}<span style="font-size:9px"> kW/m²</span></b></div>'
    f'<div><span>HCN pico</span><b>{proto["hcn_ppm_pico"]:.1f}<span style="font-size:9px"> ppm</span></b></div>'
    f'</div><div class="pg-hero-cta">Siguiente acción: <b>{first}</b> · pasos completos en '
    f'<b>RESPUESTA</b></div></div></div>', unsafe_allow_html=True)

last = len(df) - 1
t_last = float(df["timestamp_sec"].iloc[-1])  # eje X real: puede no ser 0..n con CSV irregulares
v_hi = min(ventana[1], t_last)
v_lo = min(ventana[0], v_hi)
if v_hi <= v_lo:  # ventana pedida fuera del dataset: se mantiene un tramo visible
    v_lo, v_hi = max(0.0, v_hi - 1.0), v_hi
ventana_eff = (v_lo, v_hi)
if "t_cursor" not in st.session_state:
    st.session_state.t_cursor = 0
# Tras cambiar a un dataset más corto, el cursor guardado quedaría fuera del eje.
st.session_state.t_cursor = min(int(st.session_state.t_cursor), last)
if "play" not in st.session_state:
    st.session_state.play = False

q1, q2, q3, q4 = st.columns([1.1, 1.5, 1.5, 2.6])
if q1.button("⟲ Inicio", width="stretch", help="Llevar el cursor al segundo 0"):
    st.session_state.t_cursor = 0
if q2.button("⚑ Alerta IA", width="stretch", disabled=bench["pyroguard_seg"] is None,
             help="Saltar al segundo en que el modelo avisó por primera vez"):
    st.session_state.t_cursor = int(df.index[df.timestamp_sec == bench["pyroguard_seg"]][0])
if q3.button("⚠ Pico MIRI", width="stretch", help="Saltar al instante de MIRI máximo"):
    st.session_state.t_cursor = int(df.miri_score.idxmax())
with q4:
    st.toggle("Reproducir · 8×", key="play", help="Reproduce la telemetría en tiempo acelerado")


def _style(fig, t_now, h=360, rows=3):
    fig.update_layout(
        **PLOT,
        height=h, margin=dict(l=64, r=64, t=120, b=38), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.10, x=0, font=dict(size=9.5, color=T["ink"])),
        font=dict(family="Consolas, monospace", size=11, color=T["ink"]))
    fig.update_xaxes(gridcolor=T["hair"], range=[ventana_eff[0], ventana_eff[1]],
                     tickfont=dict(color=T["ink"]), title_font=dict(color=T["dim"]))
    fig.update_yaxes(gridcolor=T["hair"], tickfont=dict(color=T["ink"]),
                     title_font=dict(color=T["dim"]))
    if rows:
        fig.update_xaxes(title_text="t (s)", row=rows, col=1)
    if corte:
        for r in range(1, rows + 1):
            fig.add_vline(x=corte, line=dict(color=RED, width=1.4, dash="dash"), row=r, col=1)
    for r in range(1, rows + 1):
        fig.add_vline(x=int(t_now), line=dict(color=CYAN, width=1, dash="dot"), row=r, col=1)
    return fig


@st.fragment(run_every=0.7 if st.session_state.get("play") else None)
def live_panel():
    if st.session_state.get("play"):
        st.session_state.t_cursor = int((st.session_state.get("t_cursor", 0) + 8) % len(df))
    t_now = st.slider("Cursor temporal (s)", 0, len(df) - 1, step=1, key="t_cursor")

    live = df.iloc[int(t_now)]
    live_miri = float(live["miri_score"])
    live_cls = "pg-nom" if live_miri < 35 else ("pg-pre" if live_miri < 65 else "pg-crit")
    st.markdown(
        '<div class="pg-strip">'
        + "".join(
            f'<div class="pg-chip"><span class="pg-chip-l">{lab}</span>'
            f'<span class="pg-chip-v {tone}">{val}<i>{unit}</i></span></div>'
            for lab, val, unit, tone in [
                ("temp", f"{live['temp_c']:.2f}", "°C", ""),
                ("CO", f"{live['co_ppm']:.1f}", "ppm", "pg-crit" if live["co_ppm"] > 50 else ""),
                ("MIRI", f"{live_miri:.0f}", "%", live_cls),
                ("IA", "ALERTA" if bool(live["ia_alerta"]) else "estable", "", live_cls),
            ])
        + "</div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["ESTADO", "DETECCIÓN", "RESPUESTA"])

    with tab1:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.10,
                            row_heights=[0.46, 0.54],
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]],
                            subplot_titles=("Temperatura de rack vs ventilación (inercia térmica en 0g)",
                                            "Firma química: CO · HCN · CO2"))
        fig.add_trace(go.Scatter(x=df.timestamp_sec, y=df.temp_c, name="temp_c (°C)",
                                 line=dict(color=ORANGE, width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.timestamp_sec, y=df.airflow_cms, name="airflow (cm/s)",
                                 line=dict(color=CYAN, width=1.4, dash="dot")), row=1, col=1, secondary_y=True)
        fig.add_trace(go.Scatter(x=df.timestamp_sec, y=df.co_ppm, name="CO (ppm)",
                                 line=dict(color=RED, width=2)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.timestamp_sec, y=df.hcn_ppm, name="HCN (ppm)",
                                 line=dict(color=VIOLET, width=1.8)), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.timestamp_sec, y=df.co2_ppm, name="CO2 (ppm)",
                                 line=dict(color=YELLOW, width=1.2)), row=2, col=1, secondary_y=True)
        if bench["pyroguard_seg"] is not None:
            for r in range(1, 3):
                fig.add_vrect(x0=bench["pyroguard_seg"], x1=t_last, fillcolor="rgba(255,59,48,.06)",
                              line_width=0, layer="below", row=r, col=1)
        fig.update_yaxes(title_text="°C", row=1, col=1)
        fig.update_yaxes(title_text="cm/s", row=1, col=1, secondary_y=True, showgrid=False,
                         range=[0, max(24.0, float(df.airflow_cms.max()) * 1.2)])
        fig.update_yaxes(title_text="ppm", row=2, col=1)
        fig.update_yaxes(title_text="CO2 ppm", row=2, col=1, secondary_y=True, showgrid=False)
        st.plotly_chart(_style(fig, float(df.timestamp_sec.iloc[int(t_now)]), 470, rows=2),
                        config=PCFG, width="stretch")
        c = st.columns(3)
        c[0].metric("Radiación pico", f"{df.radiative_heat_flux_kwm2.max():.2f} kW/m²")
        c[1].metric("Humo pico", f"{df.smoke_obscuration_pct_m.max():.2f} %/m")
        c[2].metric("O2 mínimo", f"{df.o2_pct.min():.2f} %", f"nominal {ps.ATM[atmosfera]['o2']:.1f} %")
        st.caption("Zona sombreada = régimen posterior a la primera alerta IA · línea cian = cursor temporal. "
                   "Usa los botones de arriba o el deslizador para moverte por la telemetría.")

    with tab2:
        g1, g2 = st.columns([2, 1])
        with g1:
            fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                                 subplot_titles=("IsolationForest · anomaly_score (%)",
                                                 "MIRI — Microgravity Ignition Risk Index (%)"))
            fig2.add_trace(go.Scatter(x=df.timestamp_sec, y=df.anomaly_score, name="anomaly_score",
                                      line=dict(color=CYAN, width=1.8), fill="tozeroy",
                                      fillcolor="rgba(0,229,255,.10)"), row=1, col=1)
            al = df[df.ia_alerta]
            fig2.add_trace(go.Scatter(x=al.timestamp_sec, y=al.anomaly_score, mode="markers",
                                      name="ia_alerta", marker=dict(color=RED, size=5, symbol="x")),
                           row=1, col=1)
            fig2.add_trace(go.Scatter(x=df.timestamp_sec, y=df.miri_score, name="miri_score",
                                      line=dict(color=ORANGE, width=2.2)), row=2, col=1)
            fig2.add_trace(go.Scatter(x=df.timestamp_sec, y=np.full(len(df), 35.0), name="umbral 35%",
                                      line=dict(color=YELLOW, width=1, dash="dash")), row=2, col=1)
            if bench["pyroguard_seg"] is not None:
                fig2.add_vline(x=bench["pyroguard_seg"], line=dict(color=GREEN, dash="dot"))
            if bench["tradicional_seg"] is not None:
                fig2.add_vline(x=bench["tradicional_seg"], line=dict(color=RED, dash="dot"))
            st.plotly_chart(_style(fig2, float(df.timestamp_sec.iloc[int(t_now)]), 520, rows=2),
                            config=PCFG, width="stretch")
        with g2:
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=live_miri,
                number=dict(suffix=" %", font=dict(size=27, color=T["head"])),
                title=dict(text=f"MIRI @ t={int(t_now)} s", font=dict(size=11, color=T["dim2"])),
                gauge=dict(axis=dict(range=[0, 100], tickcolor=T["dim2"], tickfont=dict(size=9)),
                           bar=dict(color=ORANGE, thickness=0.30),
                           bgcolor=T["hair"], borderwidth=0,
                           steps=[dict(range=[0, 35], color="rgba(57,255,136,.30)"),
                                  dict(range=[35, 65], color="rgba(255,209,102,.30)"),
                                  dict(range=[65, 100], color="rgba(255,59,48,.35)")],
                           threshold=dict(line=dict(color=RED, width=3), value=65))))
            gauge.update_layout(template=T["template"], paper_bgcolor="rgba(0,0,0,0)", height=250,
                                margin=dict(l=18, r=18, t=34, b=8),
                                font=dict(family="Consolas, monospace", color=T["ink"]))
            st.plotly_chart(gauge, config={"displayModeBar": False}, width="stretch")
            trad_txt_b = (f"{bench['tradicional_seg']} s" if bench["tradicional_seg"] is not None
                          else "NUNCA")
            st.markdown(f"""
<div class="pg-card">
  <div class="pg-kpi-label">Benchmark de ventaja temporal</div>
  <div style="margin-top:8px;font-size:12.5px;line-height:1.9">
    PyroGuard AI: <b style="color:{GREEN}">{bench['pyroguard_seg'] if bench['pyroguard_seg'] is not None else '—'} s</b><br>
    Detector terrestre: <b style="color:{RED}">{trad_txt_b}</b><br>
    <b class="{'pg-nom' if (bench['ventaja_seg'] or 0) > 0 else 'pg-crit'}">{bench['veredicto']}</b>
  </div>
</div>""", unsafe_allow_html=True)
        st.caption("Modelo no supervisado entrenado en vuelo con los primeros 60 s: dCO/dt, dO2/dt, dCO2/dt, "
                   "CO/CO2, airflow y flujo radiativo normalizados.")

    with tab3:
        h1, h2 = st.columns([1.1, 1])
        with h1:
            st.markdown(f'<div class="pg-h3">Clasificación: <span class="{cls}">'
                        f'{proto["tipo_combustion"]}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pg-p">Nivel de amenaza: <span class="{cls}">{nivel}</span> · '
                        f'Tiempo crítico: '
                        f'{proto["tiempo_critico_seg"] if proto["tiempo_critico_seg"] is not None else "no proyectado"} s '
                        f'(IDLH CO 1200 ppm / HCN 50 ppm)</div>', unsafe_allow_html=True)
            st.markdown("#### Acciones inmediatas (Flight Rules)")
            for a in proto["acciones_inmediatas"]:
                st.markdown(f'<div class="pg-step">{a}</div>', unsafe_allow_html=True)
        with h2:
            st.markdown("#### Análisis químico")
            st.info(proto["analisis_quimico"])
            st.markdown("#### Explicación física")
            st.success(proto["explicacion_fisica"])
            st.markdown(f"**CO/CO2:** {proto['ratio_co_co2_pct']} % · **HCN pico:** {proto['hcn_ppm_pico']} ppm · "
                        f"**ΔT:** {proto['temp_peak_c'] - proto['temp_baseline_c']:+.2f} °C · "
                        f"**O2 mín:** {proto['o2_min_pct']} %")

    with tab1:
        with st.expander("Datos y exportación"):
            st.dataframe(df, width="stretch", height=340)
            st.download_button("⬇️ Descargar telemetría + IA (CSV)", df.to_csv(index=False).encode("utf-8"),
                               f"pyroguard_{nivel.lower()}.csv", "text/csv")
            st.caption(f"{len(df)} muestras · {len(df.columns)} columnas · anomaly_score, "
                       "ia_alerta y miri_score incluidos.")


live_panel()

st.markdown(f'<div class="pg-note">PYROGUARD MICRO-G · {len(df)} MUESTRAS · '
            f'{escenario.upper() if not modo.startswith("Subir") else "DATASET EXTERNO"} · '
            f'LOCAL DETERMINISTIC CORE</div>', unsafe_allow_html=True)
