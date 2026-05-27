"""
Sincroniza datasets procesados desde el pipeline padre (bcch-mercado-petroleo)
hacia app_modelo_runs/data/processed/.

Permite que el dashboard tenga datos al día sin depender del path padre en
runtime (importante para Streamlit Cloud, que solo deploy del subfolder).

Para actualizar:
    1. Correr loaders en el padre con datos nuevos (e.g. src/loaders/load_*.py).
    2. Correr este script.
    3. Commitear los CSVs actualizados en app_modelo_runs/data/processed/.

Uso:
    python scripts/sync_data_from_master.py
"""

from __future__ import annotations

import shutil
from pathlib import Path


# Paths
SUBPROJECT_ROOT = Path(__file__).resolve().parent.parent
MASTER_ROOT = SUBPROJECT_ROOT.parent
MASTER_PROCESSED = MASTER_ROOT / "data" / "processed"
MASTER_RAW_IEA = MASTER_ROOT / "data" / "raw" / "iea"
SUB_PROCESSED = SUBPROJECT_ROOT / "data" / "processed"


# Files a sincronizar: (source_path, target_filename)
SYNC_FILES = [
    # Precios spot largos (Brent + WTI + Dubai)
    (MASTER_PROCESSED / "prices_long.csv", "prices_long.csv"),
    # Forward curves
    (MASTER_PROCESSED / "brent_constant_maturity.csv", "brent_constant_maturity.csv"),
    (MASTER_PROCESSED / "brent_futures_long.csv", "brent_futures_long.csv"),
    # Stocks IEA OMR (mensual)
    (MASTER_RAW_IEA / "omr_p50_total_global_inventories.csv", "omr_total_global_inventories.csv"),
    # World Bank Pink Sheet (mensual histórico de Brent)
    (MASTER_PROCESSED / "pink_sheet_oil_prices.csv", "pink_sheet_oil_prices.csv"),
]


def main() -> None:
    SUB_PROCESSED.mkdir(parents=True, exist_ok=True)

    for src, target_name in SYNC_FILES:
        target = SUB_PROCESSED / target_name
        if not src.exists():
            print(f"  SKIP (no existe): {src}")
            continue
        shutil.copy2(src, target)
        size_kb = target.stat().st_size / 1024
        print(f"  OK  {target.name:45s} ({size_kb:.1f} KB)")

    print()
    print(f"Sincronizados en: {SUB_PROCESSED}")


if __name__ == "__main__":
    main()
