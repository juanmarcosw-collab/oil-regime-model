"""
Streamlit app para explorar interactivamente el modelo estructural del precio del petróleo.

Permite mover sliders sobre los parámetros y ver en tiempo real cómo cambian las curvas
P_C(h), P_R(h) y P(h), junto con los valores notables del modelo.

Para correr desde la raíz del proyecto:
    streamlit run app/app.py

Requiere: streamlit, numpy, scipy, matplotlib.
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

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
st.caption("Explorador interactivo — calibración BCCh, mayo 2026")


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
    help="Elasticidad short-run de demanda (BCCh: 0,05; Caldara et al. 2019: 0,08-0,20)."
)
eps_s = st.sidebar.slider(
    "ε_s (elasticidad de oferta)", 0.01, 0.30, 0.05, 0.01,
    help="Elasticidad short-run de oferta (BCCh: 0,05)."
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

st.sidebar.subheader("Observación actual")
h_actual = st.sidebar.slider(
    "h actual estimado", 0.05, 1.0, 0.24, 0.01,
    help="Buffer slack actual estimado a partir de OMR mayo 2026."
)
P_observed = st.sidebar.slider(
    "P observado (USD/bbl)", 60.0, 200.0, 110.0, 1.0,
    help="Precio Brent observado al cierre de mayo 2026."
)


# --- Cómputo ---

params = ModelParams(
    P_star=P_star, D_0=D_0, S_f0=S_f0, eps_d=eps_d, eps_s=eps_s,
    R_max=R_max, h_R=h_R, mu=mu, delta_0=delta_0,
    h_star=h_star, sigma=sigma,
)

h_grid = np.linspace(0.001, 1.5, 600)
P_C_arr = np.array([P_classical(h, params) for h in h_grid])
P_R_arr = np.array([P_run(h, params) for h in h_grid])
q_arr = np.array([q_run(h, params) for h in h_grid])
P_arr = (1 - q_arr) * P_C_arr + q_arr * P_R_arr

P_cap_val = P_cap(params)
P_floor_val = P_floor(params)
P_C_actual = P_classical(h_actual, params)
P_R_actual = P_run(h_actual, params)
q_actual = q_run(h_actual, params)
P_model_actual = (1 - q_actual) * P_C_actual + q_actual * P_R_actual
theta = theta_implicit(P_model_actual, P_observed, params)


# --- Layout principal: figura + tabla de valores ---

col1, col2 = st.columns([2.5, 1])

with col1:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

    # Banda de fragilidad
    ax.axvspan(h_star - 2*sigma, h_star + 2*sigma, alpha=0.10, color="#F57C00")

    # Líneas de referencia
    ax.axhline(P_star, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_floor_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)
    ax.axhline(P_cap_val, color="#94A3B8", linestyle=":", linewidth=1, alpha=0.6)

    # Curvas
    ax.plot(h_grid, P_C_arr, color="#0F766E", linewidth=2.4,
            label=r"$P_C(h)$ — clásico")
    ax.plot(h_grid, P_R_arr, color="#C62828", linewidth=2.4, linestyle="--",
            label=r"$P_R(h)$ — run")
    ax.plot(h_grid, P_arr, color="#000000", linewidth=3.0,
            label=r"$P(h)$ — composite")

    # h*
    ax.axvline(h_star, color="#475569", linestyle=":", linewidth=1.2)

    # Marcador observado
    ax.scatter([h_actual], [P_observed], s=100, color="#1E40AF", zorder=10,
               edgecolor="white", linewidth=1.5, label="Observado")

    ax.set_xlim(0, 1.5)
    ax.set_xlabel(r"$h$ — buffer slack agregado", fontsize=12, fontweight="bold")
    ax.set_ylabel(r"$P$ — precio (USD/bbl)", fontsize=12, fontweight="bold")
    ax.set_title("Modelo estructural en el plano (h, P)", fontsize=13, fontweight="bold")
    ax.legend(loc="center right", fontsize=10)
    ax.grid(alpha=0.15, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    st.pyplot(fig, use_container_width=True)

with col2:
    st.markdown("### Valores notables")
    st.metric("Cap clásico (h=0)", f"${P_cap_val:.1f}/bbl")
    st.metric("Piso clásico (release máximo)", f"${P_floor_val:.1f}/bbl")

    st.markdown(f"### A h = {h_actual:.2f}")
    st.metric("dot_R(h)", f"{release_rate(h_actual, params):.2f} mb/d")
    st.metric("q(h) — prob. de run", f"{q_actual:.2f}")
    st.metric("P_C(h)", f"${P_C_actual:.1f}/bbl")
    st.metric("P_R(h)", f"${P_R_actual:.1f}/bbl")
    st.metric("P modelo (composite)", f"${P_model_actual:.1f}/bbl")

    st.markdown("### Wedge modelo vs observado")
    st.metric(
        "θ implícito",
        f"{theta:.2f}",
        delta=f"Wedge: ${P_model_actual - P_observed:+.1f}",
        help="Probabilidad implícita de normalización del shock."
    )


# --- Secciones expandibles ---

with st.expander("Ecuaciones del modelo"):
    st.markdown("**Régimen clásico:**")
    st.latex(r"D(P_C) = S_f(P_C) + \dot R(h)")

    st.markdown("**Régimen run:**")
    st.latex(r"D(P_R) + \delta(h) = S_f(P_R) + (1-\mu)\,\dot R(h)")

    st.markdown("**Probabilidad de régimen run (Goldstein-Pauzner):**")
    st.latex(r"q(h) = \Phi\!\left(\frac{h^* - h}{\sigma}\right)")

    st.markdown("**Precio observado bajo el modelo:**")
    st.latex(r"P(h) = (1-q(h))\,P_C(h) + q(h)\,P_R(h)")

    st.markdown("**Probabilidad implícita de normalización:**")
    st.latex(r"\theta = \frac{P(h) - P_{\text{mercado}}}{P(h) - P^*}")

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
    "Modelo desarrollado por la División de Política Monetaria, BCCh — mayo 2026. "
    "Documento de trabajo, versión 1. Ver el PDF adjunto para descripción completa."
)
