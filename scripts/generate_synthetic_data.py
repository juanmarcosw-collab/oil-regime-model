"""
Genera datasets sintéticos plausibles para testing de la capa de inferencia.

Series generadas:
  - Brent spot diario (feb 2026 - may 2026), reproduciendo la trayectoria
    estilizada del shock: jump al inicio, persistencia, oscilación con noise.
  - Inventarios globales mensuales (ene 2026 - may 2026), con drenaje
    progresivo desde 8.150 hasta ~7.950 mb.
  - Forward curves a tres fechas snapshot (mar, abr, may).

Outputs en data/synthetic/.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "synthetic"


def generate_brent_spot(seed: int = 42) -> pd.DataFrame:
    """Brent spot diario feb-may 2026 con dinámica estilizada."""
    rng = np.random.default_rng(seed)

    dates = pd.date_range("2026-02-01", "2026-05-30", freq="D")
    n = len(dates)
    prices = np.empty(n)

    # Pre-shock baseline ~70 hasta el 12-feb-2026 (cierre de Ormuz)
    shock_start_idx = (pd.Timestamp("2026-02-12") - dates[0]).days

    # Pre-shock: 68-72 con noise
    pre_shock = 70 + rng.normal(0, 1.0, shock_start_idx)
    prices[:shock_start_idx] = pre_shock

    # Post-shock: jump inicial a ~95, suba gradual hacia ~115 con noise
    post_n = n - shock_start_idx
    trend = np.linspace(95, 115, post_n)
    noise = rng.normal(0, 3.0, post_n)
    # Reversion suave para que no sea pura tendencia
    post_shock = trend + noise
    # Smoothing para que no haya saltos diarios extremos
    for i in range(1, post_n):
        post_shock[i] = 0.7 * post_shock[i] + 0.3 * post_shock[i - 1]
    prices[shock_start_idx:] = post_shock

    return pd.DataFrame({"date": dates, "price": prices.round(2)})


def generate_stocks_monthly() -> pd.DataFrame:
    """Stocks mensuales con drenaje progresivo durante el shock."""
    dates = pd.to_datetime([
        "2026-01-31",
        "2026-02-28",
        "2026-03-31",
        "2026-04-30",
    ])
    stocks_mb = [8150, 8090, 8020, 7951]
    return pd.DataFrame({"date": dates, "stock_mb": stocks_mb})


def generate_forward_curves(seed: int = 43) -> pd.DataFrame:
    """Snapshots de forward curve Brent en tres fechas con backwardation."""
    rng = np.random.default_rng(seed)

    rows = []
    snapshots = {
        "2026-03-15": {"spot": 102, "long_end": 78},
        "2026-04-15": {"spot": 110, "long_end": 76},
        "2026-04-30": {"spot": 114, "long_end": 76},
    }
    for snap_date, levels in snapshots.items():
        # Backwardation: caída desde spot al long-end, con noise
        spot, long_end = levels["spot"], levels["long_end"]
        # Curva tipo exponencial decay
        x = np.arange(1, 13)  # maturities 1..12 meses
        curve = long_end + (spot - long_end) * np.exp(-0.20 * (x - 1))
        curve += rng.normal(0, 0.5, len(x))
        for m, p in zip(x, curve):
            rows.append({
                "snapshot_date": snap_date,
                "maturity_month": int(m),
                "forward_price": round(float(p), 2),
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    brent = generate_brent_spot()
    brent.to_csv(OUT_DIR / "brent_spot_daily.csv", index=False, date_format="%Y-%m-%d")

    stocks = generate_stocks_monthly()
    stocks.to_csv(OUT_DIR / "stocks_monthly.csv", index=False, date_format="%Y-%m-%d")

    forwards = generate_forward_curves()
    forwards.to_csv(OUT_DIR / "brent_forward_curves.csv", index=False)

    print(f"Generated:")
    print(f"  brent_spot_daily.csv      ({len(brent)} rows)")
    print(f"  stocks_monthly.csv        ({len(stocks)} rows)")
    print(f"  brent_forward_curves.csv  ({len(forwards)} rows)")
    print(f"Output dir: {OUT_DIR}")


if __name__ == "__main__":
    main()
