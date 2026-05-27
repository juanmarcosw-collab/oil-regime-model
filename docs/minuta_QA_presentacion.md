# Minuta Q&A — Modelo estructural del precio del petróleo

**Para:** presentación al Consejo y gerentes BCCh
**Fecha:** mayo 2026
**Versión presentada:** v1 (modelo del paper). El v2 (incertidumbre sobre T) está
en desarrollo conceptual; se menciona como hoja de ruta.

---

## 0. Apertura — elevator pitch

> *Modelo estructural-teórico que articula dos regímenes del precio del petróleo
> bajo stress de oferta (cierre de Ormuz): un régimen clásico de storage theory
> y un régimen de "run" coordinado donde tenedores de inventario se coordinan en
> retener. La transición entre regímenes es endógena y probabilística, modelada
> con un global game à la Goldstein-Pauzner (2005). El precio observado es un
> promedio ponderado de los dos regímenes. Output operativo: la probabilidad de
> régimen de run dada la condición actual del buffer, y la lectura implícita
> que hace el mercado sobre la duración esperada del shock (θ implícito).*

**Tres puntos para enmarcar la conversación:**

1. **Es un modelo de investigación, no un pronóstico.** Da estructura para
   pensar el riesgo de fragilidad, no un número puntual de precio futuro.
2. **Es teórico-estructural, no econométrico.** No estimamos con datos
   históricos; calibramos con literatura y juicio. Por eso los parámetros
   tienen rango razonable pero el modelo no compite con un VAR de pronóstico.
3. **El valor está en el wedge.** Comparar precio del modelo con precio
   observado da una lectura de qué probabilidad de "normalización" está
   priciendo el mercado — una métrica que no es naturalmente observable.

---

## 1. Qué es el modelo y para qué

**1.1. ¿De qué se trata el modelo en una frase?**
Un modelo de dos regímenes del precio del petróleo bajo cierre del Estrecho
de Ormuz, con transición probabilística entre régimen clásico (storage theory)
y régimen de pánico coordinado (run), modelada con un global game.

**1.2. ¿Qué pregunta busca responder?**
¿Cuán frágil está el sistema de petróleo dado el nivel actual de inventarios?
Y, condicional al precio observado, ¿qué cree el mercado sobre la probabilidad
de resolución del shock?

**1.3. ¿Es un modelo de pronóstico?**
No. Es un modelo estructural-teórico. Da un mapa de relaciones entre estado
del sistema y precios, no una predicción puntual de precio futuro. Su
contraparte natural sería un modelo Smets-Wouters, no un VAR.

**1.4. ¿Para qué sirve operativamente?**
Dos usos: (a) tracking del θ implícito en el precio observado, como métrica
diaria de expectativas de normalización; (b) análisis de escenarios — qué
pasa con el precio si h cae a X, o si el run se materializa.

**1.5. ¿Por qué BCCh hace este trabajo?**
Porque shocks petroleros con potencial de coordinación son riesgos
sistémicos para inflación e importaciones de Chile. Tener un modelo propio
permite interpretar las lecturas del mercado y hacer escenarios sin depender
exclusivamente de calls de bancos de inversión.

---

## 2. Bases teóricas y literatura

**2.1. ¿En qué literatura se basa?**
Tres tradiciones combinadas:
- **Storage theory de commodities:** Deaton-Laroque (1992), Pindyck (2001),
  Routledge-Seppi-Spatt (2000).
- **Global games / bank runs:** Diamond-Dybvig (1983), Morris-Shin (1998),
  Goldstein-Pauzner (2005), Carlsson-van Damme (1993).
- **Empírica del petróleo:** Hamilton (2009), Kilian (2009),
  Caldara-Cavallo-Iacoviello (2019) para elasticidades.

**2.2. ¿Cuál es el aporte original?**
Articular *en un mismo modelo* la mecánica clásica de storage theory con la
posibilidad de un run coordinado, vía un global game sobre el estado del
buffer. Hasta donde sabemos, la literatura tradicional separa ambos canales.

**2.3. ¿Por qué Goldstein-Pauzner y no Diamond-Dybvig?**
Diamond-Dybvig tiene multiplicidad de equilibrios (todos corren / nadie corre).
Goldstein-Pauzner introduce señales privadas ruidosas que seleccionan un
único equilibrio, lo cual da una q(h) determinada y manipulable. Eso es lo
que necesitamos para mapear estados a probabilidades.

**2.4. ¿Por qué storage theory y no Hotelling?**
Hotelling es para recursos agotables (el petróleo "se va a acabar"). Acá lo
finito no es el petróleo sino el buffer; la storage theory es la herramienta
correcta porque modela tenedores de inventario que pueden liberar o retener.

**2.5. ¿Existe literatura previa sobre runs en commodities?**
Limitada. Hay trabajo sobre commodity hoarding (Kilian, varios) y sobre
multiplicidad de equilibrios en metales (Routledge et al.), pero la
aplicación explícita de global games a inventarios de petróleo es novedosa.

---

## 3. Régimen clásico

**3.1. ¿Qué es el régimen clásico?**
El equilibrio de market clearing donde el precio surge de oferta-demanda con
las elasticidades estándar, más la oferta adicional que viene del release
coordinado de inventarios (SPRs y comerciales).

**3.2. ¿Cuál es la ecuación?**

$$D(P_C) = S_f(P_C) + \dot R(h)$$

con $D(P) = D_0 (P/P^\ast)^{-\varepsilon_d}$ y $S_f(P) = S_{f,0} (P/P^\ast)^{\varepsilon_s}$.
Se resuelve numéricamente con root-finding (brentq).

**3.3. ¿Qué predice cuando el buffer se agota?**
Cuando $h \to 0$, $\dot R \to 0$, y la ecuación se reduce al equilibrio puro
oferta-demanda con oferta reducida. Forma cerrada:
$P_{\rm cap}/P^\ast = (D_0/S_{f,0})^{1/(\varepsilon_d + \varepsilon_s)}$.
Con la calibración del paper: ~191 USD/bbl.

**3.4. ¿Y cuando el buffer es muy alto?**
Cuando $h \to \infty$, $\dot R \to R_{\max}$. El piso es ~95 USD/bbl con
calibración default. El piso está por encima de P* (70) porque incluso con
release máximo (6 mb/d), la oferta no compensa totalmente la pérdida de
~9 mb/d por el cierre.

---

## 4. Régimen de run

**4.1. ¿Qué es el régimen de run?**
Un escenario donde los tenedores de inventario se coordinan en *no liberar*
(retener), anticipando precios futuros mayores. Esto reduce la oferta
efectiva y dispara el precio.

**4.2. ¿Cuál es la ecuación?**

$$D(P_R) + \delta(h) = S_f(P_R) + (1 - \mu) \dot R(h)$$

Dos diferencias respecto al clásico: (a) parte del release se retiene
(fracción μ), (b) hay demanda especulativa adicional δ(h).

**4.3. ¿Por qué la analogía con bank runs es válida?**
En un bank run, los depositantes retiran masivamente anticipando insolvencia.
Acá los hoarders retienen masivamente anticipando precios mayores. La
estructura matemática es idéntica: complementariedades estratégicas y
self-fulfilling prophecies.

**4.4. ¿Qué garantiza que P_R(0) = P_C(0)?**
En $h = 0$ no hay release que liberar ni retener. Ambos regímenes colapsan
en el mismo equilibrio: el cap clásico. Esa convergencia es importante
porque hace continuo el composite alrededor del stockout.

---

## 5. El global game

**5.1. ¿Qué es un global game?**
Un juego de coordinación con información privada incompleta. Cada agente
recibe una señal ruidosa sobre el fundamental subyacente y debe decidir una
acción binaria. La ruidocidad informacional **elimina la multiplicidad de
equilibrios** del juego clásico.

**5.2. ¿Qué información tiene cada agente?**
Cada tenedor de inventario recibe una señal privada $s_i = h + \varepsilon_i$
con $\varepsilon_i \sim \mathcal{N}(0, \sigma^2)$. Conoce su señal y la
distribución de ruido, pero no conoce el h verdadero ni las señales de los
demás.

**5.3. ¿Cuándo se juega el game?**
Conceptualmente, en cada instante. Operativamente, el modelo lo trata como
un juego estático para un h dado: la solución del game produce q(h), la
probabilidad de que se materialice el run en ese estado.

**5.4. ¿Cuál es el equilibrio?**
Estrategias monótonas: cada agente "retiene" sii su señal $s_i$ es menor
que un umbral $s^*$. En el límite $\sigma \to 0$, $s^* \to h^*$. Para
$\sigma > 0$, la transición agregada es suave: $q(h) = \Phi((h^* - h)/\sigma)$.

**5.5. ¿Por qué señales privadas y no información común?**
Con información común, el juego de coordinación tiene equilibrios múltiples
("todos retienen" y "nadie retiene"). La introducción de ruido idiosincrásico
permite seleccionar un único equilibrio (Carlsson-van Damme 1993). Es una
piedra angular de la teoría moderna de coordinación.

**5.6. ¿Es realista que h sea desconocido?**
Esta es una crítica importante (volvemos a ella en §11 y §12). En la
práctica, IEA/EIA publican stocks con buena frecuencia. La σ del modelo es
un placeholder; la verdadera dispersión informacional está sobre T (duración
del shock), no sobre h. Esto motiva el v2.

---

## 6. Función de release (Michaelis-Menten)

**6.1. ¿Qué representa la función de release?**
La tasa a la cual los tenedores de inventario (SPRs estratégicos, comerciales
y operacionales) liberan stock al mercado durante el shock. Es una
**reduced-form**: no se deriva de optimización explícita, agrega coordinación
implícita.

**6.2. ¿Por qué la forma Michaelis-Menten?**
$\dot R(h) = R_{\max} \cdot h/(h + h_R)$. Cumple tres propiedades necesarias:
(a) $\dot R(0) = 0$ — sin stock no hay release; (b) monótona creciente;
(c) saturación en $R_{\max}$ — hay un techo logístico/político al release.
Es la forma más parsimoniosa con esas propiedades.

**6.3. ¿Qué es h_R?**
La **constante de half-saturation**: el nivel de buffer en el cual el
release alcanza la mitad de su capacidad máxima. Controla la forma de la
curva — qué tan rápido el sistema pasa de "no libera" a "libera al tope".
Calibración: $h_R = 0{,}12$.

**6.4. ¿Por qué no una función lineal o sigmoide?**
Lineal no tiene saturación natural ni cero en el origen. Una sigmoide
funciona igual de bien matemáticamente pero requiere dos parámetros de
forma. Michaelis-Menten es estándar y minimal: un parámetro de altura
($R_{\max}$) y uno de curvatura ($h_R$).

---

## 7. Calibración

**7.1. ¿De dónde vienen los parámetros estructurales?**
Literatura estándar:
- $P^\ast = 70$ USD/bbl: Brent pre-shock (febrero 2026).
- $D_0 = 104$, $S_{f,0} = 95$ mb/d: IEA OMR.
- $\varepsilon_d = 0{,}05$, $\varepsilon_s = 0{,}04$: Caldara-Cavallo-Iacoviello
  (2019), rango bajo.
- $R_{\max} = 6$ mb/d: capacidad histórica de releases coordinados G7
  (2011 Libia, 2022 Ucrania).

**7.2. ¿Y los parámetros del game?**
- $h^\ast = 0{,}30$: umbral teórico, calibrado contra el observable empírico
  del nivel de stress operacional JPMorgan (7.600 mb).
- $\sigma = 0{,}08$: dispersión de señales, placeholder. **No identificable
  empíricamente con datos actuales** — es el punto débil del v1.

**7.3. ¿Y h_R?**
$h_R = 0{,}12$. Implica que en condiciones cercanas al stress (h ≈ 0,30),
el release está al ~71% de su capacidad. Consistente con el ritmo
observado de stockdraws (~4 mb/d) reportado por IEA OMR.

**7.4. ¿Y μ, δ?**
$\mu = 0{,}5$ (fracción del release retenida en el run) y $\delta_0 = 0$
(demanda especulativa adicional neutral). Ambos son defaults conservadores;
la sensibilidad a $\mu$ es alta, vale la pena destacarlo si se pregunta.

---

## 8. Lectura de las figuras del dashboard

**8.1. Figura 1 — Precio vs. buffer (h, P): ¿qué muestran las líneas?**
- **Verde continua:** $P_C(h)$ — precio régimen clásico (Ormuz cerrado, sin run).
- **Roja punteada:** $P_R(h)$ — precio régimen run (Ormuz cerrado + corrida).
- **Negra:** $P(h)$ — composite ponderado por $q(h)$.
- **Morada:** $P^\ast(h)$ — precio si Ormuz reabre (con demanda de reposición).
- **Marcador:** precio Brent al 30-abril-2026 (124,24 USD/bbl, FRED; 122,58 Bloomberg M1), plantado en $h_{\rm actual}$ derivado del stock IEA OMR del mismo día. Ambos del último OMR disponible al momento de la presentación (22-may-2026).

**8.2. Figura 2 — Precio en el tiempo P(t): ¿qué muestra?**
La trayectoria proyectada del precio bajo shock persistente. Cada curva es
la versión temporal de la curva correspondiente en Figura 1, con h(t)
cayendo según la dinámica de drenado.

**8.3. Figura 3 — Stock en el tiempo: ¿qué muestra?**
La trayectoria del stock global bajo cierre persistente. Las líneas
horizontales son los thresholds operacionales JPMorgan (stress = 7.600 mb,
floor = 6.800 mb). Las fechas de cruce señalan hitos de transición de régimen.

**8.4. ¿Por qué el precio observado está cerca / por debajo del modelo composite?**
Cuando el precio observado está significativamente por debajo del composite,
el mercado pricea una probabilidad positiva θ de normalización: $\theta_{\rm imp}
= (P_{\rm modelo} - P_{\rm observado}) / (P_{\rm modelo} - P^\ast)$. **Con la
calibración actual** (composite ≈ 115, observado = 124,24 FRED), el wedge
es **negativo**: $\theta \approx -0{,}21$. Lectura: el mercado pricea **más
severidad que la que el modelo capta**. Esto sugiere subestimación de la
fragilidad o canales no modelados (risk premium, run regime parcialmente
activo). Es un hallazgo diagnóstico — no invalida el modelo, señala
calibraciones a refinar.

---

## 9. Preguntas conceptuales clave

**9.1. Si todos saben que Ormuz está cerrado, ¿por qué el precio no salta
al cap (~191 USD/bbl)?**

Porque el precio del modelo es un **equilibrio spot de flujo, no de
arbitraje intertemporal puro**. La condición $D(P_t) = S_f(P_t) + \dot R(h_t)$
se cumple período a período. Mientras $h$ sea alto, $\dot R$ compensa parte
de la oferta perdida y el precio queda contenido. El cap es un punto al que
el sistema *llega trayectoriado*, no al que salta.

**9.2. ¿No debería el mercado anticipar el cap y arbitrar?**
El petróleo no es un activo financiero perfectamente almacenable. Los
arbitrajistas enfrentan costos de almacenamiento, restricciones logísticas y
políticas (SPRs no son tradeable). El no-arbitrage clásico no aplica
estrictamente; lo que aplica es market clearing de flujo.

**9.3. ¿Cuándo aparece el "salto" del precio?**
Cuando $h$ se acerca a $h^\ast$, la probabilidad de run $q(h)$ sube
rápidamente y el composite se desplaza hacia $P_R$, que es notablemente
mayor que $P_C$ al mismo h. Ese movimiento puede ser pronunciado pero no
discontinuo — la suavidad la da σ.

**9.4. ¿Qué información tiene cada agente?**
Tres tipos: (a) consumidores y oferentes son price-takers, observan $P_t$;
(b) tenedores de inventario en régimen clásico siguen una regla
reduced-form $\dot R(h)$; (c) en régimen de run, cada uno recibe una señal
privada ruidosa sobre h.

**9.5. ¿Quién juega el global game?**
Los tenedores de inventario (SPRs comerciales, estratégicos, refinerías,
traders con tank capacity). Son los únicos que tienen la opción real de
"retener vs. liberar". Consumidores y oferentes flujo no son parte del game.

---

## 10. Extensiones implementadas (sobre el paper)

El dashboard incorpora cuatro extensiones sobre el paper original.
Están documentadas en `docs/modelo_extensiones.md`.

**10.1. ¿Cuáles son las extensiones?**

| Ext | Qué hace | Por qué importa |
|---|---|---|
| 1 | θ dual: exógeno (input) y implícito (output) | Permite análisis contrafactual y diagnóstico |
| 2 | Mapeo lineal h ↔ stock observable | Conecta el modelo abstracto a datos IEA OMR |
| 3 | Dinámica temporal P(t) | Da trayectorias proyectadas bajo shock persistente |
| 4 | Demanda de reposición → P\*(stock) variable | Endogeniza el precio post-shock; hace explícito el costo de stockout |

**10.2. Ext 1 — θ dual: ¿qué cambia?**
El paper define θ como output diagnóstico (despeje implícito del precio
observado). La extensión permite usarlo también como input: dado un θ
exógeno, computar el precio esperado. Útil para escenarios contrafactuales.

**10.3. Ext 2 — Mapeo h ↔ stock: ¿cómo se hace?**
Lineal, anclado en dos thresholds JPMorgan:
- Stock_floor (6.800 mb) → h = 0.
- Stock_stress (7.600 mb) → h = h*.
Con stock al 30-abril-2026 (7.951 mb, IEA OMR), da h ≈ 0,43.

**10.4. Ext 3 — Dinámica P(t): ¿cómo se simula?**
Se integra la ODE $d\text{Stock}/dt = -\dot R(h(\text{Stock}))$ con scipy
solve_ivp, partiendo del stock observado. Para cada t se evalúan los
regímenes y el composite. Asume shock persistente (no se modela reapertura
en la simulación base).

**10.5. Ext 4 — Reposición y P\*(stock): ¿qué dice?**
Si Ormuz reabre con stocks bajos, hay demanda extra para reponer. Esta
demanda se modela como una función lineal saturada del gap stock vs.
Stock_opt (8.200 mb). Cuanto menor el stock al momento de la reapertura,
mayor P\*. **Implicación:** el "precio post-shock" no es 70 USD/bbl
mecánicamente; depende del estado de los inventarios al momento de
resolución.

---

## 11. Supuestos y limitaciones

**11.1. ¿Cuáles son los supuestos clave?**
- Cierre total y persistente del Estrecho de Ormuz (~13,6% de oferta mundial).
- Demanda y oferta de flujo estacionarias.
- $\dot R(h)$ reduced-form, no microfundamentada.
- Mapeo lineal h ↔ stock.
- Elasticidades constantes.
- Sin futures markets endógenos.

**11.2. ¿Cuáles son las limitaciones más importantes?**

1. **Calibración de σ es ad-hoc.** No identificable empíricamente con
   datos actuales.
2. **El modelo es estático en h.** No incorpora dinámicas de
   reabastecimiento durante el shock.
3. **No captura efectos macro de segunda ronda.** Inflación, tipo de
   cambio, política monetaria.
4. **Reduce el shock a una sola dimensión (cierre de Ormuz).** Shocks
   parciales, restricciones de tránsito, ataques selectivos quedan fuera.
5. **No hay heterogeneidad entre tenedores.** Trata SPRs comerciales y
   estratégicos como una única categoría.

**11.3. ¿La crítica de Lucas no aplica?**
Aplica parcialmente. Las elasticidades calibradas son short-run, derivadas
de shocks pasados; cambios de política podrían moverlas. Pero el horizonte
del modelo es de pocos meses, donde la asunción de elasticidades estables
es defensible.

**11.4. ¿Qué tan sensible es el resultado a σ?**
Muy sensible. Con $\sigma = 0{,}04$ la transición entre regímenes es
abrupta (cuasi-step function); con $\sigma = 0{,}15$ es muy suave. Es el
parámetro más débilmente identificado y el más influyente sobre la lectura
de θ. Lo conversamos como una de las motivaciones del v2.

---

## 12. Modelo v2 — qué viene

**12.1. ¿Qué problema resuelve el v2?**
El v1 sitúa la incertidumbre informacional sobre h. Empíricamente, los
inventarios son observables (IEA OMR, EIA WPSR, JODI publican datos
semanales/mensuales). La verdadera incertidumbre del caso Ormuz es la
**duración del cierre T**, que sí es no-observable y depende de geopolítica.

**12.2. ¿En qué consiste el v2?**
Reformula el global game sobre T en lugar de h. Cada agente recibe una
señal privada ruidosa sobre la duración esperada del shock. Si se proyecta
que T excede el tiempo crítico hasta el floor, retener es rentable; si no,
liberar lo es. Misma estructura matemática, distinto objeto.

**12.3. ¿Reemplaza al v1?**
No. Coexisten como pestañas distintas del dashboard. El v1 mantiene valor
pedagógico y como benchmark; el v2 es más identificable empíricamente y
más alineado con la narrativa de mercado.

**12.4. ¿Cuándo estará listo?**
Documento conceptual completo (en revisión). Implementación: 2-3 semanas
de trabajo una vez aprobado el conceptual. Está en `docs/modelo_v2_incertidumbre_T.md`.

**12.5. ¿Qué cambia en términos de outputs?**
El análogo del θ implícito pasa a ser **E[T] implícito**: días esperados de
duración del shock que el mercado está priciendo. Tiene unidades (días) y
es directamente comparable con surveys (Bloomberg consensus, JPMorgan
forecasts, Polymarket).

---

## 13. Interpretación e implicaciones

**13.1. ¿Qué nos dice el modelo sobre la situación actual (mayo 2026)?**
Datos del último IEA OMR (30-abril-2026): stock = 7.951 mb, Brent = 124,24
USD/bbl (FRED). Con la calibración, $h \approx 0{,}43$ — **por encima del
umbral de stress** ($h^\ast = 0{,}30$). El sistema opera principalmente en
régimen clásico bajo shock. Composite del modelo ≈ 115; observado = 124,24.
**El wedge es negativo** ($\theta_{\rm implícito} \approx -0{,}21$): el
mercado pricea más severidad que la que el modelo capta. Cuatro hipótesis
candidatas (no excluyentes): (a) modelo subestima fragilidad, (b) risk
premium no modelado, (c) elasticidades aún más bajas, (d) run regime
parcialmente activo. Es un hallazgo diagnóstico que orienta el refinamiento.

**13.2. ¿Es alarmante el nivel actual?**
No es señal de alarma de coordinación/run inmediata (estamos por encima del
umbral de fragilidad). Pero sí hay dos lecturas de fragilidad creciente:
(a) el margen al stress threshold (Stock_stress = 7.600) es solo ~351 mb,
equivalente a **~75-90 días al ritmo actual de drenaje** (~4 mb/d); (b) el
mercado no está descontando resolución, lo que sugiere que las expectativas
geopolíticas están alineadas con persistencia. Si el stock cae bajo 7.600,
$q$ subiría rápidamente y el modelo se desplazaría hacia $P_R \approx 147$
USD/bbl.

**13.3. ¿Qué métricas vale la pena monitorear?**
- Stock global (IEA OMR mensual).
- θ implícito diario (computable con precio Brent + modelo).
- Pendiente de la forward curve (proxy de E[T] del mercado).
- Dispersión de pronósticos de analistas (proxy de σ).

**13.4. ¿Cómo se relaciona con los pronósticos de bancos de inversión?**
JPMorgan, Goldman, Morgan Stanley publican rangos similares (110-140 USD/bbl
para los próximos 3-6 meses bajo cierre persistente). Nuestro composite a
h actual está en línea. El valor agregado del modelo no es el número sino
la *estructura*: descompone el precio en regímenes y en probabilidades.

**13.5. ¿Qué pasaría si las elasticidades fueran más altas?**
Con $\varepsilon_d = \varepsilon_s = 0{,}15$ (rango medio de la literatura),
el cap clásico bajaría de ~191 a ~125 USD/bbl. La sensibilidad a las
elasticidades es alta. Calibramos en el rango bajo (0,04-0,05) porque el
horizonte relevante es de meses, donde la elasticidad short-run es la
apropiada.

**13.6. ¿Implicaciones para política monetaria?**
El modelo es input para escenarios de inflación importada. Un movimiento
de Brent de 70 a 115 USD/bbl tiene impacto directo en IPC chileno vía
combustibles y transporte. El composite a h actual da un benchmark de
precio bajo escenario "persistencia"; el wedge con observado da la
probabilidad de "resolución" que pricea el mercado.

---

## 14. Preguntas más técnicas (si surgen)

**14.1. ¿Cómo se resuelve $P_C$ y $P_R$ numéricamente?**
Root-finding con scipy.brentq sobre la ecuación de market clearing, en el
rango [30, 2000] USD/bbl. Convergencia en milisegundos, robusta.

**14.2. ¿Hay tests unitarios?**
Sí. Verifican propiedades matemáticas clave: $P_C(0) \approx P_{\rm cap}$,
$P_C(\infty) \approx P_{\rm floor}$, $P_R(0) = P_C(0)$, $q(h^\ast) = 0{,}5$,
$\theta > 0$ cuando $P_{\rm modelo} > P_{\rm observado}$.

**14.3. ¿Se calibró contra episodios históricos?**
No formalmente. La calibración es por juicio + literatura. Una validación
contra 1990 (Kuwait), 2008 (Lehman), 2022 (Ucrania) sería natural pero
requiere armar dataset y mapear h en cada episodio. Es una extensión
identificada para próximas iteraciones.

**14.4. ¿El modelo es código abierto / replicable?**
Sí. Está en GitHub (`juanmarcosw-collab/oil-regime-model`), dashboard
deployado en Streamlit Community Cloud. Cualquier colega del banco puede
correrlo localmente o pedirle acceso al link público.

**14.5. ¿Quién más en el banco lo usa?**
Por ahora, el equipo de la DPM. El acceso se está extendiendo gradualmente.
Brian Pustilnik y Gent Bajraj tienen acceso desde la semana pasada.

---

## 15. Cierre — qué dejar en la sala

Tres mensajes para cerrar:

1. **El modelo es una herramienta de pensamiento estructurado, no un
   pronóstico.** Su valor está en la disciplina conceptual y en la métrica
   de θ implícito como tracker de expectativas.

2. **La calibración tiene un parámetro débil (σ).** Por eso estamos
   trabajando el v2, que sitúa la incertidumbre sobre T en lugar de h —
   más identificable empíricamente.

3. **Es trabajo en curso.** Está abierto a feedback. Las extensiones ya
   implementadas (4) y las próximas (v2) responden directamente a
   comentarios que esperamos recibir hoy.

---

## Apéndice A — Cheat sheet de notación

| Símbolo | Significado |
|---|---|
| $h$ | Buffer slack agregado (adimensional) |
| $h^\ast$ | Umbral del global game (default 0,30) |
| $\sigma$ | Dispersión de señales privadas (default 0,08) |
| $\dot R(h)$ | Tasa de release (mb/d) |
| $R_{\max}, h_R$ | Parámetros Michaelis-Menten del release (6, 0,12) |
| $P^\ast$ | Precio pre-shock (70 USD/bbl) |
| $P_C(h)$ | Precio régimen clásico |
| $P_R(h)$ | Precio régimen run |
| $q(h)$ | Probabilidad de régimen run |
| $P(h)$ | Composite = $(1-q) P_C + q P_R$ |
| $\theta$ | Probabilidad implícita de normalización |
| $\varepsilon_d, \varepsilon_s$ | Elasticidades demanda/oferta (0,05 / 0,04) |
| $\mu$ | Fracción del release retenida en run (0,5) |
| $\delta_0$ | Demanda especulativa en run (0) |
| Stock_floor, _stress, _opt | Umbrales JPMorgan (6.800 / 7.600 / 8.200 mb) |

## Apéndice B — Números clave para citar

- **Stock IEA OMR al 30-abril-2026:** 7.951 mb (último reporte; vs. 8.150 mb en enero).
- **Precio Brent observado al 30-abril-2026:** 124,24 USD/bbl (FRED DCOILBRENTEU) / 122,58 (Bloomberg M1).
- **$h_{\rm actual}$ (vía Ext 2):** ~0,43 (**por encima** de $h^\ast = 0{,}30$).
- **$\dot R(h_{\rm actual})$:** ~4,7 mb/d (consistente con IEA OMR).
- **$P_{\rm cap}$ del modelo:** ~191 USD/bbl ($h \to 0$).
- **$P_{\rm floor}$ del modelo:** ~95 USD/bbl ($h$ grande).
- **$P_C(h_{\rm actual})$:** ~113 USD/bbl.
- **$P_R(h_{\rm actual})$:** ~147 USD/bbl.
- **$q(h_{\rm actual})$:** ~0,05 (régimen clásico domina).
- **Composite $P(h_{\rm actual})$:** ~115 USD/bbl.
- **θ implícito al 30-abril:** ~−0,21 (wedge negativo; mercado pricea más severidad que el modelo).
- **Margen sobre Stock_stress (7.600):** 351 mb (~75-90 días al ritmo actual).
- **Margen sobre Stock_floor (6.800):** 1.151 mb (~9-10 meses al ritmo actual).
