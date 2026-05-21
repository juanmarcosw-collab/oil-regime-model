# Extensiones al modelo (v1 → v2)

Este documento describe las extensiones al modelo estructural del precio del
petróleo bajo stress de oferta respecto a la versión 1 del paper original
(mayo 2026). Cada sección detalla la motivación, la formalización y las
implicaciones de la extensión correspondiente.

---

## Extensión 1 — Parametrización dual de θ

### Motivación

El paper original define θ implícito por despeje desde el precio observado.
Dadas `P_mercado` y `P(h)` del modelo, se resuelve

$$\theta = \frac{P(h) - P_{\text{mercado}}}{P(h) - P^{\ast}}$$

interpretado como la probabilidad implícita de normalización que el mercado
está priciendo. Esta dirección es **diagnóstica**: lee el wedge y lo traduce
a θ.

### Formalización

La extensión usa la **dirección inversa**: dado un θ exógeno (que puede
representar un escenario, una creencia agregada, o un supuesto de stress
test), se computa el precio esperado por el mercado:

$$P_{\rm esp}(h) = (1 - \theta) \cdot P(h) + \theta \cdot P^{\ast}(h)$$

### Uso

Permite responder preguntas del tipo "si el mercado pricea θ = 0,4, ¿qué
precio debería observarse a h actual?" — útil para análisis contrafactual y
sensibilidad. Las dos direcciones conviven: θ implícito como output
diagnóstico y θ exógeno como input exploratorio.

---

## Extensión 2 — Mapeo lineal entre stock observado y h

### Motivación

El paper trata `h` como variable abstracta de "buffer slack agregado". Para
anclarlo a un observable empírico, lo conectamos al **Total Global Observed
Inventories** que publica la IEA en su Oil Market Report (OMR).

### Formalización

Calibración lineal anclada en dos thresholds operacionales de JPMorgan:

- Stock_floor (≈ 6.800 mb) → h = 0
- Stock_stress (≈ 7.600 mb) → h = h\*

$$h(\text{Stock}) = h^* \cdot
  \frac{\text{Stock} - \text{Stock}_{\rm floor}}
       {\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}$$

Para abril 2026 (Stock = 7.951 mb, IEA OMR), esto da h ≈ 0.43.

### Justificaciones

- **Operational floor (JPM)**: nivel mínimo bajo el cual la cadena
  refinería-logística pierde flexibilidad. Conceptualmente "no hay colchón"
  → h = 0.
- **Stress threshold (JPM)**: nivel a partir del cual el run-risk se activa
  empíricamente. Coincide en interpretación con el umbral teórico del global
  game, h\*.
- **Lineal**: parsimonia y interpretabilidad. Una forma no-lineal (e.g.
  cóncava hacia el floor) podría motivarse si se quiere capturar "stress
  acelerado" cerca del piso, pero requiere identificación empírica adicional.

---

## Extensión 3 — Dinámica temporal P(t) bajo shock persistente

### Motivación

El modelo original es **estático**: para un h dado predice P(h). Para uso
operativo (timing de hitos, proyecciones de precio) se necesita una versión
dinámica.

### Formalización

Asumiendo que el shock se mantiene (Ormuz cerrado), el stock se drena según
la función de release del modelo, ahora aplicada al stock:

$$\frac{d\,\text{Stock}}{dt} = -\dot R\!\left(h(\text{Stock})\right)$$

donde:

- `dot_R` es la función Michaelis-Menten del paper original
  ($R_{\max} \cdot h / (h + h_R)$).
- `h(Stock)` es el mapeo de la Extensión 2.

Integración numérica con condición inicial `Stock_0 = 7.951 mb` al
30-abr-2026. Horizonte default: 365 días.

Para cada `t` se evalúan `P_C(t)`, `P_R(t)`, `P(t)` composite y `P*(t)`.

### Outputs accionables

- Trayectoria del precio bajo no-resolución.
- Fechas de cruce de thresholds: stress (run-risk se activa) y floor (límite
  operacional).

### Supuestos clave

- **Shock persistente**: no se modela reabastecimiento durante la
  integración.
- **dot_R(h) constante en el tiempo**: la función de release no se modifica
  con el avance del shock.
- **Demanda y oferta de flujo estacionarias.**

### Extensiones futuras posibles

- Shock con duración finita estocástica.
- Reabastecimiento parcial durante el shock (releases retornan parte del
  stock).
- Función de release tiempo-dependiente (e.g. fatiga política reduce R_max).

---

## Extensión 4 — Demanda de reposición: P\* deja de ser constante

### Motivación

El paper trata P\* como constante (precio pre-shock, 70 USD/bbl en la
calibración). Esto asume que si Ormuz se reabre, el mercado retorna
inmediatamente al equilibrio pre-shock `D = S_open`.

En la práctica, si Ormuz se reabre con inventarios por debajo del nivel
óptimo, hay **demanda extra para reponer**. Esta demanda no se desactiva con
la reapertura — al contrario, se gatilla con ella, porque solo tiene sentido
reponer cuando la oferta es nuevamente abundante. Esta demanda empuja P\*
por encima del precio pre-shock cuanto más bajos estén los stocks al momento
de la apertura.

### Formalización

Sea `Stock_opt = 8.200 mb` el nivel objetivo de inventarios (calibrado como
el nivel alcanzado en enero 2026 tras la acumulación de 2025).

**Tasa de reposición** (lineal saturada):

$$R_{\rm repl}(\text{Stock}) = R_{\rm repl,\max} \cdot
  \text{clamp}\!\left(
    \frac{\text{Stock}_{\rm opt} - \text{Stock}}
         {\text{Stock}_{\rm opt} - \text{Stock}_{\rm floor}},
    0,\ 1
  \right)$$

Propiedades:

- Stock ≥ Stock_opt: R_repl = 0 (no hay necesidad de reponer).
- Stock = Stock_floor: R_repl = R_repl,max (saturación).
- Lineal y continua en el rango intermedio.

**Equilibrio "Ormuz abierto" con reposición:**

$$D(P^{\ast}) + R_{\rm repl}(\text{Stock}) = S_{\rm open}(P^{\ast})$$

donde D y S_open son las curvas con elasticidad constante calibradas en el
paper original (S_open evaluada con la oferta plena pre-shock, no la oferta
reducida durante el shock).

Solución cerrada implícita; en la práctica se resuelve numéricamente por
root-finding. En `R_repl = 0` se recupera `P* = P*_ref` del paper original.

### Calibración default

- **Stock_opt = 8.200 mb** (post-acumulación 2025).
- **R_repl,max = 5,0 mb/d** (saturación al floor). Con stock observado abril
  2026 da R_repl ≈ 0,9 mb/d, consistente con estimaciones de mercado para
  una reapertura en mayo/junio.
- Con ε_d = ε_s = 0,05, cada 1 mb/d de reposición sube P\* unos ~7 USD/bbl.

### Implicaciones para el resto del modelo

1. La curva `P*(h)` deja de ser horizontal y tiene **pendiente positiva
   hacia stocks bajos** (a menor h, mayor R_repl, mayor P\*).

2. El precio esperado se actualiza a:

   $$P_{\rm esp}(h) = (1 - \theta) \cdot P(h) + \theta \cdot P^{\ast}(h)$$

   con `P*(h)` variable. Ambos lados del promedio dependen de h.

3. θ implícito se recalcula contra `P*(h_actual)` en lugar de `P*_ref`
   constante:

   $$\theta_{\rm imp} = \frac{P(h) - P_{\text{mercado}}}{P(h) - P^{\ast}(h)}$$

### Interpretación económica

Esta extensión hace explícito un mecanismo que el paper original abstraía:
el "fin del shock" no es retorno instantáneo al equilibrio pre-shock, sino
transición a un nuevo equilibrio temporario donde la oferta plena está
parcialmente "comprometida" con la reposición de stocks. **El piso de
precio post-shock es endógeno al estado de los inventarios al momento de la
resolución.**

### Limitaciones

- `R_repl,max` es exógeno; no se deriva de microfundamentos de optimización
  inter-temporal de holders.
- El nivel óptimo `Stock_opt` es exógeno; podría endogenizarse vía costos de
  almacenamiento y expectativas de oferta futura.
- La forma funcional lineal es ad-hoc; una forma cóncava o saturada con
  Michaelis-Menten podría capturar saturación más realista de logística
  refinería-transporte.
