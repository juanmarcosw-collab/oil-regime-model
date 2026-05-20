# Modelo Estructural del Precio del Petróleo bajo Stress de Oferta

Explorador interactivo del modelo teórico-estructural desarrollado por la División de Política Monetaria del Banco Central de Chile (mayo 2026).

## Descripción

El modelo articula dos regímenes explícitos en el plano (h, P):

1. **Régimen clásico**: equilibrio de storage theory clásico donde el precio se determina por la oferta y demanda con liberación normal de inventarios.

2. **Régimen de run**: pánico coordinado donde los tenedores de inventario retiran masivamente, anticipando precios futuros mayores. La transición entre regímenes ocurre probabilísticamente via un global game à la Goldstein-Pauzner.

El precio observado se modela como un promedio ponderado de los dos regímenes, con peso dado por la probabilidad de cada uno. Esto permite cuantificar la incertidumbre sobre cuál régimen se materializa.

El parámetro **θ** (probabilidad implícita de normalización) captura el wedge entre el precio predicho por el modelo y el precio de mercado, interpretable como las expectativas del mercado sobre resolución del shock.

## Instalación

### Con `uv` (recomendado)

```bash
uv sync
```

### Con `pip`

```bash
pip install -e .
```

### Con `poetry`

```bash
poetry install
```

## Uso

Para ejecutar la app interactiva:

```bash
uv run streamlit run app/app.py
```

La app se abrirá en `http://localhost:8501`. Desde allí puedes:

- Mover sliders para variar los parámetros del modelo.
- Ver en tiempo real cómo cambian las curvas P_C(h), P_R(h) y P(h).
- Consultar los valores notables del modelo (cap, piso, probabilidad de run, θ implícito).
- Explorar secciones expandibles con ecuaciones, funciones constituyentes y referencias bibliográficas.

## Estructura del proyecto

```
oil_regime_model/
├── README.md                          # Este archivo
├── pyproject.toml                     # Configuración de dependencias
├── model/
│   ├── __init__.py                    # Exports limpios
│   ├── core.py                        # Implementación del modelo (P_C, P_R, q, P)
│   ├── calibration.py                 # Parámetros por defecto con docstrings
│   └── empirics.py                    # Funciones derivadas (θ, P_cap, P_floor)
├── app/
│   └── app.py                         # Aplicación Streamlit principal
├── tests/
│   └── test_model.py                  # Tests unitarios del modelo
└── docs/
    └── modelo_petroleo.pdf            # Referencia: documento de trabajo BCCh
```

## Calibración

Los valores por defecto corresponden a la calibración reportada en el documento de trabajo BCCh (mayo 2026, sección 8):

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **P\*** | 70 USD/bbl | Precio pre-shock (Brent, feb-2026) |
| **D₀** | 104 mb/d | Demanda mundial pre-guerra |
| **S_f,0** | 95 mb/d | Oferta durante shock (Ormuz cerrado) |
| **ε_d** | 0.05 | Elasticidad demanda (short-run) |
| **ε_s** | 0.05 | Elasticidad oferta (short-run) |
| **R_max** | 6 mb/d | Capacidad máx. releases coordinados |
| **h_R** | 0.12 | Saturación del release |
| **h\*** | 0.30 | Umbral del global game |
| **σ** | 0.08 | Dispersión de señales |

Con estos valores:
- **P_cap** (h→0) ≈ 173 USD/bbl
- **P_floor** (h grande) ≈ 95 USD/bbl

## Pruebas

Para ejecutar los tests unitarios:

```bash
uv run pytest tests/
```

O con cobertura:

```bash
uv run pytest tests/ --cov=model
```

Los tests verifican propiedades matemáticas clave:
- P_C(0) ≈ P_cap
- P_C(∞) ≈ P_floor
- P_R(0) = P_C(0)
- q(h*) = 0.5
- θ > 0 cuando P_modelo > P_observado

## Referencias

**Documento de trabajo:**

Banco Central de Chile, División de Política Monetaria (2026). "Modelo estructural del precio del petróleo bajo stress de oferta: Marco analítico para evaluar el riesgo de transición a régimen de pánico coordinado." *Documento de trabajo, versión 1.*

**Fuentes teóricas clave:**

- **Caldara, Cavallo & Iacoviello (2019).** Oil Price Elasticities and Oil Price Fluctuations. *Journal of Monetary Economics*, 103, 1-20.
- **Deaton & Laroque (1992).** On the Behaviour of Commodity Prices. *Review of Economic Studies*, 59(1), 1-23.
- **Diamond & Dybvig (1983).** Bank Runs, Deposit Insurance, and Liquidity. *Journal of Political Economy*, 91(3), 401-419.
- **Goldstein & Pauzner (2005).** Demand-Deposit Contracts and the Probability of Bank Runs. *Journal of Finance*, 60(3), 1293-1327.
- **Hamilton (2009).** Understanding Crude Oil Prices. *Energy Journal*, 30(2), 179-206.
- **Kilian (2009).** Not All Oil Price Shocks Are Alike. *American Economic Review*, 99(3), 1053-1069.
- **Morris & Shin (1998).** Unique Equilibrium in a Model of Self-Fulfilling Currency Attacks. *AER*, 88(3), 587-597.
- **Pindyck (2001).** The Dynamics of Commodity Spot and Futures Markets: A Primer. *Energy Journal*, 22(3), 1-29.
- **Routledge, Seppi & Spatt (2000).** Equilibrium Forward Curves for Commodities. *Journal of Finance*, 55(3), 1297-1338.

## Posibles extensiones

- **Dinámica**: simular la trayectoria h_t dada una condición inicial y un ritmo de drenado. Permitir contrafactuales (¿qué si Ormuz sigue cerrado X meses más?).
- **Calibración estructural**: usar episodios históricos para estimar h* vía maximum likelihood o método de momentos.
- **Multi-país**: extender al setup multi-origen del modelo BCCh.
- **Datos en vivo**: conectar a APIs de EIA (inventarios) y mercado de futuros (precios spot).

## Licencia

Este trabajo está licenciado bajo CC-BY-4.0.

## Contacto

División de Política Monetaria  
Banco Central de Chile  
[politicamonetaria@bcentral.cl](mailto:politicamonetaria@bcentral.cl)

---

**Nota**: Este es un documento de investigación. Las opiniones expresadas son de los autores y no necesariamente reflejan la posición oficial del Banco Central de Chile.
