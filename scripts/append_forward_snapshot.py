"""
Appendea el snapshot de forward curve del 27-may-2026 (Datos Juan) al CSV
bloomberg del padre, en el formato wide existente.

Source:  app_modelo_runs/data/raw/Datos Juan - Actualizado 20260527.xlsx
         tab: 'Futuros WTI-Brent', columnas Date/WTI/Brent

Target:  bcch-mercado-petroleo/data/raw/bloomberg/brent_forward_curve_20250421_20260511.csv
         (rename después a ..._20260527 si querés reflejar nuevo rango)

Mapping: cada fila de Datos Juan tiene Date=delivery_month (2026-07-01 etc.)
y precio Brent. El target tiene columnas como 'jul-26', 'ago-26', etc.
"""

from pathlib import Path

import pandas as pd


SOURCE = Path(
    r"C:\Users\juanm\proyectos\bcch-mercado-petroleo\app_modelo_runs\data\raw"
    r"\Datos Juan - Actualizado 20260527.xlsx"
)
TARGET = Path(
    r"C:\Users\juanm\proyectos\bcch-mercado-petroleo\data\raw\bloomberg"
    r"\brent_forward_curve_20250421_20260511.csv"
)
SNAPSHOT_DATE = "27-05-2026"

# Mapping mes-numero -> abreviatura tipo bloomberg
MONTH_ABBREV = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sept", 10: "oct", 11: "nov", 12: "dic",
}


def main() -> None:
    # 1. Leer existente
    existing = pd.read_csv(TARGET, sep=";", encoding="utf-8", dtype=str)
    print(f"Existing: {len(existing)} rows, columns {len(existing.columns)}")

    # 2. Leer snapshot Datos Juan
    snap = pd.read_excel(SOURCE, sheet_name="Futuros WTI-Brent")
    snap["Date"] = pd.to_datetime(snap["Date"])
    snap["contract_label"] = snap["Date"].apply(
        lambda d: f"{MONTH_ABBREV[d.month]}-{str(d.year)[2:]}"
    )

    # 3. Armar fila nueva: para cada columna de contracts en existente,
    #    buscar el precio Brent correspondiente. Si no está en Datos Juan,
    #    queda NaN.
    new_row = {"Date": SNAPSHOT_DATE}
    contract_cols = [c for c in existing.columns if c != "Date"]
    for col in contract_cols:
        match = snap[snap["contract_label"] == col]
        if not match.empty:
            price = float(match["Brent"].iloc[0])
            # Formato del archivo padre: decimal coma
            new_row[col] = f"{price:.2f}".replace(".", ",")
        else:
            new_row[col] = ""

    coverage = sum(1 for c in contract_cols if new_row[c] != "")
    print(f"New row: {coverage} contracts matched (of {len(contract_cols)})")

    # 4. Verificación: chequeo que la fila ya no exista
    if SNAPSHOT_DATE in existing["Date"].values:
        print(f"WARNING: Date {SNAPSHOT_DATE} ya existe en el archivo.")
        print("Abortando para no duplicar.")
        return

    # 5. Appendear y escribir
    new_df = pd.concat([existing, pd.DataFrame([new_row])], ignore_index=True)
    new_df.to_csv(TARGET, sep=";", encoding="utf-8", index=False)
    print(f"Appended. New total: {len(new_df)} rows.")
    print(f"Last 2 rows:")
    print(new_df.tail(2).iloc[:, :8].to_string(index=False))


if __name__ == "__main__":
    main()
