"""
Funciones empíricas y derivadas del modelo.

Computa estadísticas de interés para el análisis: θ implícito, valores notables,
interpretaciones del wedge modelo-observado.
"""

from .calibration import ModelParams
from .core import P_classical


def theta_implicit(P_model: float, P_observed: float, params: ModelParams) -> float:
    """
    Probabilidad implícita de normalización del shock.

    Dado el wedge entre el precio predicho por el modelo y el precio observado en
    el mercado, estima qué probabilidad θ de normalización futura el mercado está
    priciendo implícitamente.

    Ecuación (Sección 10 del PDF):
        P_mercado = (1 - θ) · P_modelo + θ · P*

    Despeja θ:
        θ = (P_modelo - P_mercado) / (P_modelo - P*)

    Interpretación:
        θ ≈ 0: el mercado pricea el shock como persistente (P_mercado ≈ P_modelo).
        θ ≈ 1: el mercado espera normalización inmediata (P_mercado ≈ P*).
        θ ∈ (0, 1): el mercado asigna una probabilidad mixta.

    El parámetro θ captura cómo el mercado evalúa las expectativas sobre resolución
    del cierre de Ormuz, más allá de lo que el modelo estático permite endogenizar.

    Args:
        P_model: Precio predicho por el modelo (USD/bbl).
        P_observed: Precio observado en el mercado (USD/bbl).
        params: Instancia de ModelParams.

    Returns:
        θ implícito (float, idealmente en [0, 1]).
    """
    if P_model == params.P_star:
        return 0.0
    return (P_model - P_observed) / (P_model - params.P_star)


def P_cap(params: ModelParams) -> float:
    """
    Cap clásico: precio en régimen clásico cuando h → 0 (sin inventario).

    En el límite h → 0, la función de release se anula (dot_R → 0).
    El equilibrio clásico se reduce a:
        D(P_cap) = S_f(P_cap)
        D_0 · (P/P*)^(-ε_d) = S_f0 · (P/P*)^(ε_s)

    Solución cerrada (Sección 5.2 del PDF):
        P_cap / P* = (D_0 / S_f0)^(1 / (ε_d + ε_s))

    Con calibración default (ε_d = ε_s = 0.05, D_0 = 104, S_f0 = 95, P* = 70):
        P_cap ≈ 70 · (104/95)^(1/0.10) ≈ 70 · 2.47 ≈ 173 USD/bbl

    Args:
        params: Instancia de ModelParams.

    Returns:
        P_cap (USD/bbl).
    """
    return params.P_star * (params.D_0 / params.S_f0) ** (1.0 / (params.eps_d + params.eps_s))


def P_floor(params: ModelParams) -> float:
    """
    Piso clásico: precio cuando h es grande y release está saturado.

    Para h grande, dot_R(h) → R_max (saturación Michaelis-Menten).
    El equilibrio clásico tiende a:
        D(P_floor) = S_f(P_floor) + R_max

    No tiene forma cerrada simple; se computa numéricamente con h grande (≈100).
    Con calibración default, P_floor ≈ 95 USD/bbl.

    Nota: el piso del modelo está notablemente por encima de P* (70) porque incluso
    con máximo release, la demanda de sustitución sigue siendo limitada.

    Args:
        params: Instancia de ModelParams.

    Returns:
        P_floor (USD/bbl).
    """
    return P_classical(100.0, params)
