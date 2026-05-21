# Claude Code: Especificación de proyecto

## Resumen

Construí en Claude Code un **explorador interactivo** del modelo estructural del precio del petróleo bajo stress de oferta. El modelo está descrito en detalle en el PDF adjunto (`modelo_petroleo.pdf`); este documento es el spec para Claude Code.

El proyecto debe ser:

- Una aplicación **Streamlit** (Python, browser-based).
- Con sliders para los parámetros clave del modelo.
- Que muestre en tiempo real la figura $(h, P)$ con las tres curvas.
- Que reporte los valores clave (cap, piso, composite a $h$ actual, $\theta$ implícito).
- Bien estructurada para extensiones futuras (modelo dinámico, calibración estructural).

## Prompt sugerido para Claude Code

Pegale a Claude Code el bloque de abajo. Adjuntá también el archivo `modelo_petroleo.pdf` y los archivos `model_core.py` y `app.py` (que detallo más abajo) como punto de partida.

---

```
Quiero crear un proyecto Python que implemente y permita explorar interactivamente
el modelo estructural del precio del petróleo descrito en el PDF adjunto
`modelo_petroleo.pdf` (mayo 2026).

El modelo articula dos regímenes (clásico y run) en el plano (h, P), con probabilidad
de régimen derivada de un global game à la Goldstein-Pauzner. Las ecuaciones, parámetros
y calibración están en las secciones 4-8 del PDF.

Quiero que el proyecto tenga:

1. **Estructura de repositorio:**

   ```
   oil_regime_model/
   ├── README.md                  # Instrucciones de instalación y uso
   ├── pyproject.toml             # Dependencias (streamlit, numpy, scipy, matplotlib)
   ├── model/
   │   ├── __init__.py
   │   ├── core.py                # Implementación del modelo (P_C, P_R, P composite, q)
   │   ├── calibration.py         # Defaults de parámetros con docstrings citando el PDF
   │   └── empirics.py            # Funciones auxiliares para computar θ implícito, etc.
   ├── app/
   │   ├── app.py                 # Aplicación Streamlit principal
   │   └── plotting.py            # Funciones de plotting reutilizables (matplotlib)
   ├── tests/
   │   └── test_model.py          # Tests unitarios básicos
   └── docs/
       └── model_description.pdf  # Copia del PDF de referencia
   ```

2. **Interfaz Streamlit (`app/app.py`):**

   La página principal debe tener:

   - **Sidebar** con sliders/inputs para los siguientes parámetros, agrupados en secciones:
   
     - *Parámetros estructurales* (sección 4 del PDF): ε_d, ε_s, P*, D_0, S_f0
     - *Función de release* (sección 4.2): R_max, h_R
     - *Régimen de run* (sección 6): μ, δ_0
     - *Global game* (sección 6.3): h*, σ
     - *Observación actual* (sección 10): h_actual, P_observado
   
     Cada slider debe tener rango razonable y default igual a la calibración del PDF.
   
   - **Área principal:**
     
     - Figura del modelo en el plano (h, P), generada con matplotlib, con las tres curvas (P_C, P_R, P composite), banda de fragilidad alrededor de h*, líneas de referencia para P_cap, piso, y P*, marcador del punto observado actual.
     
     - Tabla de valores clave:
       - P_piso (h grande, release máximo)
       - P_cap (h=0, sin release)
       - P_C(h_actual), P_R(h_actual), q(h_actual)
       - P composite del modelo a h_actual
       - θ implícito (probabilidad de normalización)
   
   - **Sección expandible** "Detalles del modelo" con las ecuaciones renderizadas (usar `st.latex`).
   
   - **Sección expandible** "Sensibilidad" que permita ver cómo cambia el cap o el composite ante variaciones de un parámetro a la vez.

3. **Implementación del modelo (`model/core.py`):**

   Funciones principales:
   
   - `release_rate(h, R_max, h_R)` → `dot_R`
   - `delta_run(h, delta_0, R_max, h_R)` → demanda especulativa
   - `P_classical(h, params)` → P_C(h), solver con brentq
   - `P_run(h, params)` → P_R(h), solver con brentq
   - `q_run(h, h_star, sigma)` → probabilidad de régimen run (CDF normal)
   - `P_composite(h, params)` → precio observado bajo modelo estático
   - `theta_implicit(P_model, P_observed, P_star)` → probabilidad implícita de normalización

   El módulo debe estar bien documentado, con docstrings que referencien las secciones del PDF.

4. **Tests unitarios (`tests/test_model.py`):**

   - P_C(h=0) ≈ P_cap calculado analíticamente
   - P_C(h→∞) ≈ piso calculado analíticamente
   - P_R(h=0) = P_C(h=0) (convergencia en stockout)
   - q(h*) = 0.5 (probabilidad en el umbral)
   - θ implícito > 0 cuando P_observado < P_model

5. **README.md** con:
   
   - Descripción breve del modelo
   - Instrucciones de instalación (preferentemente con `uv` o `poetry`)
   - Comando para correr la app
   - Referencia al PDF y a las fuentes literarias

Empezá por implementar `model/core.py` y `app/app.py`. Los archivos que adjunto
(`model_core.py` y `app.py`) son un esqueleto funcional que reproduce la calibración
del PDF; usalos como punto de partida pero refactorizá según la estructura que pido.

Una vez funcionando, agregá tests, y luego implementá las secciones expandibles
(detalles del modelo, sensibilidad).

Importante: la app es una herramienta de investigación para un macroeconomista no
especialista en finanzas de commodities. La interfaz debe ser pedagógica: cada
parámetro debe tener un tooltip que explique brevemente qué representa y de dónde
viene el valor por defecto.
```

---

## Cómo correr la app después

Una vez Claude Code haya armado todo:

```bash
cd oil_regime_model
uv sync  # o poetry install
uv run streamlit run app/app.py
```

La app se abrirá en `http://localhost:8501`. Vas a poder mover sliders y ver cómo cambia la figura en tiempo real.

## Posibles extensiones (futuro)

Para iteraciones posteriores, considerá:

- **Extensión dinámica**: simular la trayectoria $h_t$ dada una condición inicial y un ritmo de drenado. Permitir contrafactuales (qué pasa si Ormuz sigue cerrado X meses más).
- **Calibración estructural**: usar episodios históricos (1990, 2008, 2022) para calibrar $h^*$ vía maximum likelihood o método de momentos.
- **Modelo multi-país**: extender al setup multi-origen.
- **Integración con datos en vivo**: conectar a la API de la EIA para inventarios y a alguna API de mercado para precios spot.
