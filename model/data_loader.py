"""
Loader para datasets de precios y stocks, soportando múltiples fuentes.

Convenciones de columnas (después de la normalización):
  - Brent spot:     ['date', 'price']
  - Stocks:         ['date', 'stock_mb']
  - Forward curves: ['snapshot_date', 'maturity_month', 'forward_price']

Acepta CSV o Excel. Para Excel se puede indicar sheet/columnas via kwargs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd


# ---------------------------------------------------------------------------
# Lectura de archivos genéricos
# ---------------------------------------------------------------------------

def _read_table(
    path: Union[str, Path],
    sheet_name: Optional[Union[str, int]] = None,
    **kwargs,
) -> pd.DataFrame:
    """Lee CSV o Excel. Detecta por extensión."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No existe: {p}")

    if p.suffix.lower() in (".csv", ".tsv"):
        sep = "\t" if p.suffix.lower() == ".tsv" else ","
        return pd.read_csv(p, sep=sep, **kwargs)
    elif p.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(p, sheet_name=sheet_name, **kwargs)
    else:
        raise ValueError(f"Extensión no soportada: {p.suffix}")


# ---------------------------------------------------------------------------
# Loaders específicos
# ---------------------------------------------------------------------------

def load_brent_spot(
    path: Union[str, Path],
    date_col: str = "date",
    price_col: str = "price",
    sheet_name: Optional[Union[str, int]] = None,
) -> pd.DataFrame:
    """Carga serie de Brent spot. Normaliza columnas a ['date', 'price']."""
    df = _read_table(path, sheet_name=sheet_name)
    df = df.rename(columns={date_col: "date", price_col: "price"})
    df["date"] = pd.to_datetime(df["date"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["date", "price"])
    return df[["date", "price"]].sort_values("date").reset_index(drop=True)


def load_stocks(
    path: Union[str, Path],
    date_col: str = "date",
    stock_col: str = "stock_mb",
    sheet_name: Optional[Union[str, int]] = None,
) -> pd.DataFrame:
    """Carga serie de stocks. Normaliza a ['date', 'stock_mb']."""
    df = _read_table(path, sheet_name=sheet_name)
    df = df.rename(columns={date_col: "date", stock_col: "stock_mb"})
    df["date"] = pd.to_datetime(df["date"])
    df["stock_mb"] = pd.to_numeric(df["stock_mb"], errors="coerce")
    df = df.dropna(subset=["date", "stock_mb"])
    return df[["date", "stock_mb"]].sort_values("date").reset_index(drop=True)


def load_forward_curves(
    path: Union[str, Path],
    snapshot_col: str = "snapshot_date",
    maturity_col: str = "maturity_month",
    price_col: str = "forward_price",
    sheet_name: Optional[Union[str, int]] = None,
) -> pd.DataFrame:
    """Carga forward curves. Normaliza a ['snapshot_date', 'maturity_month', 'forward_price']."""
    df = _read_table(path, sheet_name=sheet_name)
    df = df.rename(columns={
        snapshot_col: "snapshot_date",
        maturity_col: "maturity_month",
        price_col: "forward_price",
    })
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"]).dt.strftime("%Y-%m-%d")
    df["maturity_month"] = pd.to_numeric(df["maturity_month"], errors="coerce").astype("Int64")
    df["forward_price"] = pd.to_numeric(df["forward_price"], errors="coerce")
    df = df.dropna(subset=["snapshot_date", "maturity_month", "forward_price"])
    return df.sort_values(["snapshot_date", "maturity_month"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Loaders convenientes por fuente
# ---------------------------------------------------------------------------

DATA_ROOT = Path(__file__).resolve().parent.parent / "data"


def load_synthetic() -> dict:
    """Carga el dataset sintético completo."""
    syn = DATA_ROOT / "synthetic"
    return {
        "brent_spot": load_brent_spot(syn / "brent_spot_daily.csv"),
        "stocks": load_stocks(syn / "stocks_monthly.csv"),
        "forwards": load_forward_curves(syn / "brent_forward_curves.csv"),
    }


# ---------------------------------------------------------------------------
# Master pipeline (data sincronizada del padre vía sync_data_from_master.py)
# ---------------------------------------------------------------------------

PROCESSED = DATA_ROOT / "processed"


def load_master_brent_spot() -> pd.DataFrame:
    """Brent spot diario desde prices_long.csv (formato largo).

    Filtra series_id == DCOILBRENTEU (FRED daily Brent Europe).
    """
    df = pd.read_csv(PROCESSED / "prices_long.csv", parse_dates=["date"])
    brent = df[df["series_id"] == "DCOILBRENTEU"][["date", "value"]]
    brent = brent.rename(columns={"value": "price"})
    return brent.sort_values("date").reset_index(drop=True)


def load_master_stocks() -> pd.DataFrame:
    """Total Global Observed Inventories mensual desde IEA OMR (2021→2026)."""
    df = pd.read_csv(PROCESSED / "omr_total_global_inventories.csv",
                     parse_dates=["date"])
    df = df.rename(columns={"value_mb": "stock_mb"})
    return df[["date", "stock_mb"]].sort_values("date").reset_index(drop=True)


def load_master_constant_maturity() -> pd.DataFrame:
    """Constant maturity Brent (M1, M3, M6, M12, M24) por día."""
    df = pd.read_csv(PROCESSED / "brent_constant_maturity.csv",
                     parse_dates=["observation_date"])
    return df.sort_values("observation_date").reset_index(drop=True)


def load_master_forwards_long() -> pd.DataFrame:
    """Forward curves en formato largo (snapshot × contrato)."""
    df = pd.read_csv(PROCESSED / "brent_futures_long.csv",
                     parse_dates=["observation_date", "delivery_month"])
    return df.sort_values(["observation_date", "months_to_delivery"]).reset_index(drop=True)


def constant_maturity_to_term_structure(
    cm_df: pd.DataFrame, snapshot_date: str
) -> pd.DataFrame:
    """Extrae la term structure de un día dado desde constant_maturity.

    Retorna DataFrame con columnas ['snapshot_date', 'maturity_month',
    'forward_price'] compatible con theta_term_structure_from_forward.
    """
    target = pd.Timestamp(snapshot_date)
    row = cm_df[cm_df["observation_date"] == target]
    if row.empty:
        # Buscar la fecha más cercana hacia atrás
        row = cm_df[cm_df["observation_date"] <= target].tail(1)
        if row.empty:
            raise ValueError(f"No hay datos en o antes de {snapshot_date}")

    r = row.iloc[0]
    rows = [
        {"snapshot_date": r["observation_date"].strftime("%Y-%m-%d"),
         "maturity_month": m, "forward_price": float(r[f"M{m}"])}
        for m in (1, 3, 6, 12, 24)
    ]
    return pd.DataFrame(rows)


def load_master() -> dict:
    """Carga el dataset completo del master pipeline."""
    return {
        "brent_spot": load_master_brent_spot(),
        "stocks": load_master_stocks(),
        "constant_maturity": load_master_constant_maturity(),
        "forwards_long": load_master_forwards_long(),
    }
