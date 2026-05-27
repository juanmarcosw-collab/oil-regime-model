# Modelo v1 — Régimen clásico vs. régimen de run con global game sobre $h$

**Versión:** v1.1 — draft autocontenido con 4 extensiones y Q&A (mayo 2026).
**Status:** Modelo actualmente implementado en el dashboard.
**Relación con v2:** v1 sitúa la incertidumbre sobre $h$ (buffer); v2 la
sitúa sobre $T$ (duración). Coexisten como pestañas distintas del dashboard.
**Documento previo:** este archivo extiende y actualiza `modelo_petroleo.pdf`
(versión 1 del paper); las variaciones respecto a ese documento se señalan
al cierre.

---

## Resumen ejecutivo

> *Modelo teórico-estructural que describe el precio del petróleo bajo un
> shock de oferta persistente (cierre del Estrecho de Ormuz), articulando
> dos regímenes en el plano $(h, P)$: un **régimen clásico** de storage
> theory donde la liberación de inventarios complementa la oferta corriente,
> y un **régimen de run** coordinado donde los tenedores de inventario
> retienen masivamente anticipando precios mayores. La transición entre
> regímenes es endógena y probabilística, modelada con un global game à la
> Goldstein-Pauzner (2005). El precio observado se modela como promedio
> ponderado de los dos regímenes, con peso dado por la probabilidad
> sigmoide $q(h) = \Phi((h^\ast - h)/\sigma)$. Output operativo: $\theta$
> implícito, la probabilidad de "normalización del shock" que el mercado
> está priciendo.*

**Tres frases clave para enmarcar la conversación:**

1. **Es teórico, no econométrico.** Da disciplina conceptual al precio del
   petróleo en escenarios de stress; no compite con VARs de pronóstico.
2. **El valor está en el wedge.** Comparar precio del modelo con precio
   observado da una lectura de las expectativas implícitas del mercado.
3. **Es trabajo en curso.** El v1 fija la arquitectura; las 4 extensiones
   implementadas y el v2 conceptual responden a sus limitaciones identificadas.

---

## 1. Introducción y objetivo

### 1.1. La pregunta operativa

> *Dado el nivel actual de buffer slack en el sistema, ¿cuál es el precio
> de equilibrio del petróleo, y cuánto sube si el buffer se sigue drenando?*

La pregunta parece simple pero esconde una sutileza. Si el sistema operara
siempre en régimen competitivo (con todos los agentes optimizando aisladamente),
el precio se calcularía con los modelos estándar de storage theory de
Deaton-Laroque o Pindyck. Pero hay episodios históricos —1990 (Kuwait), 2008
(peak de demanda china), 2022 (Ucrania)— donde los agentes exhibieron
comportamientos coordinados de hoarding que generaron movimientos de precios
mayores a lo justificable por los fundamentos físicos. Esa diferencia —entre el
precio clásico y el observado en episodios de stress— es lo que la literatura
llama *self-fulfilling crisis* o *coordinated run*, y es lo que necesitamos
incorporar.

### 1.2. El aporte conceptual: dos regímenes articulados

El modelo articula explícitamente:

1. **Régimen clásico:** equilibrio competitivo oferta-demanda con liberación
   normal de inventarios. Es el resultado del marco competitivo estándar.

2. **Régimen de run:** los tenedores retienen inventario anticipando precios
   futuros mayores, y otros agentes compiten por el inventario disponible. Es
   el resultado de la coordinación del global game de Morris-Shin.

**La transición entre regímenes no es continua:** ocurre como un salto
probabilístico cuando el buffer cruza un umbral crítico. El precio
efectivamente observado es un promedio ponderado entre los dos regímenes, con
peso dado por la probabilidad —endógena al modelo— de estar en cada uno.

### 1.3. Para qué sirve operativamente

Dos usos:

- **Tracking de $\theta$ implícito** como métrica diaria de expectativas
  de normalización extraídas del precio observado.
- **Análisis de escenarios:** qué pasa con el precio si $h$ cae a tal valor,
  o si el run se materializa.

---

## 2. Contexto empírico (mayo 2026)

Los hechos a la fecha de presentación (22-may-2026), tomados del último
reporte IEA OMR disponible (datos al 30-abril-2026):

| Hecho | Valor | Fecha del dato |
|---|---|---|
| Retiro de oferta global por cierre de Ormuz | $\sim 13{,}6\%$ | — |
| Oferta de flujo durante shock $S_{f,0}$ | $\sim 95$ mb/d (vs. $\sim 104$ pre-guerra) | — |
| Inventarios globales (IEA OMR) | 7.951 mb (vs. 8.150 mb en enero) | **30-abril-2026** |
| Ritmo de drenaje marzo-abril | $\approx 4$ mb/d | OMR |
| Stock_floor operacional (JPMorgan) | 6.800 mb | — |
| Stock_stress threshold (JPMorgan) | 7.600 mb | — |
| Spare capacity OPEC+ | mínimo histórico (170 kb/d) | abril |
| Brent forward M1-M12 | backwardation extrema | 30-abril |
| Precio spot Brent | 124,24 USD/bbl (FRED) / 122,58 (Bloomberg M1) vs. 70 pre-guerra | **30-abril-2026** |

**Observación crucial:** el long-end de la curva forward Brent ya cotiza
modestamente arriba de pre-guerra (dic-28 $\approx 76$ USD/bbl, solo 6
arriba), mientras el spot está en 124,24 (FRED). Esa diferencia, combinada con el
shock físico, es la observación que motiva el modelo. **Si el mercado priciara
el shock como persistente indefinidamente, los precios deberían ser
materialmente mayores.** La diferencia entre lo que el modelo predice (bajo
persistencia) y lo que el mercado cotiza nos da una estimación de la
probabilidad implícita de resolución del shock.

---

## 3. Marco conceptual: alcance y supuestos

El modelo tiene tres características metodológicas que conviene explicitar:

**Es teórico-estructural.** Da un mapa de relaciones entre estado del sistema
y precios. No se estima con datos históricos; se calibra con literatura y
juicio. Su contraparte natural sería un DSGE, no un VAR.

**Es estático.** Tomamos una foto del mercado en un instante. No modelamos
cómo los inventarios se drenan en el tiempo. La pregunta es: *dado este
nivel de buffer ahora, ¿cuál es el precio de equilibrio ahora?* Es una
limitación deliberada para mantener tractable la matemática. La Extensión 3
introduce dinámica temporal sin romper el core estático.

**Es de equilibrio parcial.** Modelamos solo el mercado del petróleo. La
economía global, otros commodities, política monetaria y respuestas
regulatorias son exógenas. No capturamos efectos de segunda ronda.

**Está condicional al cierre persistente de Ormuz.** Asumimos $S_f = 95$
mb/d como constante durante el horizonte de análisis. Si Ormuz reabriera,
todos los números cambiarían: la oferta volvería hacia 104 mb/d y el precio
caería hacia 70 USD/bbl con buffer abundante. **El modelo describe un mundo
paralelo donde el cierre persiste.** El wedge con el precio observado captura
indirectamente las expectativas del mercado sobre resolución del shock.

---

## 4. Variables y parámetros

### 4.1. La variable de estado: buffer slack $h$

El **buffer slack** $h$ es la variable de estado principal del modelo. Mide
cuánto inventario tiene el sistema por encima del mínimo operativo.
Formalmente (Ext 2; ver §13.2):

$$h(\text{Stock}) = h^\ast \cdot
  \frac{\text{Stock} - \text{Stock}_{\rm floor}}
       {\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}$$

con Stock_floor = 6.800 mb (mínimo operacional JPM), Stock_stress = 7.600 mb
(threshold de stress JPM), $h^\ast = 0{,}30$. **$h$ es adimensional.**

> *Anclaje empírico clave: identificamos el umbral teórico del global game
> $h^\ast$ con el threshold de stress operacional de JPMorgan.*

Ejemplos numéricos con stock al 30-abril-2026 (último IEA OMR):

- Stock = 7.951 mb → $h \approx 0{,}43$.
- Stock = 7.600 mb → $h = h^\ast = 0{,}30$.
- Stock = 6.800 mb → $h = 0$.

**En el límite $h \to 0$:** el inventario llegó al mínimo operativo, no a
cero. La producción del día sigue ocurriendo; lo que se acabó es el colchón
para complementar la oferta corriente.

### 4.2. El ritmo de liberación $\dot R(h)$

El **ritmo de liberación** $\dot R(h)$ es un flujo (mb/d) que indica cuánto
inventario sale del pool agregado hacia el mercado por día. Es función del
buffer disponible:

$$\dot R(h) = R_{\max} \cdot \frac{h}{h + h_R}$$

Forma funcional Michaelis-Menten. Tres propiedades:

1. $\dot R(0) = 0$ — no se puede liberar lo que no se tiene.
2. $\dot R(h_R) = R_{\max}/2$ — $h_R$ es la half-saturation constant.
3. $\dot R(h) \to R_{\max}$ — saturación logística.

> *$R_{\max}$ controla la altura (capacidad de pico); $h_R$ controla la
> curvatura (qué tan rápido satura).*

Calibración: $R_{\max} = 6$ mb/d (capacidad histórica de releases coordinados
G7), $h_R = 0{,}12$ (calibrado para que a $h \approx 0{,}24$ el release sea
$\approx 4$ mb/d, matcheando OMR de marzo-abril 2026).

### 4.3. La demanda $D(P)$

Forma de elasticidad constante:

$$D(P) = D_0 \cdot (P/P^\ast)^{-\varepsilon_d}$$

con $D_0 = 104$ mb/d, $P^\ast = 70$ USD/bbl, $\varepsilon_d = 0{,}05$. La
elasticidad short-run es baja porque el consumo es esencial y poco
sustituible.

**Box — Caldara, Cavallo & Iacoviello (2019) — "Oil Price Elasticities and
Oil Price Fluctuations", *Journal of Monetary Economics***

> *Qué modela:* estimación estructural de elasticidades short-run en el
> mercado global del petróleo, usando shocks geopolíticos como instrumentos.
> *Supuestos clave:* elasticidad constante; shocks geopolíticos válidos
> como instrumentos.
> *Resultado central:* demand elasticity en rango 0,08-0,20; supply
> similar.
> *Por qué nos sirve:* establece el rango plausible de elasticidades. Usamos
> $\varepsilon_d = 0{,}05$ (debajo del rango) porque el shock actual desplaza
> 13,6% de la oferta mundial; bajo shocks de magnitud sin precedentes la
> elasticidad efectiva cae.

### 4.4. La oferta de flujo $S_f(P)$

Análogamente:

$$S_f(P) = S_{f,0} \cdot (P/P^\ast)^{\varepsilon_s}$$

con $S_{f,0} = 95$ mb/d, $\varepsilon_s = 0{,}04$. La oferta es aún menos
elástica que la demanda en el short-run por las inversiones de largo plazo
requeridas para expandir capacidad.

**Importante:** $S_{f,0}$ está definida *durante el shock* (Ormuz cerrado).
Si Ormuz reabriera, $S_{f,0}$ saltaría hacia $\approx 104$ mb/d.

---

## 5. El régimen clásico: storage theory en el plano $(h, P)$

### 5.1. La condición de equilibrio

El mercado se vacía cuando lo que se consume iguala a lo que se produce más
lo que sale de los stocks:

$$\underbrace{D(P_C)}_{\rm consumo} \;=\; \underbrace{S_f(P_C)}_{\rm producción} \;+\; \underbrace{\dot R(h)}_{\rm sale\ de\ stocks}$$

Para cada $h$, hay un único $P_C(h)$ que satisface la condición (encontrado
numéricamente con root-finding).

**Box — Storage theory: la línea Working-Brennan-Deaton-Laroque-Pindyck**

> *De qué se trata:* familia de modelos que estudian cómo el almacenamiento
> privado de un commodity media entre oferta producida y demanda consumida.
> Working (1949) y Brennan (1958) introducen el *cost of storage* y el
> *convenience yield*. Deaton-Laroque (1992, 1996) formalizan el modelo con
> expectativas racionales y restricción de no-negatividad de inventarios.
> *Resultado central:* precios spot no lineales — suaves con inventarios
> abundantes, altamente convexos cerca del stockout.
> *Por qué nos sirve:* es la pieza analítica que determina $P_C(h)$. La
> no-linealidad cerca de $h = 0$ es la firma teórica de la storage theory.

### 5.2. Comportamiento en los extremos

**Para $h$ grande (mucho buffer):** $\dot R \to R_{\max}$ y la oferta total
es $S_f(P) + R_{\max}$. Esto da el **piso del modelo** $P_{\rm floor}$:

$$P_{\rm floor} \approx 95 \text{ USD/bbl con calibración default}$$

**Para $h \to 0$ (buffer agotado):** $\dot R \to 0$. El equilibrio se
reduce a $D(P) = S_f(P)$. Solución cerrada:

$$\frac{P_{\rm cap}}{P^\ast} = \left(\frac{D_0}{S_{f,0}}\right)^{1/(\varepsilon_d + \varepsilon_s)}$$

Con $\varepsilon_d = 0{,}05$, $\varepsilon_s = 0{,}04$:

$$P_{\rm cap} = 70 \cdot (104/95)^{1/0{,}09} \approx 70 \cdot 2{,}73 \approx 191 \text{ USD/bbl}$$

Este es el **cap clásico**: el precio al cual la demanda se acomoda
completamente a la oferta de flujo sin necesidad de inventario suplementario.
Es finito y derivado endógenamente del modelo, no es un supuesto exógeno.

### 5.3. Convenience yield emergente

Una virtud notable: el convenience yield aparece como consecuencia, no como
supuesto. Definimos:

$$\psi(h) = P_C(h) - P_{\rm floor}$$

Con la calibración, $\psi(h)$ va de $\approx 0$ (cuando $h$ es grande, sin
escasez percibida) hasta $\psi(0) \approx 96$ USD/bbl (cuando $h = 0$, máximo
costo de oportunidad de no tener inventario). Esto se conecta con la backwardation
extrema observada en Brent (M1-M12 en zonas de stress), interpretable como
convenience yield empírico.

---

## 6. El régimen de run: coordinación y self-fulfilling crisis

### 6.1. La lógica del run

Imaginá que tenés un barril en stock y observás que el sistema está bajo
stress. Tenés dos opciones: liberar el barril hoy (y cobrar el precio
actual), o retenerlo esperando que el precio suba más. Si pensás que muchos
otros agentes harán lo mismo, te conviene retener vos también, porque la
retención agregada *causa* la subida del precio que esperás.

> *Esto es la dinámica de expectativas auto-cumplidas, el corazón de los
> modelos de runs. Hay múltiples equilibrios potenciales: "nadie retiene"
> (precio en $P_C$) y "todos retienen" (precio en $P_R > P_C$). La pregunta
> es cuál se materializa.*

**Box — Diamond & Dybvig (1983) — "Bank Runs, Deposit Insurance, and
Liquidity", *Journal of Political Economy***

> *Qué modela:* banco que ofrece depósitos demandables pero invierte en
> activos ilíquidos.
> *Resultado central:* existen dos equilibrios — uno benigno (clientes
> retiran solo lo necesario) y uno catastrófico (corrida).
> *Por qué nos sirve:* es el ancestro teórico de la idea de run. La
> estructura — múltiples equilibrios con uno catastrófico, transición
> disparada por expectativas — se aplica directamente al petróleo con $B$
> jugando el rol del fondo del banco y los tenedores de inventario jugando
> el rol de los depositantes.

### 6.2. La unicidad del equilibrio: Morris-Shin

El problema de Diamond-Dybvig es que predice múltiples equilibrios pero no
dice cuándo se materializa cada uno. Morris-Shin (1998) resuelven esto
introduciendo **información privada heterogénea**: cada agente recibe una
señal ruidosa sobre el fundamental, y la decisión óptima depende de la señal
recibida.

**Box — Morris & Shin (1998) — "Unique Equilibrium in a Model of
Self-Fulfilling Currency Attacks", *AER***

> *Qué modela:* ataque especulativo a una moneda fija. Cada especulador
> decide individualmente si atacar basado en su señal privada.
> *Supuestos clave:* información privada heterogénea, complementariedades
> estratégicas.
> *Resultado central:* a diferencia del modelo de información común (con
> equilibrios múltiples), el modelo con información privada tiene un **único
> equilibrio en estrategias de umbral**. Existe un valor crítico $\theta^\ast$
> tal que: para $\theta > \theta^\ast$, nadie ataca; para $\theta < \theta^\ast$,
> todos atacan.
> *Por qué nos sirve:* provee la pieza teórica que cierra el problema de
> los equilibrios múltiples. Aplicado al petróleo: existe un umbral $h^\ast$
> tal que para $h > h^\ast$ el sistema opera en régimen clásico, y para
> $h < h^\ast$ entra en run coordinado.

### 6.3. La probabilidad de run: Goldstein-Pauzner

Morris-Shin establece el umbral pero su versión original es discreta.
Goldstein-Pauzner (2005) llevan el marco a un setup multi-agente más
estructural y derivan la **probabilidad de run en función del fundamental**.

**Box — Goldstein & Pauzner (2005) — "Demand-Deposit Contracts and the
Probability of Bank Runs", *Journal of Finance***

> *Qué modela:* Diamond-Dybvig con información privada heterogénea, en el
> marco de global games de Morris-Shin.
> *Resultado central:* en el límite de noise pequeño, la probabilidad de
> run condicional al fundamental $h$ adopta la forma cerrada
>
> $$q(h) = \Phi\!\left(\frac{h^\ast - h}{\sigma}\right)$$
>
> donde $\Phi$ es la CDF normal estándar y $\sigma$ refleja la dispersión
> de señales privadas.
> *Por qué nos sirve:* provee la función $q(h)$ que necesitamos para
> promediar entre los dos regímenes. La sigmoidalidad de $q(h)$ captura
> suavemente la transición, y los parámetros $h^\ast$ y $\sigma$ son
> interpretables económicamente.

### 6.4. El precio en régimen de run

Modelamos la condición de equilibrio del run análogamente al clásico, pero
con dos modificaciones:

$$\underbrace{D(P_R) + \delta(h)}_{\rm demanda\ ampliada} \;=\; \underbrace{S_f(P_R) + (1 - \mu) \dot R(h)}_{\rm oferta\ reducida}$$

donde:

- $\mu \in [0, 1]$ es la fracción del release retenida por hoarders. Si
  $\mu = 0$, no hay retención y el régimen colapsa al clásico. Si $\mu = 1$,
  todo el release se retiene.
- $\delta(h) = \delta_0 \cdot \dot R(h)/R_{\max}$ es la demanda especulativa
  adicional. Calibración default: $\delta_0 = 0$ (neutral).

**Observación importante (convergencia en stockout):** cuando $h \to 0$,
tanto $(1-\mu)\dot R(h) \to 0$ como $\delta(h) \to 0$. La ecuación se reduce
a $D(P_R) = S_f(P_R)$, idéntica al régimen clásico en $h = 0$. Esto implica
$P_R(0) = P_C(0) = P_{\rm cap}$.

> *El régimen de run es un fenómeno transitorio que afecta la trayectoria
> pero no el destino del precio. Una vez agotado el buffer, no importa cómo
> se llegó al stockout: el precio queda determinado solo por el equilibrio
> flujo a flujo.*

---

## 7. El precio observado: composite y probabilidad de régimen

El precio observado en cualquier momento es un promedio ponderado entre los
dos regímenes, con pesos dados por las probabilidades de estar en cada uno:

$$\boxed{\;P(h) = (1 - q(h)) \cdot P_C(h) \;+\; q(h) \cdot P_R(h)\;}$$

con $q(h) = \Phi((h^\ast - h)/\sigma)$.

Tres regiones cualitativas:

| Región | $h$ | $q$ | $P(h)$ |
|---|---|---|---|
| **Régimen normal** | $h \gg h^\ast$ | $\approx 0$ | $\approx P_C(h)$ |
| **Zona de fragilidad** | $h \approx h^\ast$ | en transición | mezcla |
| **Régimen de run** | $h \ll h^\ast$ | $\approx 1$ | $\approx P_R(h)$ |

La derivada $\partial P / \partial h$ es máxima (en valor absoluto) en la
zona de fragilidad. Una caída pequeña en $h$ alrededor de $h^\ast$ produce
un movimiento grande en $P$.

---

## 8. Calibración (actualizada a mayo 2026)

### 8.1. Parámetros bien anclados en literatura

| Parámetro | Valor | Fuente |
|---|---|---|
| $\varepsilon_d$ | 0,05 | Caldara et al. (2019), rango bajo para shocks extremos |
| $\varepsilon_s$ | 0,04 | Consistente con baja elasticidad short-run |
| $D_0$ | 104 mb/d | IEA OMR pre-guerra (enero 2026) |
| $S_{f,0}$ | 95 mb/d | IEA OMR durante shock |
| $P^\ast$ | 70 USD/bbl | Brent promedio mensual pre-guerra (feb 2026) |

### 8.2. Parámetros calibrados con observaciones contemporáneas

| Parámetro | Valor | Fuente / método |
|---|---|---|
| $R_{\max}$ | 6 mb/d | Capacidad histórica de releases coordinados IEA |
| $h_R$ | 0,12 | Calibrado para que $\dot R$ matchee OMR marzo-abril 2026 |
| Stock_floor | 6.800 mb | Operational floor JPMorgan |
| Stock_stress | 7.600 mb | Stress threshold JPMorgan |
| Stock_opt | 8.200 mb | Nivel post-acumulación 2025 (Ext 4) |

### 8.3. Parámetros del global game

| Parámetro | Valor | Fuente / método |
|---|---|---|
| $h^\ast$ | 0,30 | Anclado al Stock_stress JPM vía Ext 2 |
| $\sigma$ | 0,08 | Calibración cualitativa; **parámetro débil** (motivación del v2) |

**Nota importante sobre $h^\ast$:** el modelo es invariante a re-escalamientos
del eje $h$. El valor 0,30 es una elección de normalización; lo identificable
es el anclaje a Stock_stress (ver §17 Q&A.5).

### 8.4. Parámetros del run regime

| Parámetro | Valor | Fuente / método |
|---|---|---|
| $\mu$ | 0,5 | Heurístico; mitad de los holders retiene |
| $\delta_0$ | 0 | Simplificación inicial; sin demanda especulativa adicional |

### 8.5. Parámetros nuevos de las Extensiones

| Parámetro | Valor | Uso |
|---|---|---|
| $R_{\rm repl,max}$ | 5 mb/d | Demanda de reposición saturada (Ext 4) |
| $\theta_{\rm exógeno}$ | input usuario | Probabilidad de normalización para $P_{\rm esp}$ (Ext 1) |

---

## 9. Resultados con calibración actual

Con la calibración descrita y $h_{\rm actual} = 0{,}43$ (Stock = 7.951 mb, IEA OMR al 30-abril-2026):

| Magnitud | Valor |
|---|---|
| $P_{\rm cap}$ (h → 0, sin release) | $\approx 191$ USD/bbl |
| $P_{\rm floor}$ (h grande, release máximo) | $\approx 95$ USD/bbl |
| Piso del régimen run (h grande) | $\approx 128$ USD/bbl |
| $\dot R(h_{\rm actual})$ | $\approx 4{,}7$ mb/d |
| $P_C(h_{\rm actual})$ | $\approx 113$ USD/bbl |
| $P_R(h_{\rm actual})$ | $\approx 147$ USD/bbl |
| $q(h_{\rm actual})$ | $\approx 0{,}05$ |
| **Precio composite $P(h_{\rm actual})$** | $\approx 115$ USD/bbl |
| **Precio Brent observado al 30-abril-2026** | 124,24 USD/bbl (FRED) |

> *Lectura: al stock observado actual estamos **por encima del umbral de
> fragilidad** ($h = 0{,}43$ > $h^\ast = 0{,}30$). El sistema opera
> principalmente en régimen clásico bajo shock. El precio del modelo
> ($\approx 115$) está **por debajo** del observado (124,24 USD/bbl, FRED),
> lo cual implica un wedge negativo (≈ −9,2 USD/bbl) — el mercado pricea
> más severidad que la que el modelo predice (ver §10).*

---

## 10. El wedge modelo-observado: el parámetro $\theta$

El precio composite es lo que el mercado cotizaría si todos los participantes
creyeran que Ormuz queda cerrado indefinidamente. El precio observado, en
cambio, incorpora la probabilidad subjetiva del mercado de que Ormuz reabra.

Si denotamos $\theta$ a la probabilidad implícita de normalización:

$$P_{\rm mercado}(h, \theta) = (1 - \theta) \cdot P(h) + \theta \cdot P^\ast$$

Despejando $\theta$ desde los valores observados:

$$\theta = \frac{P(h) - P_{\rm mercado}}{P(h) - P^\ast}$$

**Con la calibración actual** ($P(h) = 115$, $P_{\rm mercado} = 124{,}24$ FRED, $P^\ast = 70$):

$$\theta = \frac{115 - 124{,}24}{115 - 70} = \frac{-9{,}24}{45} \approx -0{,}21$$

> *Lectura: el wedge es **negativo** y $\theta_{\rm implícito}$ cae fuera del
> rango interpretable [0,1] como probabilidad genuina. **El mercado pricea
> más severidad/persistencia que la que el modelo capta**.*

**Cuatro hipótesis no-excluyentes para explicar el wedge negativo:**

1. **El modelo subestima la fragilidad** a $h_{\rm actual}$. El anclaje
   $h^\ast \leftrightarrow$ Stock_stress = 7.600 mb puede ser conservador;
   un $h^\ast$ más alto (umbral más cercano al estado actual) movería el
   composite hacia $P_R$ y reduciría el gap.

2. **Risk premium positivo no modelado.** Hay literatura empírica sobre
   primas de cobertura, demanda precautoria de inventario y compensaciones
   por incertidumbre que no entran en este modelo de equilibrio spot.

3. **Las elasticidades pueden ser aún más bajas.** Bajar $\varepsilon_d$ o
   $\varepsilon_s$ sube tanto $P_{\rm cap}$ como el composite. Si la
   elasticidad efectiva bajo shock extremo es ~0,02-0,03, el composite se
   acercaría al observado.

4. **El régimen de run podría estar parcialmente activo.** Subir $\mu$
   efectiva (más holders reteniendo) o introducir $\delta_0 > 0$ (demanda
   especulativa) eleva $P_R(h)$ y, por tanto, el composite.

Este hallazgo es **diagnóstico**: el wedge negativo no invalida el modelo,
señala canales que requieren refinamiento. Es exactamente el tipo de
desajuste empírico que motiva las extensiones y el v2.

**Cross-check con Bloomberg** (M1 settlement): a 30-abril Bloomberg da
122,58 USD/bbl. Diferencia con FRED (~1,7) es típica entre spot EIA y M1
settlement ICE; cualquiera de los dos da wedge negativo materialmente
similar (θ ≈ −0,17 con Bloomberg).

**Comparación con calibraciones previas:** con la calibración original del
PDF v1 (que usaba un anclaje distinto para $h$, dando $h \approx 0{,}24$
y poniéndonos en la zona de fragilidad), el composite era $\approx 136$ y
$\theta$ implícito $\approx 0{,}39$. La diferencia se debe a la actualización
del mapeo $h \leftrightarrow$ stock (Ext 2; ver §13.2). Esto se discute más
en §16.

El $\theta$ es testeable contra fuentes independientes:
- Probabilidad implícita en opciones de Brent.
- Surveys de consenso (Bloomberg, Reuters).
- Indices de geopolitical risk.

---

## 11. Extensiones implementadas (sobre el paper original)

El dashboard implementa cuatro extensiones documentadas detalladamente en
`modelo_extensiones.md`. Resumen acá:

### 11.1. Ext 1 — Parametrización dual de $\theta$

El paper define $\theta$ por despeje (output diagnóstico). La extensión
permite también usarlo como input exógeno:

$$P_{\rm esp}(h) = (1 - \theta) \cdot P(h) + \theta \cdot P^\ast(h)$$

Permite responder *"si el mercado priciera $\theta = 0{,}4$, ¿qué precio se
observaría?"* — útil para análisis contrafactual.

### 11.2. Ext 2 — Mapeo lineal stock ↔ $h$

Anclaje empírico de $h$ al Total Global Observed Inventories de IEA:

$$h(\text{Stock}) = h^\ast \cdot
  \frac{\text{Stock} - \text{Stock}_{\rm floor}}
       {\text{Stock}_{\rm stress} - \text{Stock}_{\rm floor}}$$

Con Stock_floor = 6.800 (JPM) y Stock_stress = 7.600 (JPM). **Esta extensión
es la que define los números del §9.** Reemplaza la calibración heurística
$h = (B - B_{\min})/B_{\min}$ del PDF original.

### 11.3. Ext 3 — Dinámica temporal P(t)

Bajo shock persistente, el stock se drena según:

$$\frac{d\,\text{Stock}}{dt} = -\dot R\!\left(h(\text{Stock})\right)$$

Integración numérica desde el stock observado. Para cada $t$ se computa
$P_C(t)$, $P_R(t)$, $P(t)$ y $P^\ast(t)$. Da trayectorias proyectadas y
fechas de cruce de thresholds.

### 11.4. Ext 4 — Demanda de reposición: $P^\ast(\text{Stock})$ variable

Si Ormuz reabre con stocks bajos, hay demanda extra para reponer. El
equilibrio Ormuz-abierto deja de ser $P^\ast = 70$ USD/bbl constante:

$$D(P^\ast) + R_{\rm repl}(\text{Stock}) = S_{\rm open}(P^\ast)$$

con $R_{\rm repl}$ saturada lineal en el gap stock vs. Stock_opt. Hace
endógeno el "piso post-shock": cuanto más bajos los stocks al momento de
la resolución, mayor el precio de reapertura.

---

## 12. Lectura de las figuras del dashboard

### 12.1. Figura 1 — Precio vs. buffer (h, P)

- **Eje x:** $h$, recorre [0, 1,5] como parámetro abstracto (no es un dato
  observado).
- **Líneas:**
  - **Verde continua:** $P_C(h)$, régimen clásico.
  - **Roja punteada:** $P_R(h)$, régimen de run.
  - **Negra:** $P(h)$ composite.
  - **Morada:** $P^\ast(h)$ con reposición (Ext 4).
- **Marcador:** precio Brent observado al 30-abril-2026 (124,24 USD/bbl,
  FRED), plantado en $h_{\rm actual} = 0{,}43$ derivado del stock IEA OMR
  del mismo día. Ambos vienen del último OMR disponible al momento de la
  presentación (22-may-2026).
- **Bandas verticales:** zona de fragilidad alrededor de $h^\ast$.

### 12.2. Figura 2 — Trayectoria temporal P(t)

- **Eje x:** fechas calendario desde la fecha de la observación inicial
  (30-abril-2026 por default).
- **Eje y:** precio.
- **Líneas:** las mismas cuatro de Figura 1, pero proyectadas en el tiempo
  bajo shock persistente (Ext 3).

### 12.3. Figura 3 — Evolución del stock

- **Eje x:** fechas.
- **Eje y:** stock global (mb).
- **Línea:** trayectoria simulada de drenaje.
- **Horizontales:** Stock_stress (7.600), Stock_floor (6.800).
- **Marcadores:** fechas de cruce de cada threshold.

---

## 13. Limitaciones

Tres limitaciones importantes que ordenan futuras extensiones:

**13.1. Estaticidad.** El modelo no captura la trayectoria $h_t \to h_{t+1}$.
La Ext 3 introduce dinámica del stock pero el equilibrio del global game
sigue siendo snapshot. El framework natural para una dinámica completa es
Williams-Wright (1991) ampliado con global game, en línea con Bocola-Lorenzoni
(2020).

**Box — Bocola & Lorenzoni (2020) — "Financial Crises, Dollarization, and
Lending of Last Resort in Open Economies", *AER***

> *Qué modela:* crisis financieras en economías emergentes con dolarización
> de pasivos. Combina dinámica de rollover risk con multi-equilibria tipo run.
> *Por qué nos sirve:* es el antecedente metodológico más cercano a una
> extensión dinámica de nuestro modelo.

**13.2. Calibración del run.** Los parámetros $\mu$ y $\delta_0$ están
débilmente disciplinados por la literatura. Un esfuerzo serio requeriría:
episodios históricos de hoarding institucional (1990 fue el más claro),
data de microestructura del mercado durante stress, y datos de posicionamiento
financiero (CFTC managed money).

**13.3. Calibración débil de $\sigma$.** La dispersión informacional sobre $h$
no es identificable empíricamente con datos públicos abundantes (IEA, EIA,
JODI publican stocks). **Esta es la motivación principal del v2**: sitúa la
incertidumbre sobre $T$ (duración), que sí es identificable contra surveys y
forwards.

**13.4. Single-country reduced form.** El modelo agregado no captura
heterogeneidad entre orígenes de petróleo (Brent, WTI, Dubai) ni entre
regiones de consumo. La extensión natural es trasladar la lógica de los dos
regímenes al setup multi-país.

---

## 14. Hoja de ruta: del v1 al v2

El v2 (documentado en `modelo_v2_incertidumbre_T.md`) reformula el global
game sobre $T$ (duración del shock) en lugar de $h$. Tabla comparativa:

| Aspecto | v1 (este doc) | v2 |
|---|---|---|
| Variable incierta | $h$ (buffer) | $T$ (duración) |
| Identificación empírica | Débil (stocks son públicos) | Fuerte (surveys, forwards) |
| Parámetro débil | $\sigma$ (placeholder) | ninguno fundamental |
| $h^\ast$ | parámetro libre (normalización) | derivable de $\tau_{\rm crítico}$ |
| Output diagnóstico | $\theta$ implícito (adimensional) | $\mathbb{E}[T]$ implícito (días) |
| Movimiento del precio | solo por cambio en $h$ o estructurales | también por noticias sobre $T$ |
| Status | implementado | conceptual; implementación pendiente |

Ambos coexisten como pestañas del dashboard. **El v1 mantiene valor pedagógico
y como benchmark; el v2 será la vista operacional principal una vez
implementado.**

---

## 15. Q&A — Preguntas conceptuales clave

### Q1 — Si todos saben que Ormuz está cerrado, ¿por qué el precio no salta al cap ($\approx 191$)?

> *Porque el precio del modelo es un equilibrio spot de flujo período-a-período,
> no de arbitraje intertemporal puro. Mientras $h$ sea alto, $\dot R$
> compensa parte de la oferta perdida y el precio queda contenido. El cap es
> un punto al que el sistema **llega trayectoriado**, no al que salta.*

Razones por las que el no-arbitrage clásico no aplica:

1. El petróleo no es un activo financiero perfectamente almacenable.
2. SPRs no son tradeable; hay frictions logísticas y políticas.
3. El no-arbitrage no aplica estrictamente; lo que aplica es market clearing
   de flujo cada período.

El "salto" del precio sí aparece — en la zona de fragilidad, donde $q(h)$
sube rápidamente y el composite se desplaza hacia $P_R$. Pero es suavizado
por $\sigma$, no discontinuo.

### Q2 — ¿Qué información tiene cada agente?

Tres tipos:

- **Consumidores y oferentes (price-takers):** observan precio $P_t$,
  responden con $D(P)$ y $S_f(P)$. No tienen información estratégica relevante.
- **Tenedores de inventario en régimen clásico:** siguen una regla
  *reduced-form* $\dot R(h)$. No optimizan explícitamente; sintetizan
  coordinación implícita (SPRs, IEA, refinerías).
- **Tenedores en régimen de run:** cada uno recibe una señal privada
  $s_i = h + \varepsilon_i$ con $\varepsilon_i \sim \mathcal{N}(0, \sigma^2)$.
  Conoce su señal y la distribución del ruido, pero no $h$ verdadero.

### Q3 — ¿Cuándo se juega el global game?

Conceptualmente, en cada instante. Operativamente, el modelo lo trata como un
juego **estático para un $h$ dado**: la solución produce $q(h)$, que es la
probabilidad de que se materialice el run en ese estado. El precio composite
$P(h)$ es la expectativa del precio dada la incertidumbre sobre cuál régimen
se realiza.

### Q4 — ¿En qué consiste exactamente el game?

- **Acción binaria:** cada agente elige liberar (L) o retener (R).
- **Payoffs:** dependen de la fracción agregada que retiene. Si pocos
  retienen, el precio queda en $P_C$ y retener no fue rentable. Si muchos
  retienen, el precio salta a $P_R$ y retener fue rentable.
- **Equilibrio:** en estrategias monótonas — cada agente retiene sii su
  señal $s_i < s^\ast$ (sospecha que $h$ es bajo).
- **En el límite $\sigma \to 0$:** $s^\ast \to h^\ast$, regla de threshold limpia.
- **Para $\sigma > 0$:** transición suave; $q(h) = \Phi((h^\ast - h)/\sigma)$.

### Q5 — ¿Por qué $h^\ast = 0{,}30$ exactamente?

> *Es una elección de escala, no un valor derivado. El modelo es invariante
> a re-escalamientos del eje $h$: podrías elegir $h^\ast = 1$ con resultados
> idénticos (con $\sigma$ y $h_R$ re-escalados).*

Lo que **sí es sustantivo** es el anclaje empírico vía Ext 2: identificamos
$h^\ast$ con el threshold de stress operacional JPMorgan (7.600 mb). Eso es
una hipótesis testeable, no una convención.

En el v2, este parámetro **desaparece como elección libre** porque queda
determinado endógenamente como $\tau_{\rm crítico}(\text{Stock}_0)$.

### Q6 — ¿Cómo se calcula $h$ en el modelo y en el dashboard?

**$h$ como variable independiente** (eje x de Figura 1): se barre con
`np.linspace(0.001, 1.5, 600)`. No se "calcula", es la variable.

**$h_{\rm actual}$ (marcador del punto observado):** vía Ext 2:

$$h_{\rm actual} = 0{,}30 \cdot \frac{7{.}951 - 6{.}800}{7{.}600 - 6{.}800} \approx 0{,}43$$

### Q7 — ¿Por qué Michaelis-Menten para el release?

Forma funcional minimal que cumple las tres propiedades necesarias:
$\dot R(0) = 0$, monótona creciente, saturada en $R_{\max}$. Un parámetro
de altura ($R_{\max}$) y uno de curvatura ($h_R$). Alternativas (sigmoide,
$1 - e^{-h/h_R}$) cumplen lo mismo pero requieren más parámetros o son más
opacas.

### Q8 — ¿La crítica de Lucas no aplica?

Aplica parcialmente. Las elasticidades calibradas son short-run, derivadas
de shocks pasados; cambios de política podrían moverlas. Pero el horizonte
del modelo es de pocos meses, donde la asunción de elasticidades estables
es defensible.

### Q9 — ¿Qué tan sensible es el resultado a $\sigma$?

Muy sensible. Con $\sigma = 0{,}04$ la transición entre regímenes es
abrupta; con $\sigma = 0{,}15$ es muy suave. Es el parámetro más débilmente
identificado y el más influyente sobre la lectura de $\theta$ en la zona de
fragilidad. Es una de las motivaciones del v2.

### Q10 — ¿Hay tests unitarios / validación?

Sí. Tests verifican propiedades matemáticas clave:
- $P_C(0) \approx P_{\rm cap}$.
- $P_C(\infty) \approx P_{\rm floor}$.
- $P_R(0) = P_C(0)$ (convergencia en stockout).
- $q(h^\ast) = 0{,}5$.
- $\theta > 0$ cuando $P_{\rm modelo} > P_{\rm observado}$.

**Lo que no se validó formalmente:** ajuste contra episodios históricos
(1990, 2008, 2022). Esto requiere mapear $h$ en cada episodio, que sería un
trabajo empírico autónomo identificado como extensión futura.

### Q11 — ¿El modelo es código abierto?

Sí. Repo en GitHub (`oil-regime-model`); dashboard en Streamlit Community
Cloud.

### Q12 — ¿Qué nos dice el modelo sobre el riesgo actual (mayo 2026)?

> *Con stock = 7.951 mb (IEA OMR al 30-abril), $h \approx 0{,}43$ — por
> encima del umbral de fragilidad ($h^\ast = 0{,}30$). El sistema opera
> principalmente en régimen clásico bajo shock. Composite del modelo ≈ 115;
> precio Brent observado al 30-abril = 124,24 (FRED) / 122,58 (Bloomberg M1).
> El wedge es **negativo** ($\theta_{\rm implícito} \approx -0{,}21$): el
> mercado pricea más severidad que la que el modelo capta. Esto sugiere
> al menos uno de cuatro canales mal calibrados (ver §10): $h^\ast$ debería
> estar más cerca del estado actual, hay risk premium no modelado,
> elasticidades aún más bajas, o el run regime está parcialmente activo.*

**Punto de atención:** si el stock cae bajo 7.600 mb (zona de fragilidad),
$q$ subiría rápidamente y el modelo se desplazaría hacia $P_R \approx 147$
USD/bbl. La distancia al umbral es $\sim 351$ mb, equivalente a $\sim 75-90$
días al ritmo actual.

---

## 16. Diferencias respecto al PDF original (v1.0)

Este documento extiende y actualiza `modelo_petroleo.pdf` (mayo 2026,
versión 1). Los cambios materiales son:

| Cambio | PDF v1.0 | Este doc v1.1 |
|---|---|---|
| $\varepsilon_s$ | 0,05 | **0,04** |
| $P_{\rm cap}$ | 173 USD/bbl | **191 USD/bbl** |
| Mapeo $h$ ↔ stock | $h = (B - B_{\min})/B_{\min}$ con $B_{\min} = 6.500$ | **Ext 2** (anclaje a JPM thresholds) |
| $h_{\rm actual}$ estimado | $\approx 0{,}22$ | **$\approx 0{,}43$** |
| Régimen del estado actual | fragilidad ($h < h^\ast$) | **clásico ($h > h^\ast$)** |
| Composite a $h_{\rm actual}$ | $\approx 136$ USD/bbl | **$\approx 115$ USD/bbl** |
| $\theta$ implícito | $\approx 0{,}39$ | **$\approx 0{,}02$** |
| Extensiones | no documentadas | **4 documentadas** (§11) |
| Q&A | no | **incluido** (§15) |
| Datos al cierre | mayo 2026 (P=110) | **30-abril-2026 (P=124,24 FRED, stock=7.951); presentado 22-may** |
| Referencias institucionales (BCCh, DPM) | sí | **removidas** |

**El cambio más significativo es la actualización del mapeo $h$ ↔ stock**.
La calibración del PDF v1.0 ponía al sistema en la zona de fragilidad con
$\theta$ alto; la calibración actual (Ext 2 + datos del 30-abril) lo pone en
régimen clásico bajo shock con $\theta$ muy bajo. Esto refleja una **revisión
del anclaje del umbral del global game** a los thresholds operacionales
JPMorgan, que es más defensible empíricamente que el anclaje original.

---

## Apéndice A — Glosario de notación

| Símbolo | Significado | Unidades |
|---|---|---|
| $h$ | Buffer slack agregado | adimensional |
| $h^\ast$ | Umbral del global game (default 0,30) | adimensional |
| $\sigma$ | Dispersión de señales privadas (default 0,08) | adimensional |
| $\dot R(h)$ | Tasa de release | mb/d |
| $R_{\max}$, $h_R$ | Parámetros Michaelis-Menten (6, 0,12) | mb/d, adim. |
| $P^\ast$ | Precio pre-shock (70) | USD/bbl |
| $P^\ast(\text{Stock})$ | Precio régimen abierto con reposición (Ext 4) | USD/bbl |
| $P_C(h)$ | Precio régimen clásico | USD/bbl |
| $P_R(h)$ | Precio régimen run | USD/bbl |
| $q(h)$ | Probabilidad de régimen run | adim. |
| $P(h)$ | Composite = $(1-q) P_C + q P_R$ | USD/bbl |
| $P_{\rm cap}$ | Cap clásico ($h \to 0$) | USD/bbl |
| $P_{\rm floor}$ | Piso clásico ($h$ grande) | USD/bbl |
| $\theta$ | Prob. implícita de normalización | adim. |
| $\theta_{\rm exógeno}$ | $\theta$ como input (Ext 1) | adim. |
| $\varepsilon_d$, $\varepsilon_s$ | Elasticidades (0,05 / 0,04) | adim. |
| $D_0$, $S_{f,0}$ | Demanda/oferta a $P^\ast$ (104, 95) | mb/d |
| $\mu$, $\delta_0$ | Fracción retenida, demanda especulativa (0,5, 0) | adim., mb/d |
| Stock | Total Global Observed Inventories (IEA) | mb |
| Stock_floor, _stress, _opt | Umbrales (6.800, 7.600, 8.200) | mb |
| $R_{\rm repl,max}$ | Reposición máxima (Ext 4; 5) | mb/d |

## Apéndice B — Números clave (mayo 2026)

| Magnitud | Valor | Fecha del dato |
|---|---|---|
| Stock IEA OMR | 7.951 mb | 30-abril-2026 |
| Precio Brent observado | 124,24 USD/bbl (FRED) / 122,58 (Bloomberg M1) | 30-abril-2026 |
| $h_{\rm actual}$ (Ext 2) | 0,43 | derivado |
| $\dot R(h_{\rm actual})$ | 4,69 mb/d | derivado |
| $P_C(h_{\rm actual})$ | $\approx 113$ USD/bbl | derivado |
| $P_R(h_{\rm actual})$ | $\approx 147$ USD/bbl | derivado |
| $q(h_{\rm actual})$ | $\approx 0{,}05$ | derivado |
| $P$ composite | $\approx 115$ USD/bbl | derivado |
| $\theta$ implícito (FRED) | $\approx -0{,}21$ (wedge negativo; ver §10) | derivado |
| $\theta$ implícito (Bloomberg M1) | $\approx -0{,}17$ | derivado |
| $P_{\rm cap}$ | $\approx 191$ USD/bbl | derivado |
| $P_{\rm floor}$ | $\approx 95$ USD/bbl | derivado |
| Margen sobre Stock_stress | 351 mb ($\sim 75-90$ días) | derivado |
| Margen sobre Stock_floor | 1.151 mb ($\sim 9-10$ meses) | derivado |

## Apéndice C — Referencias bibliográficas

**Storage theory y dinámica de commodities:**

- **Working (1949).** The Theory of Price of Storage. *AER* 39(6).
- **Brennan (1958).** The Supply of Storage. *AER* 48(1).
- **Deaton & Laroque (1992).** On the Behaviour of Commodity Prices. *RES*
  59(1), 1-23.
- **Deaton & Laroque (1996).** Competitive Storage and Commodity Price
  Dynamics. *JPE* 104(5).
- **Pindyck (1994).** Inventories and the Short-Run Dynamics of Commodity
  Prices. *RAND JE* 25(1).
- **Pindyck (2001).** The Dynamics of Commodity Spot and Futures Markets.
  *Energy Journal* 22(3), 1-29.
- **Williams & Wright (1991).** *Storage and Commodity Markets*. Cambridge UP.
- **Routledge, Seppi & Spatt (2000).** Equilibrium Forward Curves for
  Commodities. *JF* 55(3), 1297-1338.

**Bank runs y global games:**

- **Diamond & Dybvig (1983).** Bank Runs, Deposit Insurance, and Liquidity.
  *JPE* 91(3), 401-419.
- **Carlsson & van Damme (1993).** Global Games and Equilibrium Selection.
  *Econometrica* 61(5), 989-1018.
- **Morris & Shin (1998).** Unique Equilibrium in a Model of Self-Fulfilling
  Currency Attacks. *AER* 88(3), 587-597.
- **Goldstein & Pauzner (2005).** Demand-Deposit Contracts and the Probability
  of Bank Runs. *JF* 60(3), 1293-1327.
- **Bocola & Lorenzoni (2020).** Financial Crises, Dollarization, and Lending
  of Last Resort in Open Economies. *AER* 110(8), 2524-2557.

**Petróleo:**

- **Hamilton (2009).** Understanding Crude Oil Prices. *Energy Journal* 30(2),
  179-206.
- **Kilian (2009).** Not All Oil Price Shocks Are Alike. *AER* 99(3), 1053-1069.
- **Kilian & Murphy (2014).** The Role of Inventories and Speculative Trading
  in the Global Market for Crude Oil. *Journal of Applied Econometrics* 29(3).
- **Caldara, Cavallo & Iacoviello (2019).** Oil Price Elasticities and Oil
  Price Fluctuations. *Journal of Monetary Economics* 103, 1-20.

**Posicionamiento financiero (run regime):**

- **Acharya, Lochstoer & Ramadorai (2013).** Limits to Arbitrage and Hedging:
  Evidence from Commodity Markets. *Journal of Financial Economics* 109.

---

**Documentos relacionados del proyecto:**

- `modelo_petroleo.pdf` — versión original del paper v1 (mayo 2026).
- `modelo_extensiones.md` — detalle de las 4 extensiones implementadas.
- `modelo_v2_incertidumbre_T.md` — propuesta del v2 sobre incertidumbre en T.
- `minuta_QA_presentacion.md` — Q&A condensado para presentación.
- `nota_calculo_h.md`, `nota_calibracion_h_star.md`, `nota_v2_actualizacion_creencias.md` —
  notas técnicas adicionales.

---

**Fin del documento.**
