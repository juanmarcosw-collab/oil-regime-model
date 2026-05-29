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

from scipy.optimize import brentq

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
# Demanda de reposición y P*(Stock) variable (Extensión 4)
# Replicados de app.py para evitar import circular.
# ---------------------------------------------------------------------------

def replenishment_rate(
    stock: float, stock_opt: float, stock_floor: float, R_repl_max: float,
) -> float:
    """Tasa de reposición lineal saturada (Ext 4)."""
    if stock_opt <= stock_floor:
        return 0.0
    gap_norm = (stock_opt - stock) / (stock_opt - stock_floor)
    return R_repl_max * max(0.0, min(1.0, gap_norm))


def P_star_open(R_repl: float, params: ModelParams) -> float:
    """Precio de equilibrio con Ormuz abierto + demanda de reposición."""
    if R_repl <= 0:
        return params.P_star

    def f(P):
        return (
            params.D_0 * (P / params.P_star) ** (-params.eps_d) + R_repl
            - params.D_0 * (P / params.P_star) ** params.eps_s
        )

    return brentq(f, 30, 2000)


def p_star_at_stock(
    stock: float, stock_opt: float | None, stock_floor: float,
    R_repl_max: float | None, params: ModelParams,
) -> float:
    """Helper: si se proveen stock_opt y R_repl_max, retorna P*(Stock)
    con demanda de reposición; sino, retorna params.P_star constante.
    """
    if stock_opt is None or R_repl_max is None:
        return params.P_star
    R = replenishment_rate(stock, stock_opt, stock_floor, R_repl_max)
    return P_star_open(R, params)


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
    stock_opt: float | None = None,
    R_repl_max: float | None = None,
) -> dict:
    """θ implícito y diagnósticos para una observación (P, Stock).

    Si se proveen stock_opt y R_repl_max, usa P*(Stock) variable con demanda
    de reposición (Ext 4) como denominador del despeje — consistente con la
    métrica puntual del app. Sin esos parámetros, usa P* = 70 constante.

    Retorna:
        dict con h, p_c, p_r, q, p_composite, p_star, theta, in_range.
    """
    h = h_from_stock(stock, stock_floor, stock_stress, params.h_star)
    p_c = P_classical(h, params)
    p_r = P_run(h, params)
    q = q_run(h, params)
    p_composite = (1.0 - q) * p_c + q * p_r
    p_star = p_star_at_stock(stock, stock_opt, stock_floor, R_repl_max, params)

    # Despeje de θ desde P_mercado = (1-θ)·P_composite + θ·P*(Stock)
    denom = p_composite - p_star
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
        "p_star": p_star,
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
    stock_opt: float | None = None,
    R_repl_max: float | None = None,
) -> pd.DataFrame:
    """θ implícito a lo largo del tiempo desde series alineadas.

    prices_df: columnas ['date', 'price'].
    stocks_df: columnas ['date', 'stock_mb'] (mensual o cualquier frecuencia).
    shock_start: fechas anteriores se omiten (modelo no aplica pre-shock).
    stock_opt, R_repl_max: si se proveen, el despeje de θ usa P*(Stock) variable
        (Ext 4) en vez de P* = 70 constante — consistente con la métrica del app.

    Retorna DataFrame con columnas ['date', 'price', 'stock_mb', 'h',
    'p_classical', 'p_run', 'q', 'p_composite', 'p_star', 'theta', 'in_range'].
    """
    df = prices_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    if shock_start is not None:
        df = df[df["date"] >= pd.Timestamp(shock_start)].reset_index(drop=True)

    stocks_interp = interpolate_stocks(stocks_df, pd.DatetimeIndex(df["date"]))
    df["stock_mb"] = stocks_interp.values

    results = []
    for _, row in df.iterrows():
        r = theta_from_observation(
            price_observed=float(row["price"]),
            stock=float(row["stock_mb"]),
            stock_floor=stock_floor,
            stock_stress=stock_stress,
            params=params,
            stock_opt=stock_opt,
            R_repl_max=R_repl_max,
        )
        results.append(r)

    out = df.join(pd.DataFrame(results))
    return out


# ---------------------------------------------------------------------------
# Term structure desde forward curve
# ---------------------------------------------------------------------------

def interpolate_forward_to_daily(
    forwards_long_df: pd.DataFrame,
    snapshot_date: str,
    anchor_price: float | None = None,
    shift_months: int = 1,
) -> pd.DataFrame:
    """Interpola una forward curve discreta a frecuencia diaria, mapeada al
    calendario del M1 rolling (cada delivery_date se adelanta `shift_months`
    meses para representar "el precio del contrato que será M1 en esa fecha").

    Justificación del shift: la serie histórica M1 (rolling front-month)
    representa, en cada día, el precio del contrato más cercano a expirar
    (~1 mes adelantado). Su extensión natural hacia el futuro NO es el precio
    del contrato del mismo mes (que sería el M0 que no existe), sino el
    precio del contrato cuya entrega ocurre ~1 mes después. Adelantar las
    fechas de la forward curve por shift_months alinea ambas series.

    Si `anchor_price` se provee, se inserta un punto en `snapshot_date` con
    ese precio para empalmar sin gap con la serie histórica.

    Retorna DataFrame con columnas ['date', 'price'] diario.
    """
    snap_ts = pd.Timestamp(snapshot_date)
    df = forwards_long_df[forwards_long_df["observation_date"] == snap_ts]
    if df.empty:
        df = forwards_long_df[forwards_long_df["observation_date"] <= snap_ts]
        if df.empty:
            raise ValueError(f"No forward data en o antes de {snapshot_date}")
        latest = df["observation_date"].max()
        df = df[df["observation_date"] == latest]
        snap_ts = latest

    df = df.sort_values("delivery_month")

    # Shift de fechas: delivery_T -> (delivery_T − shift_months meses).
    shifted = (
        pd.to_datetime(df["delivery_month"].values)
        - pd.DateOffset(months=shift_months)
    )

    index = list(shifted)
    values = df["price"].astype(float).tolist()
    if anchor_price is not None and snap_ts < min(index):
        # Anchor en snap_ts para conectar con la serie histórica.
        index = [snap_ts] + index
        values = [float(anchor_price)] + values

    start = min(index)
    end = max(index)
    daily_dates = pd.date_range(start, end, freq="D")

    series = pd.Series(index=pd.DatetimeIndex(index), data=values)
    combined = series.reindex(series.index.union(daily_dates)).sort_index()
    interp = combined.interpolate(method="time")
    daily = interp.reindex(daily_dates)
    return pd.DataFrame({"date": daily_dates, "price": daily.values})


def theta_forward_extension(
    forwards_long_df: pd.DataFrame,
    snapshot_date: str,
    stock_at_snapshot: float,
    stock_floor: float,
    stock_stress: float,
    params,
    shift_months: int = 1,
    stock_opt: float | None = None,
    R_repl_max: float | None = None,
) -> pd.DataFrame:
    """Serie diaria de θ implícito extendido por maturity del forward curve,
    mapeada al calendario del M1 rolling (delivery shifteado `shift_months`).

    Para cada delivery_month del snapshot:
      1. Computa el período entre snapshot y (delivery − shift_months meses).
      2. Proyecta el stock a ese momento (release × días) acotado al floor.
      3. Computa composite P_modelo a ese stock.
      4. Despeja θ tal que F(snapshot, delivery) = (1-θ) P_modelo + θ P*.
      5. Plotea el θ en la fecha shifteada (consistente con M1 rolling).

    Luego interpola la serie de θ a frecuencia diaria.
    """
    snap_ts = pd.Timestamp(snapshot_date)
    df = forwards_long_df[forwards_long_df["observation_date"] == snap_ts]
    if df.empty:
        df = forwards_long_df[forwards_long_df["observation_date"] <= snap_ts]
        if df.empty:
            raise ValueError(f"No forward data en o antes de {snapshot_date}")
        latest = df["observation_date"].max()
        df = df[df["observation_date"] == latest]
        snap_ts = latest

    df = df.sort_values("delivery_month").reset_index(drop=True)

    from .core import release_rate, P_classical, P_run, q_run

    avg_R = release_rate(
        h_from_stock(stock_at_snapshot, stock_floor, stock_stress, params.h_star),
        params,
    )

    points = []
    for _, r in df.iterrows():
        delivery = pd.Timestamp(r["delivery_month"])
        plot_date = delivery - pd.DateOffset(months=shift_months)
        days = max((plot_date - snap_ts).days, 0)
        stock_T = max(stock_at_snapshot - avg_R * days, stock_floor + 1.0)
        h_T = h_from_stock(stock_T, stock_floor, stock_stress, params.h_star)
        p_c = P_classical(h_T, params)
        p_r = P_run(h_T, params)
        q = q_run(h_T, params)
        composite = (1 - q) * p_c + q * p_r

        # P*(Stock_T) variable si se proveen stock_opt y R_repl_max (Ext 4)
        p_star_T = p_star_at_stock(
            stock_T, stock_opt, stock_floor, R_repl_max, params,
        )

        denom = composite - p_star_T
        theta_val = (composite - float(r["price"])) / denom if abs(denom) > 1e-9 else float("nan")
        points.append((plot_date, theta_val))

    dates_arr = pd.DatetimeIndex([p[0] for p in points])
    series = pd.Series(index=dates_arr, data=[p[1] for p in points])
    daily_dates = pd.date_range(dates_arr.min(), dates_arr.max(), freq="D")
    combined = series.reindex(series.index.union(daily_dates)).sort_index()
    interp = combined.interpolate(method="time").reindex(daily_dates)
    return pd.DataFrame({"date": daily_dates, "theta": interp.values})


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
