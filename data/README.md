# Data folder

## Estructura

```
data/
├── README.md             # Este archivo
├── synthetic/            # Datos sintéticos para testing (committed)
│   ├── brent_spot_daily.csv
│   ├── stocks_monthly.csv
│   └── brent_forward_curves.csv
├── processed/            # Sincronizados del master pipeline (committed)
│   ├── prices_long.csv            ← FRED Brent/WTI/Dubai daily+monthly
│   ├── brent_constant_maturity.csv ← Bloomberg M1/M3/M6/M12/M24
│   ├── brent_futures_long.csv      ← Bloomberg forward curves (long format)
│   ├── omr_total_global_inventories.csv ← IEA OMR mensual extraído
│   └── pink_sheet_oil_prices.csv   ← World Bank Pink Sheet
└── raw/                  # Datos crudos (gitignored)
    └── ...               # PDFs, Excels originales, etc.
```

## De dónde vienen los datos procesados

El pipeline maestro vive en `bcch-mercado-petroleo` (el repo padre). Allí:

- `data/raw/` agrupa los archivos crudos por fuente: `fred/`, `bloomberg/`,
  `iea/`, `opec/`, `jodi/`, etc.
- `src/loaders/load_<fuente>.py` son scripts que normalizan cada fuente y
  producen los CSVs limpios en `data/processed/`.

Para sincronizar al subproject (este folder):

```powershell
& .\.venv\Scripts\python.exe scripts\sync_data_from_master.py
```

Eso copia los CSVs procesados relevantes desde el padre a este `processed/`.
El dashboard de Streamlit Cloud lee de acá, así que **el subfolder debe estar
commiteado y actualizado** para que el deploy tenga datos al día.

## Workflow de actualización

```
[Excel/PDF crudo nuevo]                    [Datos viejos en raw/]
       │
       ▼
[dropear en padre data/raw/<fuente>/]
       │
       ▼
[correr loader en padre: src/loaders/load_<fuente>.py]
       │
       ▼
[generar nuevos CSVs en padre data/processed/]
       │
       ▼
[correr sync_data_from_master.py en este subproject]
       │
       ▼
[git commit de app_modelo_runs/data/processed/]
       │
       ▼
[push → Streamlit Cloud rebuild → dashboard al día]
```

## Cómo agregar nueva data al pipeline

1. **Si la fuente ya tiene loader** (FRED, Bloomberg, OPEC, JODI, STEO, Pink
   Sheet): reemplazá el archivo crudo en el padre y re-corré el loader.
2. **Si es una fuente nueva**: escribir un loader en `src/loaders/` del padre
   siguiendo el patrón de los existentes, generar CSV en `data/processed/`, y
   agregarlo a `SYNC_FILES` en `scripts/sync_data_from_master.py`.

## Sintéticos

`data/synthetic/` mantiene datos generados con `scripts/generate_synthetic_data.py`
para que el dashboard funcione sin el master pipeline (e.g. ambiente de
desarrollo limpio o demo). El selector "Sintética" del sidebar los usa.

## .gitignore

- `data/raw/` está excluido del git (archivos del banco no van al repo público).
- `data/processed/` y `data/synthetic/` se commitean.
