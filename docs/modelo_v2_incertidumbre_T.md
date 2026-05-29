# Modelo v2 — Incertidumbre sobre la duración del shock (T)

**Versión:** v2.0.1 — draft inicial con corrección de §2.3-2.4, §4.4, §5.1, §9.1
sobre actualización bayesiana del posterior (mayo 2026).
**Status:** Documento conceptual; pendiente implementación en la app.
**Relación con v1:** complementa, no reemplaza. El v1 conserva valor pedagógico
y como benchmark. Ambos modelos coexisten como pestañas distintas del dashboard.

---

## Resumen ejecutivo

El modelo v1 (paper original) sitúa la incertidumbre relevante sobre el **buffer
agregado h**: los tenedores de inventario reciben señales privadas ruidosas
sobre el estado del sistema y se coordinan vía un global game à la
Goldstein-Pauzner para decidir si se materializa el régimen de run.

El modelo v2 desplaza la incertidumbre desde h hacia **la duración T del shock**.
Motivación empírica: los inventarios globales se observan con poca dispersión
(IEA OMR, EIA WPSR, JODI publican datos semanales/mensuales), mientras que la
duración del cierre de Ormuz es genuinamente incierta y depende de variables
geopolíticas no observables. Las dispersiones de pronósticos entre analistas
sobre cuándo reabrirá Ormuz son grandes, observables y se mueven con noticias.

La estructura matemática del global game se preserva: hay un umbral, hay un
threshold de coordinación, hay una probabilidad sigmoide de transición. Lo que
cambia es **el objeto sobre el cual se juega**: ya no es "¿es h lo
suficientemente alto?" sino "¿durará el shock lo suficiente como para que h
caiga al floor?".

---

## 1. Motivación

### 1.1. Limitación del v1

El v1 hereda directamente la arquitectura de Goldstein-Pauzner (2005) aplicada a
bank runs. En ese contexto, los depositantes ven la solvencia del banco con
ruido idiosincrásico, y el global game opera sobre las creencias acerca del
fundamental (la solvencia).

Trasladado al petróleo, la traducción literal es: el "fundamental" es el buffer
agregado h, y los tenedores de inventario lo ven con ruido. Esto es
matemáticamente cómodo y pedagógicamente claro, pero **empíricamente débil**:

- IEA Oil Market Report publica el Total Global Observed Inventories mensualmente
  con cobertura OECD y estimaciones non-OECD.
- EIA Weekly Petroleum Status Report publica inventarios comerciales US semanalmente.
- JODI-Oil Database cubre 100+ países con frecuencia mensual.
- OECD-OMR brinda estimaciones de stocks comerciales agregados.

No hay dispersión informacional seria sobre h. La σ del global game v1 es un
placeholder no identificable contra datos. La crítica clásica aplica: *if
everyone reads the OMR, where is the heterogeneity?*

### 1.2. La verdadera incertidumbre en el caso Ormuz

Lo que el mercado no sabe con precisión es **cuánto durará el cierre**. T
depende de variables esencialmente no observables:

- Decisiones iraníes de re-escalamiento o de-escalamiento del conflicto.
- Respuesta militar de la 5ta Flota: operaciones de re-apertura, capacidades
  de minesweeping (MCM).
- Diplomacia: rol de Qatar, Omán, China como mediadores.
- Daño físico al Strait: minado, ataques a infraestructura energética en la
  costa, presencia de embarcaciones hostiles.

T no se publica semanalmente. Los analistas geopolíticos serios difieren
significativamente: hay reports proyectando reapertura en 4-8 semanas
(escenario optimista) y otros en 6-12 meses (escenario base de conflicto
prolongado). **Esto sí justifica un objeto de dispersión informacional.**

### 1.3. Consecuencia: el mismo h se interpreta de forma distinta según T

Con h_0 = 7.951 mb (IEA OMR al 30-abril-2026, último reporte disponible al 22-may) y $\dot R \approx 4$ mb/d:

| T (días) | Stock al final del shock | Régimen realizado |
|---|---|---|
| 30 | ~7.831 mb (sobrado) | clásico |
| 90 | ~7.591 mb (cerca del stress threshold) | composite |
| 180 | ~7.231 mb (debajo del threshold) | run |
| 365 | ~6.491 mb (debajo del floor) | colapso |

El régimen que se realiza no lo determina h_0 solo; lo determinan h_0 **y T**
juntos. T es lo único genuinamente incierto.

### 1.4. Qué preguntas adicionales responde el v2

El v2 permite responder preguntas que el v1 no formula naturalmente:

- *Dado el stock actual, ¿qué duración esperada del shock está priciendo el
  mercado en el precio observado?* (E[T] implícito, análogo a θ implícito).
- *¿Cómo debería moverse el precio si llega una noticia que reduce E[T] de
  120 a 60 días?* (sensibilidad ante noticias geopolíticas).
- *¿Qué dispersión de pronósticos σ_T es consistente con la volatilidad
  observada del precio?* (identificación de σ_T contra opciones).
- *¿Cuál es la duración crítica τ_crítico dado el stock actual, debajo de la
  cual el sistema "se salva" del régimen de run?* (umbral operacional clave).

---

## 2. Setup

### 2.1. Variables observables (sin cambios respecto al v1)

- **h_0**: buffer agregado actual. Mapeo lineal al Total Global Observed
  Inventories (ver Extensión 2 del v1, `docs/modelo_extensiones.md`):

  $$h(\text{Stock}) = h^\ast \cdot
    \frac{\text{Stock} - \text{Stock}_{\rm floor}}
         {\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}$$

  Con Stock_floor = 6.800 mb y Stock_stress = 7.600 mb, h_0 ≈ 0,43 al 30-abril-2026 (último IEA OMR).

- **Función de release**: $\dot R(h) = R_{\max} \cdot h / (h + h_R)$.
  Calibración del v1: R_max = 6 mb/d, h_R = 0,12.

- **Elasticidades**: ε_d = 0,05 (demanda), ε_s = 0,04 (oferta).

- **Curvas de equilibrio**: $P_C(h)$ y $P_R(h)$ se computan exactamente como
  en el v1. Sin cambios en `model/core.py:P_classical` ni `P_run`.

- **P\*(stock) con reposición**: la curva de Ormuz abierto sigue siendo
  variable (Extensión 4 del v1). Sin cambios.

### 2.2. Variable incierta: T y su distribución prior

**T ∈ ℝ₊** es la duración aleatoria del cierre de Ormuz, medida en días desde
el inicio del shock.

**Prior baseline:** exponencial con parámetro λ:

$$T \sim \mathrm{Exp}(\lambda), \quad F(\tau; \lambda) = 1 - e^{-\lambda \tau}, \quad \mathbb{E}[T] = 1/\lambda$$

Justificaciones:

1. **Parsimonia**: un solo parámetro, equivalente a E[T] = 1/λ. Slider
   directo en el dashboard.
2. **Memoryless del prior bruto**: $\mathbb{P}(T > t + s \mid T > t) = \mathbb{P}(T > s)$.
   Es decir, **sin condicionar a una señal privada**, el paso del tiempo no
   informa sobre el remanente. El parámetro $\lambda$ no se actualiza por sí
   solo. (Nota importante: el **posterior** del agente, que combina prior +
   señal, sí se actualiza con $t$ vía truncación bayesiana. Ver §2.4.)
3. **Prior maxent**: dado solo E[T] y soporte ℝ₊, la exponencial es la
   distribución de máxima entropía. Defensible bajo ignorancia Knightiana
   sobre la dinámica geopolítica.
4. **Estándar en literatura**: los modelos de hazard de duración de
   conflictos militares en horizontes cortos usan exponencial con frecuencia.

**Prior extendido (opcional):** mixture de dos exponenciales:

$$F(\tau) = \pi \cdot F_{\rm corto}(\tau; \lambda_c) + (1-\pi) \cdot F_{\rm largo}(\tau; \lambda_l)$$

con E[T]_corto ~ 30-60 días ("resolución diplomática") y E[T]_largo ~ 180-365 días
("guerra prolongada o escalación"). Tres parámetros nuevos: π, E[T]_corto, E[T]_largo.

La mixture captura **bimodalidad de creencias**: el mercado puede tener
distribución bimodal sobre T (escenarios discretos), inalcanzable con
exponencial pura. Es el modo natural en que razonan los analistas
geopolíticos. Empíricamente identificable a través de kinks/convexidades de
la term structure de futuros.

### 2.3. Información de cada agente

Cada tenedor de inventario i recibe una **señal privada one-shot en $t=0$**,
que pasa a ser una característica fija del agente (su "tipo"):

$$s_i = T + \varepsilon_i, \quad \varepsilon_i \sim \mathcal{N}(0, \sigma_T^2) \text{ iid}$$

Cada agente conoce su propia señal $s_i$ y la distribución poblacional de
señales (es decir, conoce $\sigma_T$), pero no conoce ni el verdadero T ni
las señales de los demás. **La señal no se actualiza** — no llegan nuevas
señales durante el shock. Lo que sí evoluciona con $t$ es el *posterior*
del agente sobre T, vía condicionamiento bayesiano (§2.4).

**Calibración de σ_T:** escala con E[T]:

$$\sigma_T = \mathrm{CV} \cdot \mathbb{E}[T], \quad \mathrm{CV} = 0{,}5 \text{ (default)}$$

Justificación del coeficiente de variación constante:

- **Empírico**: los pronósticos geopolíticos tienden a tener dispersión
  proporcional al horizonte (más fácil acordar sobre cortos plazos que sobre
  largos).
- **Operacional**: el slider de σ_T se actualiza automáticamente cuando el
  usuario mueve E[T], con opción de desbloquear para análisis avanzado.
- **CV = 0,5**: alto pero realista. Dispersión de Bloomberg consensus sobre
  precios del petróleo a 6 meses suele tener CV ~ 0,2-0,4; en pronósticos
  geopolíticos sobre eventos discretos es mayor.

### 2.4. Actualización bayesiana del posterior con el paso del tiempo

Hay que distinguir tres niveles de "no actualización" que pueden confundirse:

| Objeto | Estado a lo largo de $t$ |
|---|---|
| **Prior bruto $F(\tau; \lambda)$** | Fijo. No cambia por paso del tiempo. Solo cambia por noticias exógenas (shifts de $\lambda$). |
| **Señal privada $s_i$** | Fija. Recibida una sola vez en $t=0$. No llegan nuevas señales. |
| **Posterior $\pi_t(\tau \mid s_i, T > t)$** | **Sí evoluciona con $t$** vía truncación bayesiana sobre la observación "Ormuz sigue cerrado en $t$". |

**El posterior se actualiza así.** En $t=0$, combinando prior + señal:

$$\pi_0(\tau \mid s_i) \propto \lambda e^{-\lambda \tau} \cdot
  \exp\!\left(-\frac{(s_i - \tau)^2}{2\sigma_T^2}\right)$$

Es una gaussiana centrada en $\mu_i = s_i - \lambda \sigma_T^2$ con varianza
$\sigma_T^2$ (truncada en $\tau \geq 0$).

En $t > 0$ con Ormuz aún cerrado, el agente condiciona también en $T > t$:

$$\pi_t(\tau \mid s_i, T > t) \propto \pi_0(\tau \mid s_i) \cdot \mathbf{1}\{\tau > t\}$$

Es una **gaussiana truncada por abajo en $t$**. La esperanza condicional
del remaining wait es:

$$\mathbb{E}[T - t \mid s_i, T > t] =
  \sigma_T \cdot \frac{\varphi(\alpha_i)}{1 - \Phi(\alpha_i)} - (t - \mu_i)$$

con $\alpha_i = (t - \mu_i)/\sigma_T$. Esta es la **inverse Mills ratio**:
conforme $t$ crece sin reapertura, $\alpha_i$ crece, y el posterior se
comprime hacia $t$ por la derecha.

**Implicación operacional.** Consideremos un agente con $s_i = 60$ y prior
con $\mathbb{E}[T] = 60$ días, $\sigma_T = 30$. En $t=0$ espera
$\mathbb{E}[T \mid s_i = 60] \approx 45$ días. Pasan 200 días sin reapertura:

- El posterior se trunca a $\tau > 200$.
- La gaussiana original (centrada en 45, std 30) tiene esencialmente cero
  masa sobre 200.
- El posterior se concentra apenas por encima de 200.
- $\mathbb{E}[T - 200 \mid s_i = 60, T > 200] \to 0$: el agente concluye
  "tiene que reabrir de un momento a otro".

En cambio un agente con $s_i = 300$ (pesimista) tiene $\mu_i = 285$, y a
$t=200$ su posterior está poco afectado por la truncación. Sigue esperando
algo cerca de 300 días.

**Conclusión:** el paso del tiempo "fuerza hacia el límite" las creencias
de los agentes optimistas (sus posteriors colapsan a la derecha de $t$),
pero deja a los pesimistas relativamente intactos. Esto **introduce dinámica
natural en $q_t$ aún sin cambio en el stock o en el prior bruto**.

**Las noticias geopolíticas actualizan el prior bruto.** Esto es **exógeno
al modelo**: noticias importantes entran como shifts del parámetro $\lambda$
(o equivalentemente de $\mathbb{E}[T]$). En el dashboard, el slider de
$\mathbb{E}[T]$ es la palanca con la cual el usuario implementa
"incorporación de noticias". El modelo no genera endógenamente las
actualizaciones; las recibe como input.

**Una corrección importante respecto a la lectura inicial del baseline.**
Una versión previa de este doc afirmaba "no hay learning pasivo". Esa
formulación era imprecisa: aplica al prior bruto (la $\mathrm{Exp}(\lambda)$
sin condicionar es memoryless), **no al posterior**. El framework correcto
es el de arriba: señal fija, posterior bayesiano que evoluciona con $t$.

---

## 3. Dinámica del stock condicional a T

### 3.1. Trayectoria determinista del stock

Dado un valor realizado de T, mientras Ormuz está cerrado ($t < T$) el stock
se drena según la función de release del modelo aplicada al stock vía el
mapeo lineal de §2.1:

$$\frac{d\,\text{Stock}}{dt} = -\dot R\!\left(h(\text{Stock}(t))\right), \quad \text{Stock}(0) = \text{Stock}_0$$

Es la dinámica de la Extensión 3 del v1 (`docs/modelo_extensiones.md`),
integrada numéricamente con scipy `solve_ivp`. Sin cambios.

Para $t \geq T$ (Ormuz reabierto), se acopla la demanda de reposición de la
Extensión 4 del v1. El stock recupera trayectoria hacia Stock_opt; el precio
se acomoda en P\*(Stock).

### 3.2. Tiempo crítico τ_crítico

Definimos el **tiempo hasta que el stock toca el floor operacional**:

$$\tau_{\rm crítico}(\text{Stock}_0) \equiv \inf\{t > 0 : \text{Stock}(t) \leq \text{Stock}_{\rm target}\}$$

con **Stock_target = Stock_floor = 6.800 mb** (default). El parámetro es
configurable en el dashboard. Alternativa natural: Stock_target = Stock_stress
= 7.600 mb (más conservador; más temprano el sistema "se compromete").

Interpretación: $\tau_{\rm crítico}$ es la **duración crítica del shock dado
el stock actual**. Si T < τ_crítico, Ormuz reabre antes de que el stock toque
el floor: el sistema no entra en régimen colapso. Si T > τ_crítico, el stock
cae al floor antes de la reapertura: régimen colapso garantizado.

Como $\dot R$ es decreciente en Stock cuando Stock baja (el release se debilita
con el buffer), τ_crítico es estrictamente positiva para todo Stock_0 >
Stock_target y crece con Stock_0.

**Cálculo numérico:** integrar la ODE de §3.1 con event-detection en
Stock = Stock_target. Es una llamada simple a `solve_ivp` con `events=...`.

### 3.3. Regla de transición de régimen

Bajo el modelo v2, el régimen realizado depende del orden entre dos números:

- $T$: aleatorio, distribuido $F(\tau)$.
- $\tau_{\rm crítico}(\text{Stock}_0)$: determinista, función del stock actual.

Casos:

- **T < τ_crítico**: Ormuz reabre a tiempo. El sistema se mantiene en régimen
  clásico durante todo el shock. Precio durante el shock: trayectoria $P_C(h_t)$.
  Precio post-shock: P\*(Stock(T)) con reposición.

- **T > τ_crítico**: el stock toca el floor antes de la reapertura. Antes de
  cruzar, el sistema puede o no haber entrado en régimen run (depende de
  cuándo se coordinó la corrida; ver §4). Una vez en el floor, el régimen
  es de colapso (P → P_cap).

La probabilidad ex ante de cada caso es:

$$\mathbb{P}(T < \tau_{\rm crítico}) = F(\tau_{\rm crítico}; \lambda) = 1 - e^{-\lambda \tau_{\rm crítico}}$$
$$\mathbb{P}(T \geq \tau_{\rm crítico}) = 1 - F(\tau_{\rm crítico}; \lambda) = e^{-\lambda \tau_{\rm crítico}}$$

Notar que **la probabilidad de "resolución a tiempo" tiene unidades claras y
es identificable empíricamente**, a diferencia del θ implícito del v1.

---

## 4. El global game sobre T

### 4.1. Setup del juego

Un continuo de tenedores de inventario indexado por $i \in [0, 1]$. Cada uno
posee una unidad de stock. Al inicio del shock (t = 0), cada agente recibe su
señal privada $s_i = T + \varepsilon_i$.

**Acción binaria:** cada agente elige $a_i \in \{L, R\}$:

- $L$ = "Liberar": vender el inventario hoy al mercado a precio $P_t$.
- $R$ = "Retener": guardar el inventario, no liberarlo. La intención es vender
  más adelante a un precio esperado mayor (típicamente bajo régimen run o cap).

**Nota de nomenclatura:** "retener" en este modelo equivale a "correr" en el
sentido del bank run de Diamond-Dybvig, pero **al revés**: en el bank run,
"correr" = retirar depósitos. Acá "correr" = retener inventario fuera del
mercado. Ambas son acciones de coordinación que precipitan la materialización
del régimen alterno (insolvencia bancaria / régimen de run del petróleo).

### 4.2. Payoffs

Sea $\alpha$ la fracción agregada de agentes que eligen $R$ (retener).
$\alpha$ es función del verdadero T vía las señales $s_i$.

**Payoff de Liberar** dado precio prevalente $P$:

$$\pi(L; P) = P$$

Es decir, el agente vende su unidad al precio spot del momento.

**Payoff de Retener** dado el régimen futuro realizado:

$$\pi(R; \text{régimen}, T) =
\begin{cases}
\mathbb{E}[P_C(h_{T})] & \text{si régimen clásico (T < } \tau_{\rm crítico}) \\
\mathbb{E}[P_R(h_{T})] & \text{si régimen run (} T \geq \tau_{\rm crítico}) \\
P_{\rm cap} & \text{si régimen colapso}
\end{cases}$$

(En la práctica el agente que retiene puede vender en cualquier momento entre
hoy y T, no solo al final. Por simplicidad, asumimos que vende en el punto
óptimo de su trayectoria. La heterogeneidad de timing es una limitación
asumida; ver §9.)

**Complementariedades estratégicas:** cuantos más agentes retienen, menor es
la oferta efectiva al mercado, mayor el precio, y más rentable haber
retenido. Esta es la firma de un juego de coordinación con potencial
multi-equilibrio (todos liberan ↔ nadie libera).

### 4.3. Equilibrio en estrategias monótonas

Por el resultado clásico de Carlsson-van Damme (1993) y Morris-Shin (1998), en
juegos de coordinación con señales privadas ruidosas existe **un único
equilibrio en estrategias monótonas**, definido por un umbral $s^\ast$:

$$a_i = \begin{cases} L & \text{si } s_i < s^\ast \\ R & \text{si } s_i \geq s^\ast \end{cases}$$

Es decir, **un agente retiene si y solo si su señal sobre T es lo
suficientemente alta**.

**Determinación de $s^\ast$:** el agente marginal (con señal $s_i = s^\ast$)
debe ser indiferente entre L y R:

$$\mathbb{E}[\pi(L) \mid s_i = s^\ast] = \mathbb{E}[\pi(R) \mid s_i = s^\ast]$$

**Caso límite $\sigma_T \to 0$ (señales casi perfectas):**

$$s^\ast \to \tau_{\rm crítico}(\text{Stock}_0)$$

Es decir, en ausencia de ruido informacional, los agentes retienen sii saben
que T excede τ_crítico — la regla óptima first-best.

**Caso $\sigma_T > 0$:** $s^\ast$ se desvía de τ_crítico por un término que
depende de la curvatura de los payoffs y la asimetría del riesgo. Para el
baseline, usamos la aproximación $s^\ast \approx \tau_{\rm crítico}$, válida
cuando los payoffs son aproximadamente lineales alrededor del umbral. Es una
simplificación que merece refinamiento en una segunda iteración (ver §9).

### 4.4. Probabilidad agregada de run

Dada la estrategia monótona con umbral $s^\ast$, la fracción de agentes que
retiene es:

$$\alpha(T) = \mathbb{P}(s_i \geq s^\ast \mid T) = 1 - \Phi\!\left(\frac{s^\ast - T}{\sigma_T}\right)$$

La probabilidad ex ante de que el agregado materialice el run depende de
la distribución relevante sobre T en cada snapshot. Hay dos lecturas
operacionalmente distintas:

**(a) En el snapshot inicial ($t = 0$):** se usa el prior bruto. Bajo la
aproximación $s^\ast \approx \tau_{\rm crítico}$ y con $T \sim \mathrm{Exp}(\lambda)$:

$$q_0(\mathbb{E}[T], \text{Stock}_0, \sigma_T) = 1 - \Phi\!\left(\frac{\tau_{\rm crítico}(\text{Stock}_0) - \mathbb{E}[T]}{\sigma_T}\right)$$

**(b) En snapshots posteriores ($t > 0$, Ormuz aún cerrado):** se usa el
posterior truncado (ver §2.4). La distribución relevante deja de ser el
prior $\mathrm{Exp}(\lambda)$ y pasa a ser $T \mid T > t$. Operacionalmente,
$\mathbb{E}[T]$ del input del modelo se reemplaza por el valor remanente
condicional, que **crece monótonamente con $t$** (porque la masa por
debajo de $t$ se cae).

Por lo tanto:

$$q_t(\mathbb{E}_t[T \mid T > t], \text{Stock}_t, \sigma_T) =
  1 - \Phi\!\left(\frac{\tau_{\rm crítico}(\text{Stock}_t) - \mathbb{E}_t[T \mid T > t]}{\sigma_T}\right)$$

con $\mathbb{E}_t[T \mid T > t] = t + 1/\lambda$ bajo prior exponencial (la
identidad típica de la exponencial: el "expected remaining wait" es
constante, pero el expected total $T$ crece linealmente con $t$).

**Interpretación:** $q_t$ es la probabilidad sigmoidal de run agregada en
el snapshot $t$. Crece con $\mathbb{E}[T]$ (más duración esperada →
coordinación en retener), decrece con Stock_t (más buffer → mayor
τ_crítico → menos urgencia), se suaviza con σ_T. **Conforme $t$ crece sin
reapertura, $q_t$ tiende a crecer** por dos canales: (1) el stock se drena
y τ_crítico baja, (2) $\mathbb{E}_t[T \mid T > t]$ crece.

**Caso límite σ_T → 0:** $q$ se aproxima a la indicadora $\mathbf{1}\{\mathbb{E}[T] > \tau_{\rm crítico}\}$.

**Caso límite σ_T → ∞:** $q \to 1/2$ (máxima dispersión, sin coordinación clara).

---

## 5. Formación de precios

### 5.1. Precio composite

El precio observado en el snapshot actual es el promedio ponderado de los
dos regímenes, exactamente como en el v1:

$$P_t = (1 - q_t) \cdot P_C(h_t) + q_t \cdot P_R(h_t)$$

con

$$q_t = q(\mathbb{E}_t[T], \text{Stock}_t, \sigma_T)$$

**Dinámica del precio bajo shock persistente:** el precio se mueve por tres
canales:

1. **$h_t$ baja con el tiempo** (drenaje del stock): mueve $P_C$ y $P_R$
   hacia arriba, y baja $\tau_{\rm crítico}$ → sube $q_t$.
2. **Truncación bayesiana endógena**: aún sin noticias, $\mathbb{E}_t[T \mid T > t]$
   crece con $t$ porque los agentes condicionan en "Ormuz sigue cerrado"
   (§2.4). Esto sube $q_t$ aunque el prior bruto y el stock no cambien.
3. **Noticias geopolíticas exógenas**: shifts del parámetro $\lambda$ del
   prior, mueven $\mathbb{E}_0[T]$ directamente. Operacionalizados vía
   slider en el dashboard.

Esto es la diferencia clave con el v1: en v2 el precio puede moverse
**sin que cambien los fundamentos físicos**, por cambios en expectativas
geopolíticas (canal 3) o por el simple paso del tiempo (canal 2). Es
consistente con la observación empírica de saltos de precio en respuesta a
anuncios y noticias sin cambio en stocks ni en producción, así como con la
acumulación gradual de presión al alza cuando un shock se prolonga sin
resolución.

### 5.2. Reinterpretación de θ

En el v1, θ es un parámetro libre con interpretación de "probabilidad
implícita de normalización". Su identificación es difusa: no tiene unidades
claras y se mide como un wedge residual entre P_modelo y P_observado.

En el v2, el análogo natural es:

$$\theta_{v2} \equiv \mathbb{P}(T < \tau_{\rm crítico}) = 1 - e^{-\lambda \tau_{\rm crítico}}$$

con λ = 1/E[T]. Es la **probabilidad de que el shock se resuelva a tiempo**
(antes de que el stock toque el floor operacional).

Ventajas respecto al θ del v1:

- **Unidades claras:** es una probabilidad genuina, derivada de F(τ) y τ_crítico.
- **Identificable empíricamente:** dado E[T] (de surveys/forwards) y Stock_0
  (de IEA), θ_v2 está completamente determinado. No es un parámetro libre.
- **Comparable entre escenarios:** dos escenarios con distintos Stock_0 y
  distintos E[T] producen θ_v2 distintos pero conmensurables.
- **Mapeo conceptual con v1:** θ_v2 ≈ 1 − q_v2, así que θ alta = poca prob.
  de run, igual que en v1.

### 5.3. P\*(Stock) con reposición (sin cambios)

La curva de Ormuz abierto P\*(Stock) sigue siendo variable según la Extensión
4 del v1: cuanto menor el stock al momento de la reapertura, mayor la demanda
de reposición y mayor P\*. Misma fórmula:

$$D(P^\ast) + R_{\rm repl}(\text{Stock}) = S_{\rm open}(P^\ast)$$

con R_repl saturada al floor. La integración con el v2 es natural: P\*
evaluado en Stock(T) es el precio post-shock. Para fines del precio actual,
P\*(Stock_0) sigue siendo la referencia del "régimen abierto" en cada momento.

---

## 6. Identificación empírica

### 6.1. Parámetros observables directos

- **Stock_0:** IEA OMR Total Global Observed Inventories. Frecuencia mensual.
  Calidad alta para OECD; estimación para non-OECD. Default del modelo: 7.951 mb
  (IEA OMR al 30-abril-2026, último reporte disponible al 22-may).

- **Stock_floor, Stock_stress, Stock_opt:** umbrales operacionales JPMorgan
  y nivel óptimo derivado de pico 2025. Defaults: 6.800 / 7.600 / 8.200 mb.

- **dot_R parameters (R_max, h_R):** calibrados como en v1 con datos
  históricos de releases coordinados. Sin cambios.

- **Elasticidades (ε_d, ε_s):** literatura (Caldara-Cavallo-Iacoviello 2019,
  Kilian 2009). Sin cambios.

### 6.2. Parámetros nuevos del v2

**E[T] — duración esperada del shock:**

Tres fuentes alternativas, con consistencia cruzada:

1. **Term structure de futuros (forward curve):** la pendiente de la curva
   de Brent forward (e.g. Brent CO1-CO12) pricea expectativas sobre cuándo
   los precios spot retornarán a P\*. Si la curva está en backwardation
   pronunciada por varios meses adelantados, el mercado pricea persistencia.
   Si revierte a flat o contango temprano, el mercado pricea reapertura
   próxima. Calibración: ajustar E[T] tal que el modelo reproduzca la
   pendiente observada.

2. **Surveys de analistas:** Bloomberg consensus, Reuters polls, JPMorgan
   y Goldman commodity desks publican proyecciones de Brent a 3, 6, 12
   meses. La duración implícita del shock se puede extraer del horizonte
   donde el consensus retorna a niveles pre-shock.

3. **Mercados de predicción:** si existen mercados Polymarket o Kalshi sobre
   "Strait of Hormuz reopening by date X", se puede leer F(τ) directamente
   de los precios de los contratos. Es la fuente más directa pero la menos
   líquida.

**σ_T — dispersión de pronósticos sobre T:**

- **Default por escalamiento:** $\sigma_T = 0{,}5 \cdot \mathbb{E}[T]$ (CV = 0,5).
- **Empírico de surveys:** desviación estándar entre analistas en el Bloomberg
  consensus de Brent a 6 meses, escalada al horizonte de T.
- **Implícito de opciones:** volatilidad implícita de opciones at-the-money
  sobre Brent en el strike de P\*. Mapeable a σ_T vía un cálculo de delta.

### 6.3. Calibración inversa: E[T] implícito

Análogo al θ implícito del v1, pero más limpio. Dado:
- $P_{\rm observado}$,
- Stock_0,
- Todos los parámetros estructurales (elasticidades, dot_R, P\*),
- σ_T (asumiendo CV = 0,5 o algún otro supuesto),

se despeja **el valor de E[T] que reconcilia el modelo con el precio
observado**. Operacionalmente, root-finding sobre la ecuación:

$$P_{\rm observado} = (1 - q(\mathbb{E}[T], \text{Stock}_0, \sigma_T)) \cdot P_C(h_0) + q(\cdot) \cdot P_R(h_0)$$

resolviendo por $\mathbb{E}[T]$.

**Lectura:** si el modelo se calibra con E[T]_implícito = 75 días al
30-abril-2026, eso dice que el precio observado es consistente con un mercado
que pricea una reapertura esperada de 75 días. Si al 29-may-2026 el precio
sube y E[T]_implícito = 110 días, el mercado endureció su pronóstico.

Esta serie temporal de E[T]_implícito es un **tracker diario de expectativas
geopolíticas extraído del precio**, paralelo al θ implícito pero con unidades
de tiempo.

### 6.4. Estado del mercado a mayo 2026 (placeholders para calibración)

Pendiente de poblamiento con datos al cierre. Estimaciones tentativas:

- Stock_0 = 7.951 mb (IEA OMR al 30-abril-2026, último reporte).
- P_observado = 114,01 USD/bbl (Bloomberg M1 constant-maturity) al 30-abril-2026.
- E[T]_consensus ≈ ?  (extraer del Bloomberg survey de mayo).
- σ_T ≈ ?  (extraer de dispersión de surveys, o usar default CV = 0,5).
- E[T]_implícito = ?  (resolver con la calibración inversa).

---

## 7. Predicciones del v2 y diferencias con v1

### 7.1. Mecánica de cómo se mueve el precio

| Causa | v1 (incertidumbre sobre h) | v2 (incertidumbre sobre T) |
|---|---|---|
| Cambio en stocks (Δh) | Sí, vía $P_C(h), P_R(h), q(h)$ | Sí, vía $P_C(h), P_R(h), \tau_{\rm crítico}$ |
| Cambio en expectativas geopolíticas | No tiene mecanismo natural | Sí, vía Δ$\mathbb{E}[T]$ → Δq |
| Cambio en dispersión de pronósticos | Solo si se mueve σ_h ad-hoc | Sí, vía Δσ_T → Δq (curvatura) |
| Cambio en P\* (Extensión 4) | Sí, ambos | Sí, ambos |
| Cambio en parámetros estructurales (ε, R_max, etc.) | Sí, ambos | Sí, ambos |

**Insight:** el v2 introduce **dos canales nuevos de variación del precio
sin cambio físico en los stocks**: E[T] y σ_T. Esto es esencial para
explicar saltos de precio asociados a anuncios geopolíticos sin movimiento
en datos físicos.

### 7.2. Sensibilidades cruzadas

- $\partial P / \partial h_0$: ambos modelos predicen elasticidad respecto al
  stock; el v2 es típicamente más sensible cerca de $\tau_{\rm crítico}$
  porque pequeñas variaciones en h_0 mueven τ_crítico significativamente.

- $\partial P / \partial \mathbb{E}[T]$: solo v2. Es la sensibilidad clave del
  modelo y la mayor fuente operativa de movimientos de precio en períodos
  de stocks estables.

- $\partial P / \partial \sigma_T$: solo v2. Si σ_T sube (más incertidumbre
  geopolítica), q se aproxima a 0,5 desde donde estaba; el precio se mueve
  hacia el composite balanceado.

### 7.3. Wedge entre precio observado y predicho

- **v1:** wedge = (1 − θ) · P_modelo + θ · P\* − P_observado. θ
  adimensional, identificación residual.

- **v2:** wedge = P_modelo(E[T]_consensus) − P_observado. Si distinto de
  cero, se interpreta como E[T]_implícito ≠ E[T]_consensus, con unidades
  de días y comparable diariamente.

El v2 da una **lectura más estructurada y operacional** del wedge.

### 7.4. Relación de nesting parcial entre v1 y v2

El v1 puede verse aproximadamente como caso límite del v2 cuando:

- E[T] → ∞ (mercado pricea cierre indefinido).
- σ_T es libre y captura la dispersión informacional sobre h vía un mapeo
  $\sigma_T = \sigma_h \cdot |d\tau/dh|$.

Bajo estas condiciones, q_v2 se aproxima a q_v1. Pero no es nesting estricto:
la interpretación de las señales es distinta (sobre T vs. sobre h), y los
parámetros del global game no son intercambiables uno-a-uno.

En la práctica, **es mejor mantenerlos como dos modelos paralelos** en el
dashboard, con sus propias pestañas y sliders, sin pretender mapear unos
parámetros en otros.

### 7.5. Comparativas estilizadas

Tres ejercicios numéricos que distinguen claramente v1 vs. v2 (a poblar
durante implementación):

1. **Mismo h_0, distintos E[T]:** v1 predice un único precio; v2 predice una
   sigmoide P(E[T]).

2. **Mismo E[T], distintos σ_T:** v1 no responde; v2 modula la curvatura
   de la sigmoide.

3. **h_0 cayendo gradualmente con E[T] fijo:** ambos predicen suba del
   precio. El v2 acelera la suba conforme $\tau_{\rm crítico} \to \mathbb{E}[T]$.

---

## 8. Calibración y figuras del dashboard

### 8.1. Parámetros nuevos a exponer en el sidebar

**Sliders del global game v2 (pestaña dedicada):**

- $\mathbb{E}[T]$ (días): rango 7-365, default 60.
- $\sigma_T$ (días): default = $0{,}5 \cdot \mathbb{E}[T]$ con link
  automático. Toggle "personalizar" para desbloquear.
- Stock_target para τ_crítico: dropdown con dos opciones:
  - "Floor (6.800 mb)" — default.
  - "Stress (7.600 mb)" — más conservador.
  Editable a valor numérico libre opcional.

**Sliders del prior mixture (opcional, sección expandible):**

- π (probabilidad de "escenario corto"): rango 0-1, default 0,5.
- $\mathbb{E}[T]_{\rm corto}$: rango 7-90, default 45 días.
- $\mathbb{E}[T]_{\rm largo}$: rango 90-720, default 240 días.
- Toggle "Usar mixture en lugar de exponencial".

**Sliders heredados del v1 (compartidos entre pestañas):**

- Estructurales: P\*, D_0, S_f0, ε_d, ε_s.
- Release: R_max, h_R.
- Régimen run: μ, δ_0.
- Stock: Stock_actual, Stock_stress, Stock_floor, Stock_opt, R_repl_max.

**Sliders del v1 NO usados en v2 (se desactivan en la pestaña v2):**

- h\*, σ_h: irrelevantes en v2; el umbral del game se computa endógenamente
  como $\tau_{\rm crítico}$.

### 8.2. Figuras del v2

**Figura 1 — Precio vs. E[T] (h_0 fijo): la figura principal.**

- Eje x: E[T] (días), rango 7-365.
- Eje y: precio (USD/bbl).
- Curvas:
  - **Verde continua:** $P_C(h_0)$ (constante en E[T]; el régimen clásico no
    depende de las creencias sobre T).
  - **Roja punteada:** $P_R(h_0)$ (constante en E[T]).
  - **Negra:** $P_{\rm composite}(\mathbb{E}[T]) = (1-q) P_C + q P_R$ con $q =
    q(\mathbb{E}[T], h_0, \sigma_T)$. Tiene forma sigmoide ascendente.
  - **Morada:** P\*(Stock_0) (constante en E[T]; régimen abierto).
- Marcadores verticales:
  - $\tau_{\rm crítico}(\text{Stock}_0)$: línea vertical marcando el umbral
    crítico. El régimen del modelo cambia abruptamente alrededor de este
    valor (suavizado por σ_T).
  - $\mathbb{E}[T]_{\rm consensus}$: si se inputa.
  - $\mathbb{E}[T]_{\rm implícito}$: derivado de P_observado.
- Marcador de precio observado: línea horizontal en P_observado, intersección
  con la curva composite da E[T]_implícito.

**Figura 2 — Trayectoria temporal P(t) bajo distintos escenarios T.**

- Eje x: tiempo calendario (fechas desde la fecha de la observación inicial, por default 30-abril-2026).
- Eje y: precio.
- Múltiples curvas, una por escenario T:
  - Optimista: T = E[T]_consensus − 1 σ_T.
  - Central: T = E[T]_consensus.
  - Pesimista: T = E[T]_consensus + 1 σ_T.
- Para cada escenario, se computa P(t) = composite ponderado por la
  probabilidad de cada régimen, actualizada con el paso del tiempo.
- Marcadores: fechas de cruce del stress threshold y del floor.

**Figura 3 — Stock evolution (idéntica al v1, sin cambios).**

Sigue siendo la figura temporal de stocks ya implementada.

**Figura 4 (extensión opcional) — Heat map P(h_0, E[T]).**

- Plano (h_0, E[T]).
- Color: precio composite.
- Útil para análisis cruzado, identificación de zonas de transición de régimen.

**Figura 5 (extensión opcional) — Serie temporal de E[T] implícito.**

- Si se tienen P_observado a múltiples fechas, se computa E[T]_implícito en
  cada fecha y se grafica como serie temporal.
- Es el output más operacional del modelo: un tracker diario de expectativas
  geopolíticas extraído del mercado de petróleo.

### 8.3. Estructura de pestañas del dashboard

Propuesta de tres pestañas top-level:

1. **"Modelo v1: incertidumbre sobre h"** — el actual. Sin cambios.
2. **"Modelo v2: incertidumbre sobre T"** — nuevo. Contiene las Figuras 1-5
   de arriba.
3. **"Comparativa"** — vista lado a lado de v1 y v2 para los mismos
   parámetros estructurales. Útil para entender diferencias y discutir con
   colegas.

Cada pestaña tiene su propio sidebar o paneles plegables. Los sliders
estructurales compartidos se sincronizan entre pestañas (no se duplica el
estado).

### 8.4. Notas al pie de figuras (versión v2)

A diseñar conforme las figuras se implementen. Borrador inicial:

> *Modelo estructural v2 con incertidumbre sobre la duración del shock T.
> Cada agente recibe una señal privada ruidosa $s_i = T + \varepsilon_i$ con
> $\varepsilon_i \sim \mathcal{N}(0, \sigma_T^2)$. El equilibrio del global
> game determina la probabilidad de régimen de run $q$ como función sigmoide
> de $\mathbb{E}[T]$ relativa al tiempo crítico $\tau_{\rm crítico}(\text{Stock}_0)$,
> definido como el tiempo hasta que el stock toca el floor operacional
> (6.800 mb). Calibración: $\varepsilon_d = 0{,}05$, $\varepsilon_s = 0{,}04$,
> CV = 0,5.*

---

## 9. Limitaciones y extensiones futuras

### 9.1. Limitaciones del baseline v2

1. **Decisión estática snapshot.** El game se resuelve como one-shot en cada
   instante con el estado actual. No captura la **selección dinámica** del
   pool de tenedores: en realidad, los agentes con bajas expectativas sobre T
   liberan primero, dejando en el pool solo los que tienen expectativas
   altas. Esto sesga progresivamente las creencias agregadas hacia
   pesimismo. El snapshot estático ignora este efecto de composición.

2. **Prior exponencial (memoryless del prior bruto).** El parámetro
   $\lambda$ no se actualiza por sí solo con el paso del tiempo (sí lo hace
   el posterior; ver §2.4). Esto implica que el modelo no captura
   *entrenchment* (hazard decreciente: cuanto más dura, menos probable que
   termine) ni *fatigue* (hazard creciente: cuanto más dura, más presión
   por resolver). Capturar ambos requiere Weibull con parámetro de forma
   $k \neq 1$.

3. **Señales one-shot.** Los agentes reciben $s_i$ una sola vez en $t=0$.
   El posterior se actualiza por condicionamiento sobre "$T > t$" (§2.4),
   pero no llegan nuevas señales informativas durante el shock. En la
   realidad, los agentes incorporan noticias geopolíticas idiosincrásicas
   día a día. Modelarlo formalmente requiere un filtro de Kalman acoplado
   al global game (dynamic global game con information arrival; ver
   Extensión E3 abajo).

4. **Aproximación $s^\ast \approx \tau_{\rm crítico}$.** En rigor, el umbral
   $s^\ast$ se desvía de $\tau_{\rm crítico}$ por un término que depende de
   la curvatura de los payoffs y la asimetría del riesgo entre L y R. La
   aproximación es válida cuando los payoffs son aproximadamente lineales
   alrededor del umbral; merece refinamiento en una segunda iteración.

5. **Heterogeneidad de timing de venta para los que retienen.** Asumimos que
   el agente que retiene vende en el punto óptimo de su trayectoria. En
   realidad cada agente puede vender en momentos distintos. Esto introduce
   selección y heterogeneidad de payoffs entre los R.

### 9.2. Extensiones naturales

| ID | Extensión | Complejidad | Beneficio |
|---|---|---|---|
| E1 | Prior mixture (escenarios discretos) | Baja | Captura bimodalidad de creencias, identificable con kink en forward curve |
| E2 | Prior Weibull (hazard variable) | Media | Captura entrenchment/fatigue; mejor fit a duraciones empíricas de conflictos |
| E3 | Updating bayesiano del prior con paso del tiempo | Media-alta | Endógena el efecto de "Ormuz aún cerrado al día N" sobre creencias |
| E4 | Stopping time formal (real-option) | Alta | Modelo dinámico completo; captura selección y heterogeneidad de timing |
| E5 | Información endógena (noticias generadas por el modelo) | Alta | Modelo dinámico geopolítico-económico; muy ambicioso |
| E6 | Multi-país con T heterogéneo | Alta | Permite análisis de shocks parciales (no solo Ormuz total) |

### 9.3. Limitaciones compartidas con v1

Permanecen las limitaciones del v1 documentadas en `docs/modelo_extensiones.md`:

- $\dot R$ es reduced-form, no microfundamentado.
- Mapeo lineal h ↔ Stock.
- Elasticidades constantes.
- Sin futures markets endógenos.
- Calibración de Stock_opt es exógena.

---

## 10. Hoja de ruta de implementación

Pendiente confirmación con el usuario antes de tocar código. Orden propuesto:

1. **[Doc]** Revisar este documento con el usuario, ajustar las decisiones
   sueltas (calibración inicial, ordenamiento de figuras, prioridad de
   extensiones).

2. **[Core]** Añadir a `model/` un nuevo módulo `model/v2.py` con:
   - `tau_critico(stock_0, params)`: integra ODE hasta tocar floor.
   - `q_run_v2(E_T, stock_0, sigma_T, params)`: función sigmoide.
   - `P_composite_v2(E_T, stock_0, sigma_T, params)`: el precio composite v2.
   - `E_T_implicit(P_observed, stock_0, sigma_T, params)`: calibración inversa.

3. **[Calibration]** Extender `model/calibration.py` con `ModelParamsV2`
   que herede de `ModelParams` y añada `E_T`, `sigma_T_CV`, `stock_target`.
   Considerar si conviene refactor o composición.

4. **[App]** Añadir pestaña "Modelo v2" a `app/app.py` con:
   - Sidebar con sliders nuevos.
   - Figura 1 (P vs. E[T]) — la principal.
   - Figura 2 (P(t) bajo escenarios) — segunda prioridad.
   - Figura 3 (Stock) — reuso del v1.
   - Métricas de τ_crítico, E[T]_implícito, θ_v2.

5. **[App]** Añadir pestaña "Comparativa" con vista lado a lado.

6. **[Docs]** Una vez funcionando, actualizar `docs/modelo_extensiones.md`
   para mencionar el v2 como Extensión 5 alternativa, con link a este doc.

7. **[Calibración empírica]** Poblar §6.4 con datos al cierre. Computar
   primer E[T]_implícito al 30-abril-2026.

8. **[Validación]** Comparar predicciones de v1 y v2 contra precio observado
   en una grilla de fechas (ideal: mayo 2026 día por día). Cuál ajusta mejor
   informa qué versión usar como vista principal del dashboard.

---

## Apéndices

### A. Glosario de notación

| Símbolo | Significado | Unidades |
|---|---|---|
| $T$ | Duración aleatoria del cierre de Ormuz | días |
| $\tau$ | Realización genérica de T | días |
| $\lambda$ | Parámetro de la exponencial; $1/\lambda = \mathbb{E}[T]$ | 1/días |
| $\tau_{\rm crítico}$ | Tiempo hasta que Stock toca Stock_target | días |
| $\mathbb{E}[T]$ | Duración esperada del shock | días |
| $\sigma_T$ | Desviación estándar de pronósticos sobre T | días |
| $s_i$ | Señal privada del agente i sobre T | días |
| $s^\ast$ | Umbral del global game v2 | días |
| $q$ | Probabilidad de régimen run (v2) | adimensional |
| $\theta_{v2}$ | Prob. de resolución a tiempo = $1 - q$ | adimensional |
| Stock_0 | Stock observado al inicio del shock | mb |
| Stock_target | Stock al cual se define τ_crítico (default = floor) | mb |
| Stock_floor | Floor operacional JPMorgan (6.800) | mb |
| Stock_stress | Threshold de stress JPMorgan (7.600) | mb |
| Stock_opt | Nivel óptimo de inventarios (8.200) | mb |
| $h_t$ | Buffer slack en t, vía mapeo lineal | adimensional |
| $\dot R(h)$ | Función de release Michaelis-Menten | mb/d |
| $P_C(h)$ | Precio régimen clásico | USD/bbl |
| $P_R(h)$ | Precio régimen run | USD/bbl |
| $P^\ast(\text{Stock})$ | Precio régimen abierto con reposición | USD/bbl |

### B. Referencias clave

- **Caldara, Cavallo & Iacoviello (2019).** Oil Price Elasticities and Oil
  Price Fluctuations. *Journal of Monetary Economics*, 103, 1-20.
- **Carlsson & van Damme (1993).** Global Games and Equilibrium Selection.
  *Econometrica*, 61(5), 989-1018.
- **Goldstein & Pauzner (2005).** Demand-Deposit Contracts and the Probability
  of Bank Runs. *Journal of Finance*, 60(3), 1293-1327.
- **Morris & Shin (1998).** Unique Equilibrium in a Model of Self-Fulfilling
  Currency Attacks. *American Economic Review*, 88(3), 587-597.
- **Documento de trabajo v1 (2026):** "Modelo estructural del precio del
  petróleo bajo stress de oferta" (`docs/modelo_petroleo.pdf`).
- **Extensiones documentadas del v1:** `docs/modelo_extensiones.md`.

### C. Preguntas abiertas para discusión

Estas son decisiones que merecen mayor reflexión antes de implementar:

1. **Calibración inicial de E[T] al 30-abril-2026:** ¿qué valor usar de
   default? Sugerencia tentativa: 60-90 días.

2. **Tratamiento del prior bajo noticias:** ¿hacemos un "panel de noticias"
   en el dashboard donde se simulan shocks discretos a E[T], o solo se
   manipula el slider?

3. **Tratamiento de la dinámica de E[T]:** ¿asumimos E[T] constante durante
   la simulación temporal de §8.2 Figura 2, o lo dejamos variar según una
   regla simple (e.g., revierte hacia un valor de largo plazo)?

4. **Refinamiento de $s^\ast$:** ¿vale la pena derivar la condición de
   indiferencia explícitamente, o seguimos con $s^\ast \approx \tau_{\rm crítico}$?

5. **Validación empírica:** ¿qué dataset usar para discriminar entre v1 y v2?
   Propuesta: precios diarios Brent + Stock_0 mensual + E[T]_consensus
   (Bloomberg) durante el período del shock.

6. **Vista por defecto del dashboard:** ¿la app abre en v1, v2 o
   Comparativa? Probablemente v2 una vez que esté maduro y validado, pero
   conservar v1 accesible.

7. **Naming:** ¿conviene renombrar v1 → "Modelo de buffer (h)" y v2 →
   "Modelo de duración (T)" para evitar la sugerencia de "v2 reemplaza v1"?

---

**Fin del documento.**

Próximo paso: revisión del usuario y discusión de los puntos abiertos del
Apéndice C antes de iniciar la implementación.
