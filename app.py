import html
import time

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import anomaly_engine as ae
import iss_live
import physics_simulator as ps

st.set_page_config(layout="wide", page_title="PyroGuard Micro-G | NASA Fire Safety", page_icon="🛰️")

RED, ORANGE, CYAN, GREEN, YELLOW, VIOLET = "#FF3B30", "#FF6B35", "#00E5FF", "#39FF88", "#FFD166", "#B47CFF"
PCFG = {"displaylogo": False,
        "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines",
                                   "hoverClosestCartesian", "hoverCompareCartesian"]}

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;800&display=swap');
.stApp { background: radial-gradient(circle at 18% -10%, #0d1b2a 0%, #060a10 55%, #04070b 100%); }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #C9D6E5; }
h1, h2, h3, h4 { font-family: 'Share Tech Mono', monospace !important; letter-spacing: .05em; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.pg-header { display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;
  border:1px solid rgba(0,229,255,.18); border-radius:12px; padding:14px 18px;
  background: linear-gradient(90deg, rgba(0,229,255,.07), rgba(6,10,16,.45) 58%, rgba(255,107,53,.06)); }
.pg-title { font-family:'Share Tech Mono',monospace; font-size:24px; color:#EAF4FF; letter-spacing:.04em; }
.pg-sub { color:#7FA0BF; font-size:10.5px; letter-spacing:.2em; text-transform:uppercase; margin-top:5px; }
.pg-tags { display:flex; gap:6px; flex-wrap:wrap; }
.pg-tag { border:1px solid rgba(0,229,255,.26); color:#8FD8E8; border-radius:4px; padding:2px 8px;
  font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.1em; }
.pg-tag-live { border-color:rgba(57,255,136,.4); color:#39FF88; }
div[data-testid="stWidgetLabel"] p { font-family:'Share Tech Mono',monospace; font-size:10px !important;
  letter-spacing:.13em; text-transform:uppercase; color:#6E8AA6 !important; }
.pg-card { border:1px solid rgba(128,170,210,.14); border-radius:10px; padding:11px 14px;
  background:rgba(10,18,28,.62); min-height:92px; display:flex; flex-direction:column; justify-content:space-between; }
.pg-kpi-label { font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.13em;
  color:#6E8AA6; text-transform:uppercase; }
.pg-kpi { font-family:'Share Tech Mono',monospace; font-size:21px; color:#EAF4FF; line-height:1.15;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.pg-kpi-sm { font-size:15px; }
.pg-nom { color:#39FF88; } .pg-pre { color:#FFD166; } .pg-crit { color:#FF3B30; }
.pg-strip { display:flex; gap:6px; flex-wrap:wrap; margin:2px 0 10px 0; }
.pg-chip { flex:1 1 92px; border:1px solid rgba(128,170,210,.14); border-radius:8px;
  padding:6px 9px; background:rgba(8,14,24,.72); }
.pg-chip-l { display:block; font-family:'Share Tech Mono',monospace; font-size:8.5px;
  letter-spacing:.12em; color:#5E7A96; text-transform:uppercase; }
.pg-chip-v { display:block; font-family:'Share Tech Mono',monospace; font-size:15px; color:#EAF4FF; }
.pg-chip-v i { font-style:normal; font-size:9.5px; color:#7FA0BF; margin-left:3px; }
.pg-step { border-left:2px solid #FF6B35; padding-left:11px; margin-bottom:8px;
  font-size:13px; color:#C9D6E5; line-height:1.45; }
.pg-note { font-family:'Share Tech Mono',monospace; font-size:9.5px; letter-spacing:.14em; color:#3E5A73;
  text-align:center; margin-top:16px; }
.pg-verdict { display:flex; gap:26px; align-items:center; flex-wrap:wrap; margin:2px 0 12px 0;
  border:1px solid rgba(128,170,210,.18); border-left:3px solid #00E5FF; border-radius:10px;
  padding:13px 18px; background:rgba(10,18,28,.66); }
.pg-verdict-m { display:flex; flex-direction:column; gap:3px; min-width:96px; }
.pg-verdict-v { font-family:'Share Tech Mono',monospace; font-size:23px; color:#EAF4FF; line-height:1.05; }
.pg-verdict-d { flex:1 1 240px; font-size:12px; color:#8FA9C2; line-height:1.55; }
div[data-testid="stSidebar"] { background:#070c13; border-right:1px solid rgba(0,229,255,.12); }
.pg-side-h { font-family:'Share Tech Mono',monospace; font-size:15px; color:#EAF4FF; letter-spacing:.04em; }
.pg-side-s { color:#6E8AA6; font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; margin-top:4px; }
.stTabs [data-baseweb="tab-list"] { gap:2px; border-bottom:1px solid rgba(128,170,210,.16); }
.stTabs [data-baseweb="tab"] { font-family:'Share Tech Mono',monospace; font-size:12px;
  letter-spacing:.1em; padding:8px 14px; }
.stTabs [aria-selected="true"] { color:#00E5FF !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:#00E5FF; }
div[data-testid="stMetricValue"] { font-family:'Share Tech Mono',monospace; color:#EAF4FF; font-size:19px; }
div[data-testid="stMetricLabel"] p { font-size:10px !important; letter-spacing:.1em; text-transform:uppercase; }
</style>
""", unsafe_allow_html=True)

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
    modo = st.radio("Modo de datos", ["Simulador Físico Micro-G",
                                      "Live ISS (NASA · Lightstreamer)",
                                      "Subir Dataset Real (CSV NASA OSDR / Saffire)"])
    es_live = modo.startswith("Live")
    es_csv = modo.startswith("Subir")
    up = None
    escenario, corte = ps.ESCENARIOS[0], 0
    atmosfera = list(ps.ATM)[0]
    ventana = (0, 599)
    if es_csv:
        up = st.file_uploader("CSV de telemetría", type=["csv"])
    elif not es_live:
        escenario = st.selectbox("Selector de escenario", ps.ESCENARIOS)
        corte = st.slider("Corte de ventilación (s) · 0 = sin intervención", 0, 550, 0, 5)

    if not es_live:
        st.divider()
        atmosfera = st.selectbox("Selector de atmósfera", list(ps.ATM))
        aea = "Artemis" in atmosfera
        st.caption("AEA 34.0 % O2 / 56.5 kPa · inflamabilidad más baja y ×1.65 en propagación y gases."
                   if aea else "ISS 20.9 % O2 / 101.3 kPa · referencia nominal de cabina.")
    st.divider()
    if es_live:
        st.info("🔗 Feed público NASA JSC → Lightstreamer (`ISSLIVE`). Sin credenciales. "
                "Solo se muestran como medidos los canales que el feed publica de verdad.")
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
    return {"streaming": GREEN, "connecting": YELLOW, "idle": "#6E8AA6"}.get(state, RED)


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
        '<div class="pg-card" style="border-color:rgba(255,209,102,.40);background:rgba(255,209,102,.05)">'
        '<div class="pg-kpi-label" style="color:#FFD166">Inferencia del modelo · no son mediciones</div>'
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
                           font=dict(size=10, color="#7FA0BF"), xref="x domain", yref="y domain",
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
                             line=dict(color="#9AA7B4", width=1.6, dash="dash")), row=3, col=1)
    fig.add_trace(go.Scatter(x=sim.timestamp_sec, y=sim.radiative_heat_flux_kwm2,
                             name="flujo radiativo inferido (kW/m²)",
                             line=dict(color=ORANGE, width=1.6, dash="dash")), row=3, col=1,
                  secondary_y=True)
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(8,14,24,.55)", height=560,
                      margin=dict(l=62, r=62, t=92, b=36), hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.08, x=0, font=dict(size=9.5)),
                      font=dict(family="Consolas, monospace", size=10.5, color="#C9D6E5"))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.05)", title_text="t (s)", row=3, col=1)
    fig.update_yaxes(gridcolor="rgba(255,255,255,.05)")
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


@st.cache_resource(show_spinner=False)
def _shared_feed() -> "iss_live.LiveISS":
    """Una sola sesión TLCP por servidor: recargar la página no abre otra contra NASA."""
    return iss_live.LiveISS()


def render_live_mode() -> None:
    feed = _shared_feed()
    stt = feed.status
    live_now = stt.state in ("connecting", "streaming")

    st.markdown("#### Live ISS Telemetry · NASA JSC → Lightstreamer")
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
        for col, (item, unit, label) in iss_live.PUBLIC_SENSORS.items():
            if not df_live.empty and col in df_live.columns and df_live[col].notna().any():
                val, faded = f"{df_live[col].dropna().iloc[-1]:.2f}", ""
            else:
                val, faded = "—", "pg-pre"
            chips.append((label.replace("Temperatura de cabina ", "Temp ").replace("Presión de cabina ", "Presión "),
                          val, unit, faded))
        chips += [("Muestras reales", f"{cov['samples']}", "", ""),
                  ("Actualizaciones", f"{s.updates}", "", "")]
        st.markdown(
            '<div class="pg-strip">' + "".join(
                f'<div class="pg-chip"><span class="pg-chip-l">{lab}</span>'
                f'<span class="pg-chip-v {tone}">{val}<i>{unit}</i></span></div>'
                for lab, val, unit, tone in chips) + "</div>", unsafe_allow_html=True)

        if df_live.empty:
            if s.state == "idle":
                st.info("Pulsa **Conectar feed** para abrir la sesión TLCP contra el servidor de NASA y "
                        "suscribir los canales de cabina del US Lab.")
            elif s.state == "connecting":
                st.info("Abriendo sesión TLCP y suscribiendo canales del US Lab…")
            else:
                st.warning("Enlace abierto y suscripción aceptada, pero NASA no está publicando valores para "
                           "estos canales (llegan frames nulos `#`). No se inventa ninguna cifra: la pestaña "
                           "queda a la espera y reintenta sola.")
        else:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            if "cabin_temp_c" in df_live.columns:
                fig.add_trace(go.Scatter(x=df_live.t, y=df_live.cabin_temp_c, name="temp_c (°C)",
                                         mode="lines+markers", line=dict(color=ORANGE, width=2)))
            if "cabin_pressure_mmhg" in df_live.columns:
                fig.add_trace(go.Scatter(x=df_live.t, y=df_live.cabin_pressure_mmhg,
                                         name="presión (mmHg)", mode="lines+markers",
                                         line=dict(color=CYAN, width=1.6)), secondary_y=True)
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(8,14,24,.55)", height=330,
                              margin=dict(l=60, r=60, t=60, b=36),
                              legend=dict(orientation="h", yanchor="bottom", y=1.06, x=0, font=dict(size=9.5)),
                              font=dict(family="Consolas, monospace", size=11, color="#C9D6E5"),
                              hovermode="x unified")
            fig.update_xaxes(title_text="segundos desde la primera muestra",
                             gridcolor="rgba(255,255,255,.05)")
            fig.update_yaxes(gridcolor="rgba(255,255,255,.05)")
            st.plotly_chart(fig, config=PCFG, width="stretch")

        st.markdown(
            '<div class="pg-card" style="margin-top:10px">'
            '<div class="pg-kpi-label">Cobertura de canales · qué es real y qué no</div>'
            f'<div style="margin-top:8px;font-size:12.5px;line-height:1.7">'
            f'<b style="color:{GREEN}">Medidos por el feed:</b> temperatura y presión de cabina del US Lab '
            f'({cov["available"]} de 8 canales del modelo).<br>'
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


if es_live:
    render_live_mode()
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
resumen = (f"{proto['tipo_combustion']} · CO pico {proto['co_ppm_pico']:.0f} ppm · "
           f"radiación {proto['radiative_peak_kwm2']:.2f} kW/m² · HCN {proto['hcn_ppm_pico']:.1f} ppm")
st.markdown(
    f'<div class="pg-verdict">'
    f'<div class="pg-verdict-m"><span class="pg-kpi-label">MIRI pico</span>'
    f'<span class="pg-verdict-v {cls}">{miri_max:.1f} %</span></div>'
    f'<div class="pg-verdict-m"><span class="pg-kpi-label">Nivel</span>'
    f'<span class="pg-verdict-v {cls}">{nivel}</span></div>'
    f'<div class="pg-verdict-m"><span class="pg-kpi-label">Ventaja IA</span>'
    f'<span class="pg-verdict-v {tone_ventaja}">{ventaja_txt}</span></div>'
    f'<div class="pg-verdict-d">{resumen}</div></div>', unsafe_allow_html=True)

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

pb, _ = st.columns([2, 6])
with pb:
    st.toggle("Playback · 8×", key="play", help="Reproduce la telemetría en tiempo acelerado")


def _style(fig, t_now, h=360, rows=3):
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(8,14,24,.55)",
        height=h, margin=dict(l=64, r=64, t=120, b=38), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.10, x=0, font=dict(size=9.5)),
        font=dict(family="Consolas, monospace", size=11, color="#C9D6E5"))
    fig.update_xaxes(gridcolor="rgba(255,255,255,.05)", range=[ventana_eff[0], ventana_eff[1]])
    fig.update_yaxes(gridcolor="rgba(255,255,255,.05)")
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
        st.caption("Zona sombreada = régimen posterior a la primera alerta IA · línea punteada cian = cursor temporal.")

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
                number=dict(suffix=" %", font=dict(size=27, color="#EAF4FF")),
                title=dict(text=f"MIRI @ t={int(t_now)} s", font=dict(size=11, color="#6E8AA6")),
                gauge=dict(axis=dict(range=[0, 100], tickcolor="#6E8AA6", tickfont=dict(size=9)),
                           bar=dict(color=ORANGE, thickness=0.30),
                           bgcolor="rgba(255,255,255,.04)", borderwidth=0,
                           steps=[dict(range=[0, 35], color="rgba(57,255,136,.30)"),
                                  dict(range=[35, 65], color="rgba(255,209,102,.30)"),
                                  dict(range=[65, 100], color="rgba(255,59,48,.35)")],
                           threshold=dict(line=dict(color=RED, width=3), value=65))))
            gauge.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=250,
                                margin=dict(l=18, r=18, t=34, b=8),
                                font=dict(family="Consolas, monospace", color="#C9D6E5"))
            st.plotly_chart(gauge, config={"displayModeBar": False}, width="stretch")
            st.markdown(f"""
<div class="pg-card">
  <div class="pg-kpi-label">Benchmark de ventaja temporal</div>
  <div style="margin-top:8px;font-size:12.5px;line-height:1.9">
    PyroGuard AI: <b style="color:{GREEN}">{bench['pyroguard_seg'] if bench['pyroguard_seg'] is not None else '—'} s</b><br>
    Detector terrestre: <b style="color:{RED}">{bench['tradicional_seg'] if bench['tradicional_seg'] is not None else 'NUNCA'} s</b><br>
    <b class="{'pg-nom' if (bench['ventaja_seg'] or 0) > 0 else 'pg-crit'}">{bench['veredicto']}</b>
  </div>
</div>""", unsafe_allow_html=True)
        st.caption("Modelo no supervisado entrenado en vuelo con los primeros 60 s: dCO/dt, dO2/dt, dCO2/dt, "
                   "CO/CO2, airflow y flujo radiativo normalizados.")

    with tab3:
        h1, h2 = st.columns([1.1, 1])
        with h1:
            st.markdown(f"### Clasificación: <span class='{cls}'>{proto['tipo_combustion']}</span>",
                        unsafe_allow_html=True)
            st.markdown(f"**Nivel de amenaza:** <span class='{cls}'>{nivel}</span> · **Tiempo crítico:** "
                        f"{proto['tiempo_critico_seg'] if proto['tiempo_critico_seg'] is not None else 'no proyectado'} s "
                        f"(IDLH CO 1200 ppm / HCN 50 ppm)", unsafe_allow_html=True)
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
