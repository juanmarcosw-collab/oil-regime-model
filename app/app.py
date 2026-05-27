"""
Streamlit app para explorar interactivamente el modelo estructural del precio del petróleo.

Permite mover sliders sobre los parámetros y ver en tiempo real cómo cambian las curvas
P_C(h), P_R(h) y P(h), junto con los valores notables del modelo.

Para correr desde la raíz del proyecto:
    streamlit run app/app.py

Requiere: streamlit, numpy, scipy, matplotlib.
"""

import io
from datetime import date, timedelta

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

# Importa el modelo
from model import (
    ModelParams, default_params,
    release_rate, P_classical, P_run, q_run, P_composite,
    theta_implicit, P_cap, P_floor
)


# --- Configuración de la página ---

st.set_page_config(
    page_title="Modelo estructural del petróleo",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Modelo estructural del precio del petróleo bajo stress de oferta")
st.caption("Explorador interactivo — calibración base mayo 2026")


# --- Sidebar: parámetros del modelo ---

st.sidebar.header("Parámetros del modelo")

st.sidebar.subheader("Estructurales")
P_star = st.sidebar.slider(
    "P* (USD/bbl, precio pre-shock)", 50.0, 100.0, 70.0, 1.0,
    help="Precio de referencia, equilibrio pre-guerra (Brent feb-2026)."
)
D_0 = st.sidebar.slider(
    "D₀ (mb/d, demanda pre-shock)", 95.0, 115.0, 104.0, 0.5,
    help="Demanda mundial pre-guerra al precio P*."
)
S_f0 = st.sidebar.slider(
    "S_f,0 (mb/d, oferta de flujo durante shock)", 80.0, 105.0, 95.0, 0.5,
    help="Producción mundial durante el shock, asumida constante."
)
eps_d = st.sidebar.slider(
    "ε_d (elasticidad de demanda)", 0.01, 0.30, 0.05, 0.01,
    help="Elasticidad short-run de demanda (default: 0,05; Caldara et al. 2019: 0,08-0,20)."
)
eps_s = st.sidebar.slider(
    "ε_s (elasticidad de oferta)", 0.01, 0.30, 0.05, 0.01,
    help="Elasticidad short-run de oferta (default: 0,05)."
)

st.sidebar.subheader("Función de release")
R_max = st.sidebar.slider(
    "R_max (mb/d, capacidad máxima IEA)", 1.0, 10.0, 6.0, 0.5,
    help="Capacidad técnica máxima de releases coordinados."
)
h_R = st.sidebar.slider(
    "h_R (saturación)", 0.05, 0.50, 0.12, 0.01,
    help="Parámetro de la función Michaelis-Menten del release."
)

st.sidebar.subheader("Régimen de run")
mu = st.sidebar.slider(
    "μ (fracción retenida por hoarders)", 0.0, 1.0, 0.5, 0.05,
    help="Intensidad del run: cuántos holders retienen al unísono."
)
delta_0 = st.sidebar.slider(
    "δ₀ (demanda especulativa adicional, mb/d)", 0.0, 10.0, 0.0, 0.5,
    help="Demanda extra de hoarders comprando inventario en el run."
)

st.sidebar.subheader("Global game (Goldstein-Pauzner)")
h_star = st.sidebar.slider(
    "h* (umbral del global game)", 0.05, 1.0, 0.30, 0.01,
    help="Umbral por debajo del cual el run se materializa con alta probabilidad."
)
sigma = st.sidebar.slider(
    "σ (dispersión de señales)", 0.02, 0.30, 0.08, 0.01,
    help="Cuán suave es la transición entre regímenes."
)

st.sidebar.subheader("Stock observado (IEA OMR)")

# Cargar serie histórica de stocks del master pipeline (best-effort)
_omr_dates: list = []
_omr_lookup: dict = {}
try:
    from model.data_loader import load_master_stocks
    _stocks_master = load_master_stocks()
    _omr_dates = [d.strftime("%Y-%m") for d in _stocks_master["date"]]
    _omr_lookup = dict(zip(_omr_dates, _stocks_master["stock_mb"].astype(float)))
except Exception as _exc:
    st.sidebar.warning(f"No pude cargar stocks IEA OMR: {_exc}")

if _omr_dates:
    _default_idx = len(_omr_dates) - 1  # último mes disponible
    chosen_omr_month = st.sidebar.selectbox(
        "Fecha OMR (mensual)", options=_omr_dates, index=_default_idx,
        help=(
            "Mes del OMR a usar. Stock se carga automáticamente desde "
            "`omr_total_global_inventories.csv` (IEA OMR mayo 2026 extraído)."
        ),
    )
    stock_from_omr = float(_omr_lookup[chosen_omr_month])
    st.sidebar.caption(f"Stock IEA OMR @ {chosen_omr_month}: **{stock_from_omr:,.0f} mb**")
    with st.sidebar.expander("Override manual del stock", expanded=False):
        stock_actual = st.slider(
            "Stock (mb)", 6500.0, 9000.0, stock_from_omr, 10.0,
            help="Por default precarga el valor del OMR; usalo para análisis hipotéticos."
        )
else:
    stock_actual = st.sidebar.slider(
        "Stock actual (mb)", 6500.0, 9000.0, 7951.0, 10.0,
        help="Total Global Observed Inventories. Fallback manual (master pipeline no disponible).",
    )

stock_stress = st.sidebar.slider(
    "Stress threshold (JPM, mb)", 6500.0, 9000.0, 7600.0, 10.0,
    help="Operational stress según JPMorgan. Por debajo, el run-risk se activa."
)
stock_floor = st.sidebar.slider(
    "Operational floor (JPM, mb)", 5000.0, 8000.0, 6800.0, 10.0,
    help="Mínimo operacional según JPMorgan. Mapea a h = 0."
)

st.sidebar.subheader("Demanda de reposición (Ormuz abierto)")
stock_opt = st.sidebar.slider(
    "Stock óptimo (mb)", 7500.0, 9000.0, 8200.0, 10.0,
    help=(
        "Nivel objetivo de inventarios post-acumulación. Default: 8.200 mb "
        "(enero 2026, pre-shock). Si Ormuz se reabre con stocks por debajo "
        "de este nivel, hay demanda extra para reponer."
    ),
)
R_repl_max = st.sidebar.slider(
    "R_repl_max (mb/d, saturación)", 0.0, 15.0, 5.0, 0.5,
    help=(
        "Saturación de la tasa de reposición cuando Stock = Stock_floor. "
        "Default 5 mb/d: en el stock actual (~7.951 mb) da ~0.9 mb/d, "
        "alineado con las estimaciones de mayo/junio. R_repl baja "
        "linealmente hasta cero al alcanzar Stock_opt."
    ),
)

st.sidebar.subheader("Observación de mercado")
P_observed = st.sidebar.slider(
    "P observado (USD/bbl)", 60.0, 200.0, 124.24, 0.5,
    help="Precio Brent observado al 30 de abril 2026."
)
theta_user = st.sidebar.slider(
    "θ (prob. de normalización futura)", 0.0, 1.0, 0.30, 0.01,
    help=(
        "Probabilidad que el mercado le asigna a que el shock se resuelva (Ormuz "
        "se reabra). Movelo hasta que el precio esperado calce con el observado: "
        "ese θ es lo que el mercado está priciendo implícitamente."
    ),
)


# --- Inferencia empírica (overlay θ en serie temporal) ---

st.sidebar.subheader("Inferencia empírica (θ histórico)")
inference_source = st.sidebar.selectbox(
    "Fuente de datos",
    ["Ninguna", "Master pipeline", "Sintética"],
    index=0,
    help=(
        "Master pipeline = CSVs sincronizados del proyecto padre (FRED daily + "
        "OMR mensual + Bloomberg forward curves). Sintética = datos generados "
        "para testing."
    ),
)
show_theta_overlay = st.sidebar.checkbox(
    "Mostrar θ implícito en Figura 2", value=False,
    disabled=(inference_source == "Ninguna"),
)
show_term_structure = st.sidebar.checkbox(
    "Mostrar term structure θ (forward curve)", value=False,
    disabled=(inference_source == "Ninguna"),
)


# --- Mapeo stock <-> h (lineal) ---

def h_from_stock(stock: float, stock_floor: float, stock_stress: float,
                 h_star: float) -> float:
    """Mapeo lineal: stock_floor -> h=0, stock_stress -> h=h_star."""
    if stock_stress <= stock_floor:
        return 0.0
    return max(0.0, h_star * (stock - stock_floor) / (stock_stress - stock_floor))


def stock_from_h(h: float, stock_floor: float, stock_stress: float,
                 h_star: float) -> float:
    """Inverso del mapeo."""
    return stock_floor + h * (stock_stress - stock_floor) / h_star


# --- Demanda de reposición (solo opera con Ormuz abierto) ---

def replenishment_rate(stock: float, stock_opt: float, stock_floor: float,
                       R_repl_max: float) -> float:
    """Tasa de reposición de inventarios cuando Ormuz está abierto.

    Lineal saturada:
        R_repl(Stock) = R_repl_max · clamp((Stock_opt - Stock) /
                                            (Stock_opt - Stock_floor), 0, 1)
    """
    if stock_opt <= stock_floor:
        return 0.0
    gap_norm = (stock_opt - stock) / (stock_opt - stock_floor)
    return R_repl_max * max(0.0, min(1.0, gap_norm))


def P_star_open(R_repl: float, params: ModelParams) -> float:
    """Precio de equilibrio con Ormuz abierto y demanda de reposición.

    Equilibrio: D(P) + R_repl = S_open(P), donde
        D(P)      = D_0 · (P/P*)^(-ε_d)
        S_open(P) = D_0 · (P/P*)^(ε_s)

    En R_repl = 0 da exactamente params.P_star.
    """
    if R_repl <= 0:
        return params.P_star

    def f(P):
        return (params.D_0 * (P / params.P_star) ** (-params.eps_d) + R_repl
                - params.D_0 * (P / params.P_star) ** params.eps_s)

    return brentq(f, 30, 2000)


# --- Cómputo: figura 1 (h, P) ---

params = ModelParams(
    P_star=P_star, D_0=D_0, S_f0=S_f0, eps_d=eps_d, eps_s=eps_s,
    R_max=R_max, h_R=h_R, mu=mu, delta_0=delta_0,
    h_star=h_star, sigma=sigma,
)

h_actual = h_from_stock(stock_actual, stock_floor, stock_stress, h_star)


# --- Carga de datos de inferencia (si fue seleccionada) ---

theta_overlay_df = None
forwards_df = None
cm_master_df = None  # constant-maturity para term structure
if inference_source != "Ninguna":
    try:
        from model.data_loader import (
            load_master, load_synthetic, constant_maturity_to_term_structure,
        )
        from model.inference import theta_series, theta_term_structure_from_forward

        if inference_source == "Master pipeline":
            _data = load_master()
            # Wrap constant_maturity para que el selector de fechas use sus snapshots
            cm_master_df = _data["constant_maturity"]
        elif inference_source == "Sintética":
            _data = load_synthetic()

        if show_theta_overlay and "brent_spot" in _data and "stocks" in _data:
            theta_overlay_df = theta_series(
                prices_df=_data["brent_spot"],
                stocks_df=_data["stocks"],
                stock_floor=stock_floor,
                stock_stress=stock_stress,
                params=params,
                shock_start="2026-02-12",
            )
        if show_term_structure:
            # Para master pipeline usamos constant_maturity (snapshots por día);
            # para sintética usamos el archivo de forward curves preparado.
            if inference_source == "Master pipeline" and cm_master_df is not None:
                # Marker para que el render más abajo sepa que es master
                forwards_df = "MASTER_CM"
            elif inference_source == "Sintética" and "forwards" in _data:
                forwards_df = _data["forwards"]
    except Exception as exc:
        st.sidebar.error(f"Error cargando datos: {exc}")


h_grid = np.linspace(0.001, 1.5, 600)
P_C_arr = np.array([P_classical(h, params) for h in h_grid])
P_R_arr = np.array([P_run(h, params) for h in h_grid])
q_arr = np.array([q_run(h, params) for h in h_grid])
P_arr = (1 - q_arr) * P_C_arr + q_arr * P_R_arr

# Stock(h) y P*(h) con demanda de reposición
stock_grid = np.array([stock_from_h(h, stock_floor, stock_stress, h_star)
                       for h in h_grid])
R_repl_arr = np.array([replenishment_rate(s, stock_opt, stock_floor, R_repl_max)
                       for s in stock_grid])
P_star_open_arr = np.array([P_star_open(r, params) for r in R_repl_arr])

P_expected_arr = (1 - theta_user) * P_arr + theta_user * P_star_open_arr

P_cap_val = P_cap(params)
P_floor_val = P_floor(params)
P_C_actual = P_classical(h_actual, params)
P_R_actual = P_run(h_actual, params)
q_actual = q_run(h_actual, params)
P_model_actual = (1 - q_actual) * P_C_actual + q_actual * P_R_actual

R_repl_actual = replenishment_rate(stock_actual, stock_opt, stock_floor, R_repl_max)
P_star_open_actual = P_star_open(R_repl_actual, params)
P_expected_actual = (1 - theta_user) * P_model_actual + theta_user * P_star_open_actual

# θ implícito ajustado por P*(h_actual) en vez de P* constante:
#     θ = (P_model - P_observed) / (P_model - P*(h))
_denom = P_model_actual - P_star_open_actual
theta = (P_model_actual - P_observed) / _denom if abs(_denom) > 1e-9 else 0.0


# --- Cómputo: figura 2 (tiempo, P) ---

t_obs_date = date(2026, 4, 30)
horizon_days = 365


def _rhs_stock(t, y, params, stock_floor, stock_stress, h_star):
    h = max(h_from_stock(y[0], stock_floor, stock_stress, h_star), 1e-4)
    return [-release_rate(h, params)]


sol = solve_ivp(
    _rhs_stock, [0, horizon_days], [stock_actual],
    args=(params, stock_floor, stock_stress, h_star),
    max_step=2.0, dense_output=True,
)

t_days = np.linspace(0, horizon_days, 366)
stock_t = sol.sol(t_days)[0]
h_t = np.array([h_from_stock(s, stock_floor, stock_stress, h_star) for s in stock_t])
h_t_safe = np.maximum(h_t, 1e-4)

P_C_t = np.array([P_classical(h, params) for h in h_t_safe])
P_R_t = np.array([P_run(h, params) for h in h_t_safe])
q_t = np.array([q_run(h, params) for h in h_t_safe])
P_t = (1 - q_t) * P_C_t + q_t * P_R_t

R_repl_t = np.array([replenishment_rate(s, stock_opt, stock_floor, R_repl_max)
                     for s in stock_t])
P_star_open_t = np.array([P_star_open(r, params) for r in R_repl_t])

P_expected_t = (1 - theta_user) * P_t + theta_user * P_star_open_t

dates_t = [t_obs_date + timedelta(days=int(d)) for d in t_days]


# --- Helpers: defaults de textos por figura ---

HP_DEFAULTS = dict(
    title="Modelo estructural en el plano (h, P)",
    xlabel=r"$h$ — buffer slack agregado",
    ylabel=r"$P$ — precio (USD/bbl)",
    legend_loc="upper right",
    xlim=(0.0, 1.5),
)

TP_DEFAULTS = dict(
    title="Proyección temporal: precio dado dStock/dt = −dot_R(h(Stock))",
    xlabel="Fecha",
    ylabel=r"$P$ — precio (USD/bbl)",
    legend_loc="lower right",
)

LEGEND_LOCS = [
    "best", "upper right", "upper left", "lower right", "lower left",
    "center right", "center left", "upper center", "lower center", "center",
]

LINESTYLE_LABELS = {
    "-": "Solid",
    "--": "Dashed",
    ":": "Dotted",
    "-.": "Dash-dot",
}
LINESTYLE_OPTIONS = list(LINESTYLE_LABELS.keys())

SERIES_DEFAULTS_HP = {
    "classical":  {"color": "#0F766E", "linestyle": "-",  "linewidth": 2.4,
                   "label": r"$P_C(h)$ — clásico"},
    "run":        {"color": "#C62828", "linestyle": "--", "linewidth": 2.4,
                   "label": r"$P_R(h)$ — run"},
    "composite":  {"color": "#000000", "linestyle": "-",  "linewidth": 3.0,
                   "label": r"$P(h)$ — composite"},
    "expected":   {"color": "#1E40AF", "linestyle": ":",  "linewidth": 2.2,
                   "label_fmt": r"$P_{{\rm esp}}(h)$ — esperado (θ={theta:.2f})"},
    "normalized": {"color": "#7C3AED", "linestyle": "-.", "linewidth": 2.0,
                   "label": r"$P^*$ — Ormuz abierto"},
}

SERIES_DEFAULTS_TP = {
    "classical":  {"color": "#0F766E", "linestyle": "-",  "linewidth": 2.4,
                   "label": r"$P_C(t)$ — clásico"},
    "run":        {"color": "#C62828", "linestyle": "--", "linewidth": 2.4,
                   "label": r"$P_R(t)$ — run"},
    "composite":  {"color": "#000000", "linestyle": "-",  "linewidth": 3.0,
                   "label": r"$P(t)$ — composite"},
    "expected":   {"color": "#1E40AF", "linestyle": ":",  "linewidth": 2.2,
                   "label_fmt": r"$P_{{\rm esp}}(t)$ — esperado (θ={theta:.2f})"},
    "normalized": {"color": "#7C3AED", "linestyle": "-.", "linewidth": 2.0,
                   "label": r"$P^*$ — Ormuz abierto"},
}

STOCK_DEFAULTS = dict(
    title="Evolución del stock observado",
    xlabel="Fecha",
    ylabel="Stock (millones de barriles)",
    legend_loc="lower left",
)

SERIES_DEFAULTS_STOCK = {
    "stock":  {"color": "#1F2937", "linestyle": "-",  "linewidth": 2.8,
               "label": "Stock observado"},
    "stress": {"color": "#DC2626", "linestyle": "--", "linewidth": 1.6,
               "label": "Stress threshold (JPM)"},
    "floor":  {"color": "#7F1D1D", "linestyle": "--", "linewidth": 1.6,
               "label": "Operational floor (JPM)"},
    "opt":    {"color": "#059669", "linestyle": ":",  "linewidth": 1.6,
               "label": "Stock óptimo"},
}

COLORS_DEFAULTS = {
    "facecolor": "#FFFFFF",
    "band_color": "#F57C00",
    "ref_line_color": "#94A3B8",
    "observed_color": "#1E40AF",
    "hstar_line_color": "#475569",
}

EXPORT_FORMATS = {
    "PNG (raster)":  {"ext": "png", "mime": "image/png"},
    "SVG (vectorial)": {"ext": "svg", "mime": "image/svg+xml"},
    "PDF (vectorial)": {"ext": "pdf", "mime": "application/pdf"},
}


# --- Funciones de figuras ---

def _merged(defaults: dict, overrides: dict | None) -> dict:
    """Deep merge superficial: overrides individuales reemplazan keys."""
    out = {k: dict(v) if isinstance(v, dict) else v for k, v in defaults.items()}
    if overrides:
        for k, v in overrides.items():
            if isinstance(v, dict) and k in out and isinstance(out[k], dict):
                out[k].update(v)
            else:
                out[k] = v
    return out


def make_hP_figure(
    figsize=(10, 6), dpi=110,
    show_classical=True, show_run=True, show_composite=True,
    show_expected=True, show_normalized=True, show_observed=True,
    show_band=True, show_reference_lines=True,
    xlim=None, ylim=None,
    title=None, xlabel=None, ylabel=None,
    title_fontsize=13, axis_label_fontsize=12,
    legend_fontsize=10, tick_fontsize=10,
    legend_loc=None,
    series_styles: dict | None = None,
    colors: dict | None = None,
):
    series = _merged(SERIES_DEFAULTS_HP, series_styles)
    palette = _merged(COLORS_DEFAULTS, colors)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi,
                           facecolor=palette["facecolor"])
    ax.set_facecolor(palette["facecolor"])

    if show_band:
        ax.axvspan(h_star - 2*sigma, h_star + 2*sigma, alpha=0.10,
                   color=palette["band_color"])
        ax.axvline(h_star, color=palette["hstar_line_color"],
                   linestyle=":", linewidth=1.2)

    if show_reference_lines:
        for y in (P_star, P_floor_val, P_cap_val):
            ax.axhline(y, color=palette["ref_line_color"],
                       linestyle=":", linewidth=1, alpha=0.6)

    def _plot(key, x, y):
        st_ = series[key]
        label = st_.get("label") or st_["label_fmt"].format(theta=theta_user)
        ax.plot(x, y, color=st_["color"], linestyle=st_["linestyle"],
                linewidth=st_["linewidth"], label=label)

    if show_classical:  _plot("classical", h_grid, P_C_arr)
    if show_run:        _plot("run", h_grid, P_R_arr)
    if show_composite:  _plot("composite", h_grid, P_arr)
    if show_expected:   _plot("expected", h_grid, P_expected_arr)
    if show_normalized: _plot("normalized", h_grid, P_star_open_arr)

    if show_observed:
        ax.scatter([h_actual], [P_observed], s=100,
                   color=palette["observed_color"], zorder=10,
                   edgecolor="white", linewidth=1.5, label="Observado")

    ax.set_xlim(xlim if xlim is not None else HP_DEFAULTS["xlim"])
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_xlabel(xlabel if xlabel is not None else HP_DEFAULTS["xlabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_ylabel(ylabel if ylabel is not None else HP_DEFAULTS["ylabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_title(title if title is not None else HP_DEFAULTS["title"],
                 fontsize=title_fontsize, fontweight="bold")
    ax.tick_params(axis="both", labelsize=tick_fontsize)

    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc=legend_loc or HP_DEFAULTS["legend_loc"],
                  fontsize=legend_fontsize, frameon=True, framealpha=0.6,
                  edgecolor="none")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig


def make_time_figure(
    figsize=(10, 6), dpi=110,
    show_classical=True, show_run=True, show_composite=True,
    show_expected=True, show_normalized=True, show_observed=True,
    show_reference_lines=True,
    xlim=None, ylim=None,
    title=None, xlabel=None, ylabel=None,
    title_fontsize=13, axis_label_fontsize=12,
    legend_fontsize=10, tick_fontsize=10,
    legend_loc=None,
    series_styles: dict | None = None,
    colors: dict | None = None,
    theta_overlay: "pd.DataFrame | None" = None,
):
    series = _merged(SERIES_DEFAULTS_TP, series_styles)
    palette = _merged(COLORS_DEFAULTS, colors)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi,
                           facecolor=palette["facecolor"])
    ax.set_facecolor(palette["facecolor"])

    if show_reference_lines:
        for y in (P_star, P_floor_val, P_cap_val):
            ax.axhline(y, color=palette["ref_line_color"],
                       linestyle=":", linewidth=1, alpha=0.6)

    def _plot(key, x, y):
        st_ = series[key]
        label = st_.get("label") or st_["label_fmt"].format(theta=theta_user)
        ax.plot(x, y, color=st_["color"], linestyle=st_["linestyle"],
                linewidth=st_["linewidth"], label=label)

    if show_classical:  _plot("classical", dates_t, P_C_t)
    if show_run:        _plot("run", dates_t, P_R_t)
    if show_composite:  _plot("composite", dates_t, P_t)
    if show_expected:   _plot("expected", dates_t, P_expected_t)
    if show_normalized: _plot("normalized", dates_t, P_star_open_t)

    if show_observed:
        ax.scatter([t_obs_date], [P_observed], s=100,
                   color=palette["observed_color"], zorder=10,
                   edgecolor="white", linewidth=1.5,
                   label=f"Observado {t_obs_date.strftime('%d-%b-%Y')}")

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    fig.autofmt_xdate(rotation=0, ha="center")

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_xlabel(xlabel if xlabel is not None else TP_DEFAULTS["xlabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_ylabel(ylabel if ylabel is not None else TP_DEFAULTS["ylabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_title(title if title is not None else TP_DEFAULTS["title"],
                 fontsize=title_fontsize, fontweight="bold")
    ax.tick_params(axis="both", labelsize=tick_fontsize)

    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc=legend_loc or TP_DEFAULTS["legend_loc"],
                  fontsize=legend_fontsize, frameon=True, framealpha=0.6,
                  edgecolor="none")
    ax.spines["top"].set_visible(False)
    # Si hay overlay, mantenemos el spine derecho para el eje gemelo
    if theta_overlay is None or len(theta_overlay) == 0:
        ax.spines["right"].set_visible(False)

    # --- Overlay θ implícito en eje derecho ---
    if theta_overlay is not None and len(theta_overlay) > 0:
        ax2 = ax.twinx()
        ax2.plot(
            theta_overlay["date"], theta_overlay["theta"],
            color="#5e35b1", linewidth=1.6, linestyle="-",
            alpha=0.85, label="θ implícito",
        )
        ax2.axhline(0, color="#5e35b1", linewidth=0.5, linestyle=":", alpha=0.4)
        ax2.axhline(1, color="#5e35b1", linewidth=0.5, linestyle=":", alpha=0.4)
        ax2.set_ylabel("θ implícito", fontsize=axis_label_fontsize,
                       fontweight="bold", color="#5e35b1")
        ax2.tick_params(axis="y", labelsize=tick_fontsize, colors="#5e35b1")
        # Rango automático con padding
        ymin, ymax = theta_overlay["theta"].min(), theta_overlay["theta"].max()
        pad = max(0.1, (ymax - ymin) * 0.1)
        ax2.set_ylim(min(-0.05, ymin - pad), max(1.05, ymax + pad))
        ax2.spines["top"].set_visible(False)

    fig.tight_layout()
    return fig


def make_term_structure_figure(
    forwards_df, snapshot_date: str,
    stock_at_snapshot: float, stock_floor_v: float, stock_stress_v: float,
    params_obj, figsize=(10, 5), dpi=110,
):
    """Term structure de θ implícito desde forward curve a snapshot_date."""
    from model.inference import theta_term_structure_from_forward

    ts = theta_term_structure_from_forward(
        forward_df=forwards_df,
        snapshot_date=snapshot_date,
        stock_at_snapshot=stock_at_snapshot,
        stock_floor=stock_floor_v,
        stock_stress=stock_stress_v,
        params=params_obj,
    )

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, facecolor="white")
    ax.plot(ts["maturity_month"], ts["theta"],
            marker="o", color="#5e35b1", linewidth=1.8)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle=":")
    ax.axhline(1, color="gray", linewidth=0.5, linestyle=":")
    ax.fill_between(ts["maturity_month"], 0, ts["theta"],
                    color="#5e35b1", alpha=0.1)
    ax.set_xlabel("Maturity (meses)", fontsize=12, fontweight="bold")
    ax.set_ylabel("θ implícito", fontsize=12, fontweight="bold")
    ax.set_title(
        f"Term structure de θ implícito — forward curve al {snapshot_date}",
        fontsize=13, fontweight="bold",
    )
    ax.set_xticks(ts["maturity_month"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)
    fig.tight_layout()
    return fig, ts


def make_stock_figure(
    figsize=(10, 5), dpi=110,
    show_stock=True, show_stress=True, show_floor=True, show_opt=True,
    show_observed=True,
    xlim=None, ylim=None,
    title=None, xlabel=None, ylabel=None,
    title_fontsize=13, axis_label_fontsize=12,
    legend_fontsize=10, tick_fontsize=10,
    legend_loc=None,
    series_styles: dict | None = None,
    colors: dict | None = None,
):
    series = _merged(SERIES_DEFAULTS_STOCK, series_styles)
    palette = _merged(COLORS_DEFAULTS, colors)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi,
                           facecolor=palette["facecolor"])
    ax.set_facecolor(palette["facecolor"])

    if show_stock:
        st_ = series["stock"]
        ax.plot(dates_t, stock_t, color=st_["color"], linestyle=st_["linestyle"],
                linewidth=st_["linewidth"], label=st_["label"])

    for key, val, show in [("stress", stock_stress, show_stress),
                            ("floor",  stock_floor,  show_floor),
                            ("opt",    stock_opt,    show_opt)]:
        if show:
            st_ = series[key]
            ax.axhline(val, color=st_["color"], linestyle=st_["linestyle"],
                       linewidth=st_["linewidth"], label=st_["label"])

    if show_observed:
        ax.scatter([t_obs_date], [stock_actual], s=100,
                   color=palette["observed_color"], zorder=10,
                   edgecolor="white", linewidth=1.5,
                   label=f"Observado {t_obs_date.strftime('%d-%b-%Y')}")

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    fig.autofmt_xdate(rotation=0, ha="center")

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    ax.set_xlabel(xlabel if xlabel is not None else STOCK_DEFAULTS["xlabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_ylabel(ylabel if ylabel is not None else STOCK_DEFAULTS["ylabel"],
                  fontsize=axis_label_fontsize, fontweight="bold")
    ax.set_title(title if title is not None else STOCK_DEFAULTS["title"],
                 fontsize=title_fontsize, fontweight="bold")
    ax.tick_params(axis="both", labelsize=tick_fontsize)

    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc=legend_loc or STOCK_DEFAULTS["legend_loc"],
                  fontsize=legend_fontsize, frameon=True, framealpha=0.6,
                  edgecolor="none")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig


def small_metric(label: str, value: str, delta: str | None = None):
    """Versión compacta de st.metric con fuente más chica."""
    delta_html = (
        f"<span style='color:#888;font-size:0.85em;margin-left:0.4em'>{delta}</span>"
        if delta else ""
    )
    st.markdown(
        f"<div style='margin-bottom:0.6em'>"
        f"<div style='font-size:0.78em;color:#666'>{label}</div>"
        f"<div style='font-size:1.05em;font-weight:600'>{value}{delta_html}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def customize_and_export(
    fig_factory,
    defaults: dict,
    series_defaults: dict,
    key_prefix: str,
    filename_base: str,
    has_band: bool = False,
    xlim_kind: str = "numeric",  # "numeric" (h, P) o "none" (fechas)
    default_ylim: tuple = (0.0, 250.0),
):
    """Renderiza tabs de personalización + preview + descarga (PNG/SVG/PDF)."""
    with st.expander("Personalizar y exportar (para presentación)"):
        tab_el, tab_st, tab_ax, tab_tx, tab_dl = st.tabs(
            ["Elementos", "Estilo", "Ejes", "Textos", "Tamaño y descarga"]
        )

        with tab_el:
            cA, cB = st.columns(2)
            with cA:
                show_classical = st.checkbox("P clásico", True, key=f"{key_prefix}_c")
                show_run = st.checkbox("P run", True, key=f"{key_prefix}_r")
                show_composite = st.checkbox("P composite", True, key=f"{key_prefix}_cm")
                show_expected = st.checkbox("P esperado", True, key=f"{key_prefix}_e")
                show_normalized = st.checkbox(
                    "P* (Ormuz abierto)", True, key=f"{key_prefix}_n",
                    help="Precio de equilibrio si el shock se resuelve. "
                         "Sube cuando el stock está por debajo del óptimo "
                         "por la demanda de reposición.",
                )
            with cB:
                show_observed = st.checkbox("Punto observado", True, key=f"{key_prefix}_o")
                show_reference_lines = st.checkbox(
                    "Líneas de referencia (P*, cap, piso)", True,
                    key=f"{key_prefix}_ref",
                )
                if has_band:
                    show_band = st.checkbox(
                        "Banda de fragilidad y línea h*", True,
                        key=f"{key_prefix}_b",
                    )
                else:
                    show_band = False

        with tab_st:
            st.caption("Colores generales:")
            cg1, cg2 = st.columns(2)
            facecolor = cg1.color_picker(
                "Fondo", COLORS_DEFAULTS["facecolor"], key=f"{key_prefix}_fc",
            )
            ref_color = cg2.color_picker(
                "Líneas de referencia", COLORS_DEFAULTS["ref_line_color"],
                key=f"{key_prefix}_refc",
            )
            cg3, cg4 = st.columns(2)
            observed_color = cg3.color_picker(
                "Punto observado", COLORS_DEFAULTS["observed_color"],
                key=f"{key_prefix}_oc",
            )
            if has_band:
                band_color = cg4.color_picker(
                    "Banda de fragilidad", COLORS_DEFAULTS["band_color"],
                    key=f"{key_prefix}_bc",
                )
            else:
                band_color = COLORS_DEFAULTS["band_color"]

            st.caption("Por serie (color y estilo de línea):")
            series_overrides = {}
            series_labels = [
                ("classical", "P clásico"),
                ("run", "P run"),
                ("composite", "P composite"),
                ("expected", "P esperado"),
                ("normalized", "P* (Ormuz abierto)"),
            ]
            for s_key, s_label in series_labels:
                cs1, cs2, cs3 = st.columns([1.4, 1, 1])
                cs1.markdown(f"<div style='padding-top:0.55em'>{s_label}</div>",
                             unsafe_allow_html=True)
                s_color = cs2.color_picker(
                    f"Color {s_label}", series_defaults[s_key]["color"],
                    key=f"{key_prefix}_{s_key}_col",
                    label_visibility="collapsed",
                )
                s_ls_idx = LINESTYLE_OPTIONS.index(
                    series_defaults[s_key]["linestyle"]
                ) if series_defaults[s_key]["linestyle"] in LINESTYLE_OPTIONS else 0
                s_ls = cs3.selectbox(
                    f"Estilo {s_label}", LINESTYLE_OPTIONS, index=s_ls_idx,
                    format_func=lambda x: LINESTYLE_LABELS[x],
                    key=f"{key_prefix}_{s_key}_ls",
                    label_visibility="collapsed",
                )
                series_overrides[s_key] = {"color": s_color, "linestyle": s_ls}

            colors_overrides = {
                "facecolor": facecolor,
                "ref_line_color": ref_color,
                "observed_color": observed_color,
                "band_color": band_color,
            }

        with tab_ax:
            if xlim_kind == "numeric":
                cx1, cx2 = st.columns(2)
                xmin = cx1.number_input(
                    "X min", value=float(defaults["xlim"][0]), step=0.1,
                    key=f"{key_prefix}_xmin",
                )
                xmax = cx2.number_input(
                    "X max", value=float(defaults["xlim"][1]), step=0.1,
                    key=f"{key_prefix}_xmax",
                )
                xlim = (xmin, xmax)
            else:
                xlim = None
                st.caption("Los ticks del eje X son fechas; se muestran automáticamente.")

            use_ylim = st.checkbox(
                "Fijar manualmente el rango Y", False, key=f"{key_prefix}_uy",
            )
            if use_ylim:
                cy1, cy2 = st.columns(2)
                ymin = cy1.number_input(
                    "Y min", value=float(default_ylim[0]), step=5.0,
                    key=f"{key_prefix}_ymin",
                )
                ymax = cy2.number_input(
                    "Y max", value=float(default_ylim[1]), step=5.0,
                    key=f"{key_prefix}_ymax",
                )
                ylim = (ymin, ymax)
            else:
                ylim = None

        with tab_tx:
            title = st.text_input(
                "Título", defaults["title"], key=f"{key_prefix}_t",
            )
            xlabel = st.text_input(
                "Etiqueta eje X", defaults["xlabel"], key=f"{key_prefix}_xl",
            )
            ylabel = st.text_input(
                "Etiqueta eje Y", defaults["ylabel"], key=f"{key_prefix}_yl",
            )
            loc_idx = (LEGEND_LOCS.index(defaults["legend_loc"])
                       if defaults["legend_loc"] in LEGEND_LOCS else 0)
            legend_loc = st.selectbox(
                "Posición de la leyenda", LEGEND_LOCS, index=loc_idx,
                key=f"{key_prefix}_ll",
            )
            st.caption("Tamaños de fuente:")
            cf1, cf2 = st.columns(2)
            title_fs = cf1.number_input(
                "Título", 8, 30, 13, 1, key=f"{key_prefix}_tfs",
            )
            axis_fs = cf2.number_input(
                "Etiquetas ejes", 6, 24, 12, 1, key=f"{key_prefix}_afs",
            )
            cf3, cf4 = st.columns(2)
            legend_fs = cf3.number_input(
                "Leyenda", 6, 20, 10, 1, key=f"{key_prefix}_lfs",
            )
            tick_fs = cf4.number_input(
                "Ticks", 6, 18, 10, 1, key=f"{key_prefix}_tkfs",
            )

        with tab_dl:
            cd1, cd2, cd3 = st.columns(3)
            w = cd1.number_input(
                "Ancho (in)", 4.0, 20.0, 10.0, 0.5, key=f"{key_prefix}_w",
            )
            h_in = cd2.number_input(
                "Alto (in)", 3.0, 15.0, 6.0, 0.5, key=f"{key_prefix}_h",
            )
            dpi = cd3.number_input(
                "DPI (solo PNG)", 72, 600, 200, 10, key=f"{key_prefix}_dpi",
            )
            fmt_label = st.selectbox(
                "Formato", list(EXPORT_FORMATS.keys()), index=0,
                key=f"{key_prefix}_fmt",
                help="PNG es raster (ideal para web). SVG/PDF son vectoriales "
                     "(escalables sin pérdida; mejor para imprimir o "
                     "presentaciones de alta calidad).",
            )

        # Build figure
        kwargs = dict(
            figsize=(w, h_in), dpi=int(dpi),
            show_classical=show_classical, show_run=show_run,
            show_composite=show_composite, show_expected=show_expected,
            show_normalized=show_normalized,
            show_observed=show_observed,
            show_reference_lines=show_reference_lines,
            xlim=xlim, ylim=ylim,
            title=title, xlabel=xlabel, ylabel=ylabel,
            title_fontsize=int(title_fs), axis_label_fontsize=int(axis_fs),
            legend_fontsize=int(legend_fs), tick_fontsize=int(tick_fs),
            legend_loc=legend_loc,
            series_styles=series_overrides,
            colors=colors_overrides,
        )
        if has_band:
            kwargs["show_band"] = show_band

        st.markdown("**Preview de la figura a exportar:**")
        custom_fig = fig_factory(**kwargs)
        st.pyplot(custom_fig, use_container_width=True)

        fmt = EXPORT_FORMATS[fmt_label]
        buf = io.BytesIO()
        save_kwargs = dict(format=fmt["ext"], bbox_inches="tight",
                           facecolor=custom_fig.get_facecolor())
        custom_fig.savefig(buf, **save_kwargs)
        plt.close(custom_fig)
        st.download_button(
            f"Descargar {fmt['ext'].upper()}", data=buf.getvalue(),
            file_name=f"{filename_base}.{fmt['ext']}", mime=fmt["mime"],
            key=f"{key_prefix}_dl",
        )


def customize_and_export_stock(
    fig_factory,
    key_prefix: str,
    filename_base: str,
    default_ylim: tuple = (6500.0, 8500.0),
):
    """Panel de personalización + export para la figura de stock."""
    with st.expander("Personalizar y exportar (para presentación)"):
        tab_el, tab_st, tab_ax, tab_tx, tab_dl = st.tabs(
            ["Elementos", "Estilo", "Ejes", "Textos", "Tamaño y descarga"]
        )

        with tab_el:
            cA, cB = st.columns(2)
            with cA:
                show_stock = st.checkbox("Stock (línea principal)", True,
                                         key=f"{key_prefix}_s")
                show_observed = st.checkbox("Punto observado", True,
                                            key=f"{key_prefix}_o")
            with cB:
                show_stress = st.checkbox("Stress threshold", True,
                                          key=f"{key_prefix}_str")
                show_floor = st.checkbox("Operational floor", True,
                                         key=f"{key_prefix}_fl")
                show_opt = st.checkbox("Stock óptimo", True,
                                       key=f"{key_prefix}_op")

        with tab_st:
            st.caption("Colores generales:")
            cg1, cg2 = st.columns(2)
            facecolor = cg1.color_picker(
                "Fondo", COLORS_DEFAULTS["facecolor"], key=f"{key_prefix}_fc",
            )
            observed_color = cg2.color_picker(
                "Punto observado", COLORS_DEFAULTS["observed_color"],
                key=f"{key_prefix}_oc",
            )

            st.caption("Por serie (color y estilo de línea):")
            series_overrides = {}
            series_labels = [
                ("stock",  "Stock"),
                ("stress", "Stress threshold"),
                ("floor",  "Operational floor"),
                ("opt",    "Stock óptimo"),
            ]
            for s_key, s_label in series_labels:
                cs1, cs2, cs3 = st.columns([1.4, 1, 1])
                cs1.markdown(f"<div style='padding-top:0.55em'>{s_label}</div>",
                             unsafe_allow_html=True)
                s_color = cs2.color_picker(
                    f"Color {s_label}",
                    SERIES_DEFAULTS_STOCK[s_key]["color"],
                    key=f"{key_prefix}_{s_key}_col",
                    label_visibility="collapsed",
                )
                s_ls_idx = LINESTYLE_OPTIONS.index(
                    SERIES_DEFAULTS_STOCK[s_key]["linestyle"]
                ) if SERIES_DEFAULTS_STOCK[s_key]["linestyle"] in LINESTYLE_OPTIONS else 0
                s_ls = cs3.selectbox(
                    f"Estilo {s_label}", LINESTYLE_OPTIONS, index=s_ls_idx,
                    format_func=lambda x: LINESTYLE_LABELS[x],
                    key=f"{key_prefix}_{s_key}_ls",
                    label_visibility="collapsed",
                )
                series_overrides[s_key] = {"color": s_color, "linestyle": s_ls}

            colors_overrides = {
                "facecolor": facecolor,
                "observed_color": observed_color,
            }

        with tab_ax:
            st.caption("El eje X son fechas; los ticks se muestran automáticamente.")
            use_ylim = st.checkbox(
                "Fijar manualmente el rango Y", False, key=f"{key_prefix}_uy",
            )
            if use_ylim:
                cy1, cy2 = st.columns(2)
                ymin = cy1.number_input(
                    "Y min", value=float(default_ylim[0]), step=50.0,
                    key=f"{key_prefix}_ymin",
                )
                ymax = cy2.number_input(
                    "Y max", value=float(default_ylim[1]), step=50.0,
                    key=f"{key_prefix}_ymax",
                )
                ylim = (ymin, ymax)
            else:
                ylim = None

        with tab_tx:
            title = st.text_input(
                "Título", STOCK_DEFAULTS["title"], key=f"{key_prefix}_t",
            )
            xlabel = st.text_input(
                "Etiqueta eje X", STOCK_DEFAULTS["xlabel"], key=f"{key_prefix}_xl",
            )
            ylabel = st.text_input(
                "Etiqueta eje Y", STOCK_DEFAULTS["ylabel"], key=f"{key_prefix}_yl",
            )
            loc_idx = (LEGEND_LOCS.index(STOCK_DEFAULTS["legend_loc"])
                       if STOCK_DEFAULTS["legend_loc"] in LEGEND_LOCS else 0)
            legend_loc = st.selectbox(
                "Posición de la leyenda", LEGEND_LOCS, index=loc_idx,
                key=f"{key_prefix}_ll",
            )
            st.caption("Tamaños de fuente:")
            cf1, cf2 = st.columns(2)
            title_fs = cf1.number_input(
                "Título", 8, 30, 13, 1, key=f"{key_prefix}_tfs",
            )
            axis_fs = cf2.number_input(
                "Etiquetas ejes", 6, 24, 12, 1, key=f"{key_prefix}_afs",
            )
            cf3, cf4 = st.columns(2)
            legend_fs = cf3.number_input(
                "Leyenda", 6, 20, 10, 1, key=f"{key_prefix}_lfs",
            )
            tick_fs = cf4.number_input(
                "Ticks", 6, 18, 10, 1, key=f"{key_prefix}_tkfs",
            )

        with tab_dl:
            cd1, cd2, cd3 = st.columns(3)
            w = cd1.number_input(
                "Ancho (in)", 4.0, 20.0, 10.0, 0.5, key=f"{key_prefix}_w",
            )
            h_in = cd2.number_input(
                "Alto (in)", 3.0, 15.0, 5.0, 0.5, key=f"{key_prefix}_h",
            )
            dpi = cd3.number_input(
                "DPI (solo PNG)", 72, 600, 200, 10, key=f"{key_prefix}_dpi",
            )
            fmt_label = st.selectbox(
                "Formato", list(EXPORT_FORMATS.keys()), index=0,
                key=f"{key_prefix}_fmt",
            )

        kwargs = dict(
            figsize=(w, h_in), dpi=int(dpi),
            show_stock=show_stock, show_stress=show_stress,
            show_floor=show_floor, show_opt=show_opt,
            show_observed=show_observed,
            ylim=ylim,
            title=title, xlabel=xlabel, ylabel=ylabel,
            title_fontsize=int(title_fs), axis_label_fontsize=int(axis_fs),
            legend_fontsize=int(legend_fs), tick_fontsize=int(tick_fs),
            legend_loc=legend_loc,
            series_styles=series_overrides,
            colors=colors_overrides,
        )

        st.markdown("**Preview de la figura a exportar:**")
        custom_fig = fig_factory(**kwargs)
        st.pyplot(custom_fig, use_container_width=True)

        fmt = EXPORT_FORMATS[fmt_label]
        buf = io.BytesIO()
        custom_fig.savefig(buf, format=fmt["ext"], bbox_inches="tight",
                           facecolor=custom_fig.get_facecolor())
        plt.close(custom_fig)
        st.download_button(
            f"Descargar {fmt['ext'].upper()}", data=buf.getvalue(),
            file_name=f"{filename_base}.{fmt['ext']}", mime=fmt["mime"],
            key=f"{key_prefix}_dl",
        )


# --- Layout: Figura 1 (h, P) + métricas ---

col1, col2 = st.columns([2.5, 1])

with col1:
    st.pyplot(make_hP_figure(), use_container_width=True)
    customize_and_export(
        make_hP_figure, HP_DEFAULTS, SERIES_DEFAULTS_HP, key_prefix="hp",
        filename_base="modelo_hP",
        has_band=True, xlim_kind="numeric",
    )

with col2:
    st.markdown("##### Valores notables")
    small_metric("Cap clásico (h=0)", f"${P_cap_val:.1f}/bbl")
    small_metric("Piso clásico (release máximo)", f"${P_floor_val:.1f}/bbl")

    st.markdown(f"##### A h = {h_actual:.2f} (stock = {stock_actual:.0f} mb)")
    small_metric("dot_R(h)", f"{release_rate(h_actual, params):.2f} mb/d")
    small_metric("q(h) — prob. de run", f"{q_actual:.2f}")
    small_metric("P_C(h)", f"${P_C_actual:.1f}/bbl")
    small_metric("P_R(h)", f"${P_R_actual:.1f}/bbl")
    small_metric("P modelo (composite)", f"${P_model_actual:.1f}/bbl")
    small_metric("R_repl(stock)", f"{R_repl_actual:.2f} mb/d")
    small_metric(
        "P* (Ormuz abierto, con reposición)",
        f"${P_star_open_actual:.1f}/bbl",
        delta=f"(+${P_star_open_actual - P_star:.1f} vs P* sin reposición)",
    )
    small_metric(
        f"P esperado (θ={theta_user:.2f})", f"${P_expected_actual:.1f}/bbl",
        delta=f"(vs observado: ${P_expected_actual - P_observed:+.1f})",
    )

    st.markdown("##### Wedge modelo vs observado")
    small_metric(
        "θ implícito",
        f"{theta:.2f}",
        delta=f"(Wedge: ${P_model_actual - P_observed:+.1f})",
    )


# --- Layout: Figura 2 (t, P) ---

st.divider()
st.markdown("## Proyección temporal")
st.caption(
    "Asume que el shock se mantiene (Ormuz cerrado). El stock se drena según "
    "`dStock/dt = −dot_R(h(Stock))`, partiendo del 30-abr-2026."
)

colT1, colT2 = st.columns([2.5, 1])

with colT1:
    st.pyplot(
        make_time_figure(theta_overlay=theta_overlay_df),
        use_container_width=True,
    )
    customize_and_export(
        make_time_figure, TP_DEFAULTS, SERIES_DEFAULTS_TP, key_prefix="tp",
        filename_base="modelo_tP",
        has_band=False, xlim_kind="none",
    )

with colT2:
    st.markdown("##### Hitos temporales")
    idx_stress = np.argmax(stock_t <= stock_stress) if np.any(stock_t <= stock_stress) else None
    idx_floor = np.argmax(stock_t <= stock_floor) if np.any(stock_t <= stock_floor) else None

    if idx_stress is not None and stock_t[idx_stress] <= stock_stress:
        small_metric(
            "Cruce del stress threshold",
            dates_t[idx_stress].strftime("%d-%b-%Y"),
            delta=f"(+{int(t_days[idx_stress])} días)",
        )
    else:
        small_metric("Cruce del stress threshold", "no alcanzado en 365 d")

    if idx_floor is not None and stock_t[idx_floor] <= stock_floor:
        small_metric(
            "Cruce del operational floor",
            dates_t[idx_floor].strftime("%d-%b-%Y"),
            delta=f"(+{int(t_days[idx_floor])} días)",
        )
    else:
        small_metric("Cruce del operational floor", "no alcanzado en 365 d")

    st.markdown("##### Stock final (a 365 d)")
    small_metric("Stock", f"{stock_t[-1]:.0f} mb",
                 delta=f"({stock_t[-1] - stock_actual:+.0f} mb)")
    small_metric("Precio composite", f"${P_t[-1]:.1f}/bbl",
                 delta=f"({P_t[-1] - P_t[0]:+.1f})")


# --- Layout: Figura — Term structure de θ desde forward curve ---

if forwards_df is not None:
    from model.data_loader import constant_maturity_to_term_structure

    st.divider()
    st.markdown("## Term structure de θ implícito (forward curve)")
    st.caption(
        "Para cada maturity del forward curve Brent, se proyecta el stock "
        "(integrando la función de release) y se computa el θ que reconcilia "
        "el precio forward con el composite del modelo a ese horizonte. Es "
        "una lectura del mercado sobre la probabilidad de normalización a "
        "distintos plazos."
    )

    # Modo master pipeline: usar constant_maturity (M1, M3, M6, M12, M24).
    # Modo sintético: usar el archivo de forward curves preparado.
    if isinstance(forwards_df, str) and forwards_df == "MASTER_CM":
        cm_df = cm_master_df
        snapshot_options = [
            d.strftime("%Y-%m-%d") for d in cm_df["observation_date"]
        ]
        chosen_snapshot = st.selectbox(
            "Fecha del snapshot de forward curve",
            snapshot_options, index=len(snapshot_options) - 1,
        )
        forward_input = constant_maturity_to_term_structure(cm_df, chosen_snapshot)
    else:
        snapshot_options = sorted(forwards_df["snapshot_date"].unique())
        chosen_snapshot = st.selectbox(
            "Fecha del snapshot de forward curve",
            snapshot_options, index=len(snapshot_options) - 1,
        )
        forward_input = forwards_df[
            forwards_df["snapshot_date"] == chosen_snapshot
        ]

    ts_fig, ts_data = make_term_structure_figure(
        forwards_df=forward_input,
        snapshot_date=chosen_snapshot,
        stock_at_snapshot=stock_actual,
        stock_floor_v=stock_floor,
        stock_stress_v=stock_stress,
        params_obj=params,
    )
    colTS1, colTS2 = st.columns([2.5, 1])
    with colTS1:
        st.pyplot(ts_fig, use_container_width=True)
    with colTS2:
        st.markdown("##### Lectura por horizonte")
        for m in (1, 3, 6, 12):
            row = ts_data[ts_data["maturity_month"] == m]
            if not row.empty:
                small_metric(
                    f"θ a {m} mes{'es' if m > 1 else ''}",
                    f"{row['theta'].iloc[0]:.2f}",
                )


# --- Layout: Figura 3 (evolución del stock) ---

st.divider()
st.markdown("## Evolución del stock")
st.caption(
    "Trayectoria del Total Global Observed Inventories bajo el supuesto de "
    "Ormuz cerrado, con los thresholds operacionales (stress y floor) y el "
    "stock óptimo de referencia."
)

colS1, colS2 = st.columns([2.5, 1])

with colS1:
    st.pyplot(make_stock_figure(), use_container_width=True)
    customize_and_export_stock(
        make_stock_figure, key_prefix="sk", filename_base="modelo_stock",
    )

with colS2:
    st.markdown("##### Niveles de referencia")
    small_metric("Stock óptimo", f"{stock_opt:.0f} mb")
    small_metric("Stress threshold", f"{stock_stress:.0f} mb")
    small_metric("Operational floor", f"{stock_floor:.0f} mb")

    st.markdown("##### Estado actual")
    small_metric(
        "Stock observado", f"{stock_actual:.0f} mb",
        delta=f"({stock_actual - stock_opt:+.0f} vs óptimo)",
    )

    st.markdown("##### Drawdown a 365 d")
    small_metric(
        "Stock final", f"{stock_t[-1]:.0f} mb",
        delta=f"({stock_t[-1] - stock_actual:+.0f} mb)",
    )
    small_metric(
        "Caída total", f"{stock_actual - stock_t[-1]:.0f} mb",
        delta=f"({(stock_actual - stock_t[-1]) / 365:.2f} mb/d promedio)",
    )


# --- Secciones expandibles ---

with st.expander("Cómo leer el modelo", expanded=False):
    st.markdown(r"""
### El problema

Cuando el Estrecho de Ormuz se cierra, ~13.6% de la oferta mundial de petróleo
deja de fluir. El precio observado depende de **cuánto stock buffer queda** para
amortiguar el shock y, sobre todo, de **si los holders de inventario entran o
no en pánico coordinado** (un "bank run" sobre el inventario físico).

### Los dos regímenes

El modelo separa dos equilibrios posibles para cada nivel de stock:

- **Régimen clásico ($P_C$)**: storage theory normal. Los holders liberan
  inventario de acuerdo a la teoría de Pindyck/Deaton-Laroque, equilibrando
  precio spot con expectativas futuras.
- **Régimen de run ($P_R$)**: pánico coordinado à la Diamond-Dybvig. Los
  holders retienen masivamente inventario anticipando que los otros también
  lo harán → precios disparados.

> **Importante**: el composite $P(h)$ es un **promedio en un punto** entre
> ambos regímenes, ponderado por la probabilidad de cada uno. **No es** una
> trayectoria temporal donde "eventualmente se produce una corrida". La
> corrida es un equilibrio alternativo, no un evento futuro garantizado; lo
> que cambia con $h$ es la **probabilidad** de estar en uno u otro régimen.

### El buffer slack $h$ y su mapeo a stock observado

$h \in [0, \infty)$ es una medida **adimensional** del colchón de inventario
disponible para release — **no son los inventarios directamente**, sino una
variable abstracta del modelo. La conexión con el stock real (en mb) la hace
nuestro mapeo lineal con el Total Global Observed Inventories (IEA OMR):

- Stock al **operational floor** (JPM ≈ 6.800 mb) → $h = 0$ (sin colchón)
- Stock al **stress threshold** (JPM ≈ 7.600 mb) → $h = h^*$ (umbral global game)

Default: 7.951 mb al 30-abr-2026 → $h \approx 0.43$.

### El global game y $h^*$

¿Por qué hay un régimen y no el otro? Goldstein-Pauzner (2005) muestran que en
juegos de coordinación con información imperfecta existe un **umbral crítico
$h^*$**: por encima, todos los holders eligen el equilibrio clásico; por debajo,
todos eligen el run. La transición es probabilística (no determinística) por la
dispersión de señales privadas $\sigma$:

$$q(h) = \Phi\!\left(\tfrac{h^* - h}{\sigma}\right)$$

Y el precio observado bajo el modelo estático es un promedio ponderado:

$$P(h) = (1-q(h))\,P_C(h) + q(h)\,P_R(h)$$

### El wedge $\theta$ y el precio esperado

El modelo asume que **el shock es persistente** (Ormuz no se reabre). En la
realidad, el mercado pricea una probabilidad $\theta$ de que el shock se
resuelva. Por eso el precio observado suele ser menor al $P(h)$ del modelo:

$$P_{\rm esp}(h) = (1-\theta)\,P(h) + \theta\,P^{\ast}(h)$$

- **Slider $\theta$**: movelo hasta que la curva azul punteada calce con el
  punto observado. Ese $\theta$ es la probabilidad implícita de normalización
  que el mercado está priciendo.
- **$\theta$ implícito** en la tabla derecha: idem, pero calculado de forma
  cerrada por despeje a partir de $P_{\rm observado}$.
""")

    st.markdown(r"""### Por qué $P^{\ast}$ depende de $h$ (demanda de reposición)

Cuando Ormuz se reabre con inventarios por debajo del nivel óptimo
(default 8.200 mb), aparece una **demanda extra para reponer**. Modelamos
esa tasa $R_{\rm repl}$ como lineal saturada:""")

    st.latex(
        r"R_{\rm repl}(\text{Stock}) = R_{\rm repl,max} \cdot "
        r"\mathrm{clamp}\!\left(\frac{\text{Stock}_{\rm opt} - \text{Stock}}"
        r"{\text{Stock}_{\rm opt} - \text{Stock}_{\rm floor}},\,0,\,1\right)"
    )

    st.markdown(r"""El equilibrio "Ormuz abierto" pasa a ser
$D(P^{\ast}) + R_{\rm repl} = S_{\rm open}(P^{\ast})$, lo que sube $P^{\ast}$
por encima del precio pre-shock $P^{\ast}_{\rm ref} = 70$. Como $R_{\rm repl}$
crece a medida que $h$ baja (porque Stock baja), la curva violeta
$P^{\ast}(h)$ tiene **pendiente positiva hacia la izquierda**.

Con la calibración default ($\varepsilon_d = \varepsilon_s = 0{,}05$), cada
1 mb/d de reposición sube $P^{\ast}$ unos ~7 USD/bbl.""")

    st.markdown(r"""### Cómo leer la figura $(h, P)$

- **Curva verde** $P_C(h)$: precio clásico. Decreciente: más stock $\Rightarrow$
  más release $\Rightarrow$ precio menor.
- **Curva roja punteada** $P_R(h)$: precio en régimen de run. Mucho más alto
  porque los hoarders retienen.
- **Curva negra** $P(h)$: composite ponderado por $q(h)$.
- **Curva azul punteada** $P_{\rm esp}(h)$: composite descontado por la prob.
  $\theta$ de normalización.
- **Curva violeta dash-dot** $P^{\ast}(h)$ (opcional): precio en el mundo
  contrafactual donde Ormuz se reabre. **Tiene pendiente positiva hacia la
  izquierda** porque a menor stock, mayor la demanda de reposición y mayor
  $P^{\ast}$. Se enciende desde el tab "Elementos" del panel de personalización.
  La curva azul $P_{\rm esp}$ es exactamente el promedio ponderado entre
  la negra $P(h)$ y esta violeta.
- **Banda naranja**: zona de fragilidad $[h^* - 2\sigma, h^* + 2\sigma]$.
- **Punto azul**: precio observado actual.

### Cómo leer la figura temporal $(t, P)$

La trayectoria se construye **asumiendo Ormuz cerrado durante todo el
horizonte**: el stock se drena según $dStock/dt = -\dot R(h(Stock))$ por
365 días. Para cada fecha $t$, las curvas se evalúan al stock vigente en
ese instante.

Cómo interpretar cada curva en este contexto:

- **Curva negra $P(t)$**: el composite "si Ormuz sigue cerrado en t". Es
  la **upper bound** condicional a no-apertura — lo que costaría el barril
  si el mercado supiera con certeza que el shock continúa.
- **Curva violeta $P^{\ast}(t)$**: "si llego al día t con Ormuz cerrado y justo
  ese día se abre". Sube con $t$ porque mientras más se drenó el stock,
  mayor la demanda de reposición. Es la **lower bound** condicional a
  apertura.
- **Curva azul $P_{\rm esp}(t)$**: lo que **el mercado realmente paga
  hoy**, combinando ambas expectativas con peso $\theta$. Es la curva
  empíricamente relevante.

> **Sobre $\theta$ en la fig 2**: el slider mantiene $\theta$ **constante a
> lo largo de todo el horizonte**. El modelo no condiciona $\theta(t)$ al
> paso del tiempo — no decae aunque pasen meses sin apertura, ni sube
> aunque el stock se acerque al floor. Endogenizar $\theta(t)$ sería una
> extensión natural pero no está implementada.

La columna derecha indica cuándo se cruzan los umbrales (stress y floor)
bajo la trayectoria de drenaje.

### Personalizar las figuras para una presentación

Cada figura tiene un panel **"Personalizar y exportar"** debajo. Te permite:

- **Elementos**: encender/apagar curvas individuales, el punto observado,
  las líneas de referencia y la banda de fragilidad.
- **Ejes**: ajustar manualmente los rangos X/Y (o dejar autoajuste).
- **Textos**: editar título, etiquetas de ejes y posición/tamaño de la leyenda;
  ajustar tamaño de fuente de cada elemento.
- **Tamaño y descarga**: definir ancho/alto/DPI del PNG exportable y bajarlo
  con un botón.

Los cambios se reflejan en un preview en vivo antes de descargar.
""")

with st.expander("Ecuaciones del modelo"):
    st.markdown("**Régimen clásico:**")
    st.latex(r"D(P_C) = S_f(P_C) + \dot R(h)")

    st.markdown("**Régimen run:**")
    st.latex(r"D(P_R) + \delta(h) = S_f(P_R) + (1-\mu)\,\dot R(h)")

    st.markdown("**Probabilidad de régimen run (Goldstein-Pauzner):**")
    st.latex(r"q(h) = \Phi\!\left(\frac{h^* - h}{\sigma}\right)")

    st.markdown("**Precio observado bajo el modelo:**")
    st.latex(r"P(h) = (1-q(h))\,P_C(h) + q(h)\,P_R(h)")

    st.markdown("**Precio esperado por el mercado (descontando normalización):**")
    st.latex(r"P_{\rm esp}(h) = (1-\theta)\,P(h) + \theta\,P^*(h)")

    st.markdown("**Probabilidad implícita de normalización (despeje, "
                "usando $P^{\\ast}$ al stock actual):**")
    st.latex(r"\theta = \frac{P(h) - P_{\text{mercado}}}{P(h) - P^*(h)}")

    st.markdown("**Demanda de reposición (solo activa con Ormuz abierto):**")
    st.latex(
        r"R_{\rm repl}(\text{Stock}) = R_{\rm repl,max} \cdot "
        r"\text{clamp}\!\left(\tfrac{\text{Stock}_{\rm opt} - \text{Stock}}"
        r"{\text{Stock}_{\rm opt} - \text{Stock}_{\rm floor}},\,0,\,1\right)"
    )

    st.markdown("**Equilibrio con Ormuz abierto:**")
    st.latex(r"D(P^*) + R_{\rm repl}(\text{Stock}) = S_{\rm open}(P^*)")

    st.markdown("**Mapeo stock ↔ h (lineal, anclado en thresholds JPM):**")
    st.latex(
        r"h(\text{Stock}) = h^* \cdot "
        r"\frac{\text{Stock} - \text{Stock}_{\rm floor}}"
        r"{\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}"
    )

    st.markdown("**Dinámica del stock (asumiendo shock persistente):**")
    st.latex(r"\frac{d\,\text{Stock}}{dt} = -\dot R\!\left(h(\text{Stock})\right)")

with st.expander("Funciones constituyentes"):
    st.markdown("**Demanda y oferta de flujo (elasticidad constante):**")
    st.latex(r"D(P) = D_0 \left(\frac{P}{P^*}\right)^{-\epsilon_d}")
    st.latex(r"S_f(P) = S_{f,0} \left(\frac{P}{P^*}\right)^{\epsilon_s}")

    st.markdown("**Función de release (Michaelis-Menten):**")
    st.latex(r"\dot R(h) = R_{\max} \cdot \frac{h}{h + h_R}")

    st.markdown("**Demanda especulativa en el run:**")
    st.latex(r"\delta(h) = \delta_0 \cdot \frac{\dot R(h)}{R_{\max}}")

with st.expander("Referencias bibliográficas"):
    st.markdown("""
    - **Caldara, D., Cavallo, M., Iacoviello, M. (2019).** Oil Price Elasticities and Oil Price Fluctuations. *Journal of Monetary Economics*, 103, 1-20.
    - **Deaton, A., Laroque, G. (1992).** On the Behaviour of Commodity Prices. *Review of Economic Studies*, 59(1), 1-23.
    - **Diamond, D.W., Dybvig, P.H. (1983).** Bank Runs, Deposit Insurance, and Liquidity. *Journal of Political Economy*, 91(3), 401-419.
    - **Goldstein, I., Pauzner, A. (2005).** Demand-Deposit Contracts and the Probability of Bank Runs. *Journal of Finance*, 60(3), 1293-1327.
    - **Hamilton, J.D. (2009).** Understanding Crude Oil Prices. *Energy Journal*, 30(2), 179-206.
    - **Kilian, L. (2009).** Not All Oil Price Shocks Are Alike. *American Economic Review*, 99(3), 1053-1069.
    - **Morris, S., Shin, H.S. (1998).** Unique Equilibrium in a Model of Self-Fulfilling Currency Attacks. *AER*, 88(3), 587-597.
    - **Pindyck, R.S. (2001).** The Dynamics of Commodity Spot and Futures Markets: A Primer. *Energy Journal*, 22(3), 1-29.
    - **Routledge, B.R., Seppi, D.J., Spatt, C.S. (2000).** Equilibrium Forward Curves for Commodities. *Journal of Finance*, 55(3), 1297-1338.
    """)


st.divider()
st.caption(
    "Modelo estructural del precio del petróleo bajo stress de oferta — mayo 2026. "
    "Ver la sección expandible \"Cómo leer el modelo\" para una guía rápida."
)
