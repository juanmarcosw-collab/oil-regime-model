# v2 — Cuándo reciben los agentes la señal y cómo se actualizan las creencias con el paso del tiempo

**Refinamiento al baseline propuesto en `modelo_v2_incertidumbre_T.md` §2.3-2.4.**

La pregunta es muy buena y expone una tensión que el doc original glosó.
La respuesta corta:

> *La señal se recibe **una sola vez al inicio del shock (t=0)**, pero la
> creencia del agente sobre T **sí se actualiza con el paso del tiempo**, vía
> condicionamiento bayesiano sobre la observación "Ormuz sigue cerrado en t".
> La señal $s_i$ es fija; el posterior sobre T no.*

---

## 1. Qué es fijo y qué se actualiza

Hay que separar dos cosas distintas que en el doc original quedaron mezcladas:

| Objeto | Estado |
|---|---|
| **Señal privada $s_i$** | Fija. Recibida una vez en $t=0$. Es un "tipo" del agente. |
| **Posterior sobre T** | Evoluciona con $t$. Se actualiza bayesianamente. |
| **Decisión (liberar / retener)** | Re-evaluada en cada snapshot $t$, usando el posterior actual. |

Lo que dije en el doc original ("no hay learning pasivo") era impreciso: aplica
al prior sin condicionamiento, no al posterior bajo "Ormuz sigue cerrado en t".

---

## 2. La actualización bayesiana con el paso del tiempo

**Setup en $t=0$:**

- Prior: $T \sim \mathrm{Exp}(\lambda)$, con $\lambda = 1/\mathbb{E}[T]$.
- Señal: $s_i = T + \varepsilon_i$, $\varepsilon_i \sim \mathcal{N}(0, \sigma_T^2)$.
- Posterior inicial (combinando prior + señal):

$$\pi_0(\tau \mid s_i) \propto \lambda e^{-\lambda \tau} \cdot
  \exp\!\left(-\frac{(s_i - \tau)^2}{2\sigma_T^2}\right)$$

Es una gaussiana truncada en $\tau \geq 0$, centrada en $s_i - \lambda \sigma_T^2$
con varianza $\sigma_T^2$.

**En $t > 0$ (Ormuz aún cerrado):**

El agente observa el evento "T > t". El posterior se actualiza:

$$\pi_t(\tau \mid s_i, T > t) \propto \pi_0(\tau \mid s_i) \cdot \mathbf{1}\{\tau > t\}$$

Esto es una **gaussiana truncada por abajo en $t$**. Conforme $t$ crece, se va
cortando masa por la izquierda y el posterior se concentra cada vez más
cerca de $t$ (por la derecha).

**Expected remaining wait:**

$$\mathbb{E}[T - t \mid s_i, T > t] =
  \mathbb{E}[T \mid s_i, T > t] - t$$

Para la gaussiana truncada, esto es la *inverse Mills ratio*:

$$\mathbb{E}[T \mid s_i, T > t] = \mu_i + \sigma_T \cdot
  \frac{\varphi(\alpha_i)}{1 - \Phi(\alpha_i)}$$

con $\mu_i = s_i - \lambda \sigma_T^2$ y $\alpha_i = (t - \mu_i)/\sigma_T$.

---

## 3. Respuesta directa a tu pregunta: ¿y si $t > \mathbb{E}_0[T]$ y Ormuz sigue cerrado?

Caso concreto: imaginemos $\mathbb{E}_0[T] = 60$ días, $\sigma_T = 30$,
$s_i = 60$ (agente con señal central). Sin condicionar, el agente espera
$T \approx 60 - \lambda \sigma_T^2 = 60 - 15 = 45$ días.

Ahora pasan 200 días sin reapertura. El posterior se trunca a $\tau > 200$:

- La gaussiana original (centrada en 45, std 30) tiene **prácticamente cero
  masa** sobre 200 ($z = (200-45)/30 \approx 5{,}2$ desvíos).
- Bayes obliga: el posterior se concentra **apenas por encima de 200**.
- $\mathbb{E}[T \mid s_i = 60, T > 200] \approx 200 + \epsilon$, con $\epsilon$ chico.
- $\mathbb{E}[T - 200 \mid s_i = 60, T > 200] \approx \epsilon \approx 0$ días.

Es decir: el agente que en $t=0$ pensaba "esto dura 60 días" ahora,
después de 200, piensa "tiene que reabrir de un momento a otro". Su
**expected remaining wait** colapsa.

En cambio, un agente que recibió señal $s_i = 300$ (pesimista) tiene
$\mu_i = 285$, y a $t = 200$ su $\alpha_i = -2{,}83$. El posterior está
poco afectado por la truncación; sigue esperando algo cerca de 300 días.

**Conclusión:** el paso del tiempo "fuerza hacia arriba" las creencias de
los agentes optimistas, pero deja relativamente intactos a los pesimistas.

---

## 4. Implicación operacional para el snapshot del game

En el snapshot a tiempo $t$, los agentes que aún tienen inventario y aún no
liberaron están decidiendo si retener o liberar. Cada uno usa su posterior
$\pi_t(\tau \mid s_i, T > t)$ para evaluar el payoff esperado de cada
acción. La probabilidad agregada de run $q_t$ se calcula sobre la
distribución de $s_i$ en el pool remanente, **ponderada por sus posteriors
actuales sobre $T - t$**.

Operacionalmente:

- En $t = 0$, la dispersión de creencias es máxima: hay agentes optimistas y
  pesimistas, y muchos en el medio.
- Conforme $t$ crece sin reapertura, los optimistas se ven forzados al
  límite "el tiempo restante es chico" — algunos liberan, otros mantienen.
- Los pesimistas conservan sus creencias y siguen reteniendo.
- $q_t$ tiende a converger a algo determinado por la **fracción del pool
  que mantiene creencias pesimistas robustas a la truncación**.

Esto da una dinámica natural del precio durante el shock que no depende
exclusivamente del drenaje del stock.

---

## 5. La capa más profunda: selección del pool

Hay un segundo efecto que sí queda fuera del baseline y que el doc v2
mencionaba como limitación (§9.1.1, "decisión estática snapshot"):

**El pool de tenedores se va seleccionando con el tiempo.** Los agentes
que liberan en $t$ salen del juego; quedan solo los que retuvieron. Como
los optimistas tienden a liberar primero (su expected $T$ es bajo, no vale
la pena retener), el pool remanente se va sesgando hacia **agentes con
señales originalmente altas o con expected $T$ robusto a la truncación**.

Esto significa que **la composición del pool ya no es la distribución
inicial** $s_i \sim$ algo simétrico; se vuelve cada vez más sesgada hacia
los pesimistas. La $q_t$ del game agregado se calcula sobre el pool
seleccionado, no sobre toda la población inicial.

Capturar esto formalmente requiere un **stopping-time game con selección
endógena del pool**, que es la Extensión E4 del v2 doc. Para el baseline,
ignoramos selección y trabajamos con la población inicial; el costo es que
el modelo subestima la persistencia del régimen de run en horizontes largos.

---

## 6. Implicaciones para el documento v2

El baseline original (`modelo_v2_incertidumbre_T.md`) necesita dos
correcciones menores en §2.3-2.4:

1. **§2.3 — Información del agente:** aclarar que $s_i$ es una característica
   fija del agente (su "tipo"), recibida una vez en $t=0$.

2. **§2.4 — Aprendizaje:** corregir la afirmación de "no hay learning
   pasivo". La afirmación correcta es: **no hay learning pasivo del prior
   bruto** (porque la exponencial es memoryless), pero **sí hay learning
   bayesiano del posterior condicional a (s_i, T > t)**. El paso del
   tiempo actualiza el posterior mediante truncación, aún sin nuevas
   señales.

3. **Agregar a §3 o §4:** explicitar que en cada snapshot $t$, los agentes
   usan $\pi_t(\tau \mid s_i, T > t)$ para evaluar payoffs. Esto introduce
   dinámica natural en $q_t$ aún con stock constante.

Estos son ajustes substantivos pero menores; no rompen la arquitectura
del v2. Si te parece, los incorporo cuando volvamos a tocar el doc.

---

## 7. Una alternativa más ambiciosa: signal arrival continuo

El framework que propusimos asume **una sola señal en $t=0$**. Una
alternativa más realista sería que cada agente reciba un *stream* de señales
$s_{i,1}, s_{i,2}, \ldots$ a lo largo del shock, cada una informativa
sobre T. Esto es un **filtro de Kalman acoplado al global game**: agentes
hacen updates bayesianos en tiempo real, las creencias se mueven con
"flujo de noticias" idiosincrásico.

Esto es la frontera teórica (dynamic global games à la Angeletos-Hellwig-Pavan).
Está identificado como Extensión E3 en el v2 doc. Está fuera del scope del
baseline pero vale la pena tenerlo en el mapa: si en un futuro queremos
modelar con detalle "cómo se incorporan las noticias geopolíticas día a
día al precio", esa es la maquinaria.

---

## Resumen en una línea

> *La señal $s_i$ se recibe una sola vez en $t=0$ y es fija. Pero el
> posterior sobre T se actualiza con el tiempo vía truncación bayesiana
> sobre "Ormuz sigue cerrado en $t$", lo cual fuerza a los optimistas a
> converger hacia "reabrirá de un momento a otro" y deja a los pesimistas
> relativamente intactos.*
