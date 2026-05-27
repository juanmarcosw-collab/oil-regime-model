# Por qué $h^\ast = 0{,}30$

**Respuesta corta:** $h^\ast = 0{,}30$ **no es un valor derivado**, es una
elección de escala. El modelo es invariante a re-escalamientos del eje h, así
que el valor numérico en sí mismo no es identificable. Lo que sí es
substantivo es **dónde se ancla** $h^\ast$ contra un observable empírico.

---

## 1. La invariancia de escala del modelo

El modelo trabaja en un eje h adimensional. Si multiplicamos h y todos sus
"compañeros de escala" por una constante $c$:

$$h \mapsto c \cdot h, \quad h^\ast \mapsto c \cdot h^\ast, \quad
\sigma \mapsto c \cdot \sigma, \quad h_R \mapsto c \cdot h_R$$

las **predicciones del modelo son idénticas**. Es decir, podríamos haber
elegido $h^\ast = 1$, $\sigma = 0{,}267$, $h_R = 0{,}40$ y obtener
exactamente el mismo precio composite, la misma probabilidad de run, la
misma figura. Solo cambiarían los números en el eje x.

Por lo tanto, $h^\ast = 0{,}30$ es **una convención**. Lo único identificable
es:

- La posición de $h_{\rm actual}$ relativa a $h^\ast$ (qué tan lejos está
  el estado del umbral).
- El cociente $\sigma / h^\ast$ (qué tan ancha es la zona de transición
  relativa al umbral).
- El cociente $h_R / h^\ast$ (qué tan rápido satura el release relativo al
  umbral).

---

## 2. Lo que sí está anclado empíricamente

La calibración de la app no usa $h^\ast = 0{,}30$ a secas. **Usa la
Extensión 2** para anclar $h^\ast$ a un observable:

$$h^\ast \leftrightarrow \text{Stock}_{\rm stress} = 7{.}600 \text{ mb}$$

Es decir, **el umbral teórico del global game se identifica con el
threshold de stress operacional de JPMorgan**. Eso sí es una afirmación
substantiva — no es una elección de escala, es una hipótesis sobre dónde
ocurre la coordinación.

La frase relevante para la presentación es:

> *"Asumimos que el umbral teórico del run del global game coincide con el
> nivel de stock donde JPMorgan identifica empíricamente el stress
> operacional del sistema. Ese es el contenido empírico de $h^\ast$. El
> valor numérico (0,30) es solo una convención de normalización; podríamos
> haber elegido 1 sin que cambien las predicciones."*

---

## 3. Cómo se calibraron $h_R$ y $\sigma$ dentro de esa escala

Una vez fijado $h^\ast = 0{,}30$, los demás parámetros del eje h se
calibran consistentemente:

**$h_R = 0{,}12$** — Calibrado para que, a la condición observada en mayo
2026, la tasa de release sea ~4 mb/d (consistente con stockdraws reportados
por IEA OMR). En cocientes: $h_R / h^\ast = 0{,}40$ — el release alcanza
half-saturation al 40% del nivel de stress.

**$\sigma = 0{,}08$** — Placeholder. En cocientes: $\sigma / h^\ast \approx
0{,}27$. **No está identificado empíricamente** — es el parámetro más
débilmente calibrado del modelo. Es exactamente uno de los motivos del v2.

---

## 4. Por qué no $h^\ast = 1$ (que sería más "natural")

Buena pregunta. Tres razones por las que se eligió 0,30:

1. **Herencia del paper.** El paper de referencia usaba 0,30 como número
   razonable; cambiarlo introduciría inconsistencia con el documento de
   trabajo.
2. **Estética de los plots.** Con $h^\ast = 0{,}30$, las figuras tienen
   curvas que se ven bien en un eje $[0, 1{,}5]$. Con $h^\ast = 1$, la
   grilla relevante sería $[0, 5]$ y las curvas se aplastan.
3. **Tradición Goldstein-Pauzner.** En el paper original, los valores
   típicos del threshold del global game son chicos (< 0,5).

Ninguna de estas razones es de fondo. Si el Consejo lo pidiera, podríamos
re-escalar el modelo a $h^\ast = 1$ con cero cambio en outputs.

---

## 5. Qué responder si en la presentación insisten en "¿por qué 0,30?"

Tres niveles de respuesta, dependiendo de la audiencia:

**Nivel 1 (alta gerencia, foco en lectura del modelo):**

> *"$h^\ast = 0{,}30$ es una convención de escala — el modelo es invariante
> a re-escalamientos del eje h, así que el número en sí mismo no es
> identificable. Lo que sí elegimos sustantivamente es anclarlo al stress
> threshold de JPMorgan (7.600 mb de stocks globales)."*

**Nivel 2 (gerentes técnicos):**

> *"Es una normalización; podríamos haber elegido $h^\ast = 1$ con
> resultados idénticos. La elección de 0,30 hereda del paper original y
> facilita la legibilidad de las figuras. Los parámetros que sí son
> sustantivos son los **cocientes** $h_R/h^\ast$ (forma del release) y
> $\sigma/h^\ast$ (anchura de la zona de transición)."*

**Nivel 3 (staff técnico de la DPM, si llegan a este detalle):**

> *"Identificación parcial. Lo identificable es: (a) la posición del estado
> observado relativa al umbral, lo cual surge del anclaje al threshold JPM,
> y (b) los ratios $h_R/h^\ast$ y $\sigma/h^\ast$. El valor absoluto
> de $h^\ast$ es libre. El parámetro débil de calibración no es $h^\ast$ —
> es $\sigma$, que no tiene anclaje empírico claro y motiva el desarrollo
> del v2."*

---

## 6. Conexión con el v2

Una de las virtudes del v2 (incertidumbre sobre T) es que **el parámetro
análogo a $h^\ast$ desaparece como parámetro libre**: queda determinado
endógenamente como $\tau_{\rm crítico}(\text{Stock}_0)$, el tiempo hasta
que el stock toca el floor operacional. Es decir, en v2 el umbral del game
es derivable de la dinámica de drenado y del stock observado, sin
parámetro libre adicional.

Esto resuelve precisamente la incomodidad de "¿por qué 0,30 y no otro
número?" — porque en v2 no hay que elegir.
