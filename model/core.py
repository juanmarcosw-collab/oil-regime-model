"""
Núcleo del modelo estructural del precio del petróleo bajo stress de oferta.

Implementa el modelo descrito en el PDF "Modelo estructural del precio del petróleo
bajo stress de oferta" (mayo 2026), secciones 4-7.

Componentes:
  - Régimen clásico: P_C(h) solución de D(P) = S_f(P) + dot_R(h)
  - Régimen run:     P_R(h) solución de D(P) + δ(h) = S_f(P) + (1-μ)·dot_R(h)
  - Probabilidad de régimen: q(h) = Φ((h* - h)/σ)  [Goldstein-Pauzner 2005]
  - Precio observado: P(h) = (1-q(h))·P_C(h) + q(h)·P_R(h)
"""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

from .calibration import ModelParams


# === Funciones auxiliares ===

def release_rate(h: float, params: ModelParams) -> float:
    """
    Ritmo de liberación de reservas como función del buffer slack.

    Forma funcional Michaelis-Menten (Sección 4.2 del PDF):
        dot_R(h) = R_max · h / (h + h_R)

    Propiedades:
        dot_R(0) = 0           (no se puede liberar lo que no se tiene)
        dot_R(∞) = R_max       (saturación a capacidad técnica)
        dot_R(h_R) = R_max/2   (saturación al 50% cuando h = h_R)

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Tasa de liberación (millones de barriles/día).
    """
    return params.R_max * h / (h + params.h_R)


def delta_run(h: float, params: ModelParams) -> float:
    """
    Demanda especulativa adicional en régimen de run.

    Modelada como proporcional al release disponible (Sección 6.4 del PDF):
        δ(h) = δ_0 · dot_R(h) / R_max

    Justificación: en el run, los speculators compran inventario liberado
    anticipando precios futuros mayores. La demanda especulativa crece con
    el volumen disponible, pero se desvanece cuando dot_R → 0.

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Demanda especulativa (millones de barriles/día).
    """
    return params.delta_0 * release_rate(h, params) / params.R_max


# === Ecuaciones de equilibrio ===

def P_classical(h: float, params: ModelParams) -> float:
    """
    Precio en régimen clásico (storage theory).

    Resuelve la condición de market clearing (Sección 5.1 del PDF):
        D(P_C) = S_f(P_C) + dot_R(h)

    Equivalentemente:
        D_0 · (P/P*)^(-ε_d) = S_f0 · (P/P*)^(ε_s) + dot_R(h)

    Método: brentq (root-finding numérico). Rango de búsqueda: [30, 2000] USD/bbl.

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Precio de equilibrio P_C(h) (USD/bbl).
    """
    R = release_rate(h, params)

    def f(P):
        return (params.D_0 * (P / params.P_star) ** (-params.eps_d)
                - params.S_f0 * (P / params.P_star) ** params.eps_s
                - R)

    return brentq(f, 30, 2000)


def P_run(h: float, params: ModelParams) -> float:
    """
    Precio en régimen de run (coordinación y pánico).

    Resuelve la condición de market clearing modificada (Sección 6.4 del PDF):
        D(P_R) + δ(h) = S_f(P_R) + (1 - μ) · dot_R(h)

    Donde:
      - δ(h) es la demanda especulativa adicional (hoarders comprando).
      - μ es la fracción del release retenida por hoarders.

    Ambos términos se desvanecen en h → 0, garantizando que P_R(0) = P_C(0)
    (convergencia en stockout: sin inventario, no hay diferencia de régimen).

    Método: brentq (root-finding numérico). Rango de búsqueda: [30, 2000] USD/bbl.

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Precio de equilibrio P_R(h) (USD/bbl).
    """
    R = release_rate(h, params)
    delta = delta_run(h, params)

    def f(P):
        return (params.D_0 * (P / params.P_star) ** (-params.eps_d) + delta
                - params.S_f0 * (P / params.P_star) ** params.eps_s
                - (1 - params.mu) * R)

    return brentq(f, 30, 2000)


def q_run(h: float, params: ModelParams) -> float:
    """
    Probabilidad de estar en régimen run, dado el buffer slack.

    Forma cerrada derivada de Goldstein-Pauzner (2005) en el límite σ → 0
    (Sección 6.3 del PDF):
        q(h) = Φ((h* - h) / σ)

    donde Φ es la CDF normal estándar.

    Propiedades:
        q(h*) = 0.5       (probabilidad 50% en el umbral).
        q(h → ∞) → 0      (régimen clásico domina).
        q(h → -∞) → 1     (régimen run domina, aunque h ≥ 0 acota inferiormente).

    Parámetros:
      - h_star: umbral crítico del global game.
      - sigma: dispersión de señales privadas.

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Probabilidad q(h) ∈ [0, 1].
    """
    return norm.cdf((params.h_star - h) / params.sigma)


def P_composite(h: float, params: ModelParams) -> float:
    """
    Precio observado bajo el modelo estático: promedio ponderado de regímenes.

    Ecuación (Sección 7 del PDF):
        P(h) = (1 - q(h)) · P_C(h) + q(h) · P_R(h)

    Es lo que un econometrista observaría como precio spot bajo el supuesto
    de cierre persistente del shock (sin expectativas de normalización).

    Interpretación: la probabilidad q(h) actúa como peso de la incertidumbre
    sobre cuál régimen se materializa.

    Args:
        h: Buffer slack.
        params: Instancia de ModelParams.

    Returns:
        Precio composite P(h) (USD/bbl).
    """
    p_c = P_classical(h, params)
    p_r = P_run(h, params)
    q = q_run(h, params)
    return (1 - q) * p_c + q * p_r


