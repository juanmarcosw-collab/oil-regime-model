"""
Inferencia empírica del θ implícito (probabilidad de normalización) a partir
de series de precios y stocks observados.

Funciones principales:
  - theta_from_observation: θ implícito en una fecha puntual.
  - theta_series: serie temporal de θ a partir de DataFrames alineados.
  - theta_term_structure_from_forward: term structure de θ desde forward curve.

Convención de signos: θ se reporta sin clipear, así que valores fuera de [0,1]
son señales informativas (modelo no calza bien o supuestos violados).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .calibration import ModelParams
from .core import P_classical, P_run, q_run


# ---------------------------------------------------------------------------
# Mapeo stock -> h (replicado de app.py para evitar import circular)
# ---------------------------------------------------------------------------

def h_from_stock(
    stock: float,
    stock_floor: float,
    stock_stress: float,
    h_star: float,
) -> float:
    """Mapeo lineal Ext 2: stock_floor -> 0, stock_stress -> h_star."""
    if stock_stress <= stock_floor:
        return 0.0
    return max(0.0, h_star * (stock - stock_floor) / (stock_stress - stock_floor))


# ---------------------------------------------------------------------------
# Cómputo puntual
# ---------------------------------------------------------------------------

def composite_price(h: float, params: ModelParams) -> float:
    """Precio composite del modelo a un h dado."""
    p_c = P_classical(h, params)
    p_r = P_run(h, params)
    q = q_run(h, params)
    return (1.0 - q) * p_c + q * p_r


def theta_from_observation(
    price_observed: float,
    stock: float,
    stock_floor: float,
    stock_stress: float,
    params: ModelParams,
) -> dict:
    """θ implícito y diagnósticos para una observación (P, Stock).

    Retorna:
        dict con h, p_c, p_r, q, p_composite, theta, in_range.
    """
    h = h_from_stock(stock, stock_floor, stock_stress, params.h_star)
    p_c = P_classical(h, params)
    p_r = P_run(h, params)
    q = q_run(h, params)
    p_composite = (1.0 - q) * p_c + q * p_r

    # Despeje de θ desde P_mercado = (1-θ)·P_modelo + θ·P*
    denom = p_composite - params.P_star
    if abs(denom) < 1e-9:
        theta = float("nan")
    else:
        theta = (p_composite - price_observed) / denom

    return {
        "h": h,
        "p_classical": p_c,
        "p_run": p_r,
        "q": q,
        "p_composite": p_composite,
        "theta": theta,
        "in_range": 0.0 <= theta <= 1.0,
    }


# ---------------------------------------------------------------------------
# Serie temporal
# ---------------------------------------------------------------------------

def interpolate_stocks(
    stocks_df: pd.DataFrame,
    target_dates: pd.DatetimeIndex,
) -> pd.Series:
    """Interpola linealmente la serie de stocks hacia las target_dates.

    stocks_df debe tener columnas ['date', 'stock_mb']. target_dates fuera del
    rango se rellenan con el extremo más cercano (extrapolación flat).
    """
    stocks_df = stocks_df.copy()
    stocks_df["date"] = pd.to_datetime(stocks_df["date"])
    stocks_df = stocks_df.sort_values("date").set_index("date")

    # Reindexa al union de fechas y luego interpola
    all_dates = stocks_df.index.union(target_dates).sort_values()
    s = stocks_df["stock_mb"].reindex(all_dates).interpolate(method="time")
    # Extrapolación flat al final y al inicio
    s = s.bfill().ffill()
    return s.reindex(target_dates)


def theta_series(
    prices_df: pd.DataFrame,
    stocks_df: pd.DataFrame,
    stock_floor: float,
    stock_stress: float,
    params: ModelParams,
    shock_start: Optional[pd.Timestamp] = None,
) -> pd.DataFrame:
    """θ implícito a lo largo del tiempo desde series alineadas.

    prices_df: columnas ['date', 'price'].
    stocks_df: columnas ['date', 'stock_mb'] (mensual o cualquier frecuencia).
    shock_start: fechas anteriores se omiten (modelo no aplica pre-shock).

    Retorna DataFrame con columnas ['date', 'price', 'stock_mb', 'h',
    'p_classical', 'p_run', 'q', 'p_composite', 'theta', 'in_range'].
    """
    df = prices_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if shock_start is not None:
        df = df[df["date"] >= pd.Timestamp(shock_start)].reset_index(drop=True)

    # Interpolación de stocks
    stocks_interp = interpolate_stocks(stocks_df, pd.DatetimeIndex(df["date"]))
    df["stock_mb"] = stocks_interp.values

    # Cómputo por fila (vectorizable a futuro si hace falta velocidad)
    results = []
    for _, row in df.iterrows():
        r = theta_from_observation(
            price_observed=float(row["price"]),
            stock=float(row["stock_mb"]),
            stock_floor=stock_floor,
            stock_stress=stock_stress,
            params=params,
        )
        results.append(r)

    out = df.join(pd.DataFrame(results))
    return out


# ---------------------------------------------------------------------------
# Term structure desde forward curve
# ---------------------------------------------------------------------------

def theta_term_structure_from_forward(
    forward_df: pd.DataFrame,
    snapshot_date: str,
    stock_at_snapshot: float,
    stock_floor: float,
    stock_stress: float,
    params: ModelParams,
    P_star_open_fn=None,
) -> pd.DataFrame:
    """θ implícito por maturity desde una forward curve.

    Para cada maturity T meses:
      1. Proyecta h(T) integrando dot_R(h) desde h(0) durante T meses
         (placeholder: aproximación lineal, ver TODO).
      2. Computa composite P_modelo(h(T)).
      3. Despeja θ(T) tal que F(0,T) = (1-θ)·P_modelo + θ·P*(h(T)).

    P_star_open_fn(stock) opcional: si se provee, usa el P* variable (Ext 4)
    evaluado en el stock proyectado; si no, usa params.P_star constante.

    TODO: reemplazar el placeholder de proyección lineal por la integración
    real de la ODE de Ext 3 (importar solve_ivp).
    """
    snap = forward_df[forward_df["snapshot_date"] == snapshot_date].copy()
    if snap.empty:
        raise ValueError(f"No hay datos para snapshot {snapshot_date}")

    h_0 = h_from_stock(stock_at_snapshot, stock_floor, stock_stress, params.h_star)

    rows = []
    for _, r in snap.iterrows():
        m = int(r["maturity_month"])
        F = float(r["forward_price"])

        # Placeholder: proyección lineal del stock asumiendo dot_R promedio
        from .core import release_rate
        avg_R = release_rate(h_0, params)  # mb/d
        days = m * 30
        stock_T = max(stock_at_snapshot - avg_R * days, stock_floor + 1.0)
        h_T = h_from_stock(stock_T, stock_floor, stock_stress, params.h_star)

        p_c = P_classical(h_T, params)
        p_r = P_run(h_T, params)
        q = q_run(h_T, params)
        p_composite = (1.0 - q) * p_c + q * p_r

        p_star = P_star_open_fn(stock_T) if P_star_open_fn else params.P_star

        denom = p_composite - p_star
        theta = (p_composite - F) / denom if abs(denom) > 1e-9 else float("nan")

        rows.append({
            "snapshot_date": snapshot_date,
            "maturity_month": m,
            "forward_price": F,
            "stock_projected": stock_T,
            "h_projected": h_T,
            "p_composite": p_composite,
            "p_star_open": p_star,
            "theta": theta,
            "in_range": 0.0 <= theta <= 1.0,
        })

    return pd.DataFrame(rows)
