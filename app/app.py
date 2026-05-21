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
stock_actual = st.sidebar.slider(
    "Stock actual (millones de bbl)", 6500.0, 9000.0, 7951.0, 10.0,
    help="Total Global Observed Inventories según IEA OMR. Default: 7.951 mb al 30-abr-2026."
)
stock_stress = st.sidebar.slider(
    "Stress threshold (JPM, mb)", 6500.0, 9000.0, 7600.0, 10.0,
    help="Operational stress según JPMorgan. Por debajo, el run-risk se activa."
)
stock_floor = st.sidebar.slider(
    "Operational floor (JPM, mb)", 5000.0, 8000.0, 6800.0, 10.0,
    help="Mínimo operacional según JPMorgan. Mapea a h = 0."
)

st.sidebar.subheader("Observación de mercado")
P_observed = st.sidebar.slider(
    "P observado (USD/bbl)", 60.0, 200.0, 114.0, 1.0,
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


# --- Cómputo: figura 1 (h, P) ---

params = ModelParams(
    P_star=P_star, D_0=D_0, S_f0=S_f0, eps_d=eps_d, eps_s=eps_s,
    R_max=R_max, h_R=h_R, mu=mu, delta_0=delta_0,
    h_star=h_star, sigma=sigma,
)

h_actual = h_from_stock(stock_actual, stock_floor, stock_stress, h_star)

h_grid = np.linspace(0.001, 1.5, 600)
P_C_arr = np.array([P_classical(h, params) for h in h_grid])
P_R_arr = np.array([P_run(h, params) for h in h_grid])
q_arr = np.array([q_run(h, params) for h in h_grid])
P_arr = (1 - q_arr) * P_C_arr + q_arr * P_R_arr
P_expected_arr = (1 - theta_user) * P_arr + theta_user * P_star

P_cap_val = P_cap(params)
P_floor_val = P_floor(params)
P_C_actual = P_classical(h_actual, params)
P_R_actual = P_run(h_actual, params)
q_actual = q_run(h_actual, params)
P_model_actual = (1 - q_actual) * P_C_actual + q_actual * P_R_actual
P_expected_actual = (1 - theta_user) * P_model_actual + theta_user * P_star
theta = theta_implicit(P_model_actual, P_observed, params)


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
P_expected_t = (1 - theta_user) * P_t + theta_user * P_star

dates_t = [t_obs_date + timedelta(days=int(d)) for d in t_days]


# --- Helpers de figuras ---

def make_hP_figure(figsize=(10, 6), dpi=110):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    ax.axvspan(h_star - 2*sigma, h_star + 2*sigma, alpha=0.10, color="#F57C00")
    ax.axhline(P_star, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_floor_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_cap_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)

    ax.plot(h_grid, P_C_arr, color="#0F766E", linewidth=2.4,
            label=r"$P_C(h)$ — clásico")
    ax.plot(h_grid, P_R_arr, color="#C62828", linewidth=2.4, linestyle="--",
            label=r"$P_R(h)$ — run")
    ax.plot(h_grid, P_arr, color="#000000", linewidth=3.0,
            label=r"$P(h)$ — composite")
    ax.plot(h_grid, P_expected_arr, color="#1E40AF", linewidth=2.2, linestyle=":",
            label=fr"$P_{{\rm esp}}(h)$ — esperado (θ={theta_user:.2f})")

    ax.axvline(h_star, color="#475569", linestyle=":", linewidth=1.2)
    ax.scatter([h_actual], [P_observed], s=100, color="#1E40AF", zorder=10,
               edgecolor="white", linewidth=1.5, label="Observado")

    ax.set_xlim(0, 1.5)
    ax.set_xlabel(r"$h$ — buffer slack agregado", fontsize=12, fontweight="bold")
    ax.set_ylabel(r"$P$ — precio (USD/bbl)", fontsize=12, fontweight="bold")
    ax.set_title("Modelo estructural en el plano (h, P)", fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10, frameon=True, framealpha=0.6,
              edgecolor="none")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig


def make_time_figure(figsize=(10, 6), dpi=110):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    ax.axhline(P_star, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_floor_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_cap_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)

    ax.plot(dates_t, P_C_t, color="#0F766E", linewidth=2.4,
            label=r"$P_C(t)$ — clásico")
    ax.plot(dates_t, P_R_t, color="#C62828", linewidth=2.4, linestyle="--",
            label=r"$P_R(t)$ — run")
    ax.plot(dates_t, P_t, color="#000000", linewidth=3.0,
            label=r"$P(t)$ — composite")
    ax.plot(dates_t, P_expected_t, color="#1E40AF", linewidth=2.2, linestyle=":",
            label=fr"$P_{{\rm esp}}(t)$ — esperado (θ={theta_user:.2f})")

    ax.scatter([t_obs_date], [P_observed], s=100, color="#1E40AF", zorder=10,
               edgecolor="white", linewidth=1.5, label=f"Observado 30-abr-2026")

    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b-%y"))
    fig.autofmt_xdate(rotation=0, ha="center")

    ax.set_xlabel("Fecha", fontsize=12, fontweight="bold")
    ax.set_ylabel(r"$P$ — precio (USD/bbl)", fontsize=12, fontweight="bold")
    ax.set_title(
        "Proyección temporal: precio dado dStock/dt = −dot_R(h(Stock))",
        fontsize=13, fontweight="bold",
    )
    ax.legend(loc="lower right", fontsize=10, frameon=True, framealpha=0.6,
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


def export_controls(fig_factory, key_prefix: str, default_w=10.0, default_h=6.0,
                    filename="figura.png"):
    """Renderiza inputs de tamaño + botón de descarga PNG."""
    with st.expander("Exportar figura (para presentación)"):
        c1, c2, c3 = st.columns(3)
        with c1:
            w = st.number_input("Ancho (in)", 4.0, 20.0, default_w, 0.5,
                                key=f"{key_prefix}_w")
        with c2:
            h = st.number_input("Alto (in)", 3.0, 15.0, default_h, 0.5,
                                key=f"{key_prefix}_h")
        with c3:
            dpi = st.number_input("DPI", 72, 600, 200, 10, key=f"{key_prefix}_dpi")

        fig_export = fig_factory(figsize=(w, h), dpi=int(dpi))
        buf = io.BytesIO()
        fig_export.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig_export)
        st.download_button(
            "Descargar PNG", data=buf.getvalue(),
            file_name=filename, mime="image/png",
            key=f"{key_prefix}_dl",
        )


# --- Layout: Figura 1 (h, P) + métricas ---

col1, col2 = st.columns([2.5, 1])

with col1:
    st.pyplot(make_hP_figure(), use_container_width=True)
    export_controls(make_hP_figure, key_prefix="hp", filename="modelo_hP.png")

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
    st.pyplot(make_time_figure(), use_container_width=True)
    export_controls(make_time_figure, key_prefix="tp", filename="modelo_tP.png")

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

### El buffer slack $h$ y su mapeo a stock observado

$h \in [0, \infty)$ es una medida adimensional del **colchón de inventario disponible
para release** (cuán lejos estamos del piso operacional). Lo mapeamos linealmente
con el Total Global Observed Inventories (IEA OMR):

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

$$P_{\rm esp}(h) = (1-\theta)\,P(h) + \theta\,P^*$$

- **Slider $\theta$**: movelo hasta que la curva azul punteada calce con el
  punto observado. Ese $\theta$ es la probabilidad implícita de normalización
  que el mercado está priciendo.
- **$\theta$ implícito** en la tabla derecha: idem, pero calculado de forma
  cerrada por despeje a partir de $P_{\rm observado}$.

### Cómo leer la figura $(h, P)$

- **Curva verde** $P_C(h)$: precio clásico. Decreciente: más stock $\Rightarrow$
  más release $\Rightarrow$ precio menor.
- **Curva roja punteada** $P_R(h)$: precio en régimen de run. Mucho más alto
  porque los hoarders retienen.
- **Curva negra** $P(h)$: composite ponderado por $q(h)$.
- **Curva azul punteada** $P_{\rm esp}(h)$: composite descontado por la prob.
  $\theta$ de normalización.
- **Banda naranja**: zona de fragilidad $[h^* - 2\sigma, h^* + 2\sigma]$.
- **Punto azul**: precio observado actual.

### Cómo leer la figura temporal $(t, P)$

Asume shock persistente. El stock se drena según $dStock/dt = -\dot R(h(Stock))$,
y se grafica el precio de equilibrio a lo largo de 365 días. La columna derecha
indica cuándo se cruzan los umbrales (stress y floor) bajo esa trayectoria.
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
    st.latex(r"P_{\rm esp}(h) = (1-\theta)\,P(h) + \theta\,P^*")

    st.markdown("**Probabilidad implícita de normalización (despeje):**")
    st.latex(r"\theta = \frac{P(h) - P_{\text{mercado}}}{P(h) - P^*}")

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
