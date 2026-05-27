Tu observación es estructuralmente correcta y apunta a una limitación real del modelo. Lo desarrollo en bloques.

  1. Por qué el paper puso la incertidumbre sobre h

  Es por fidelidad al template Goldstein-Pauzner: en bank runs la "fundamental" es la solvencia del banco, que los depositantes
  observan con ruido. Trasladado al petróleo, la fundamental natural es el buffer agregado h, y los agentes lo ven con ruido
  idiosincrásico.

  Esa elección es pedagógica y matemáticamente cómoda, pero empíricamente débil: IEA OMR, EIA WPSR, JODI, OECD-OMR publican
  inventarios casi semanalmente. No hay dispersión informacional seria sobre h. La σ del global game en el paper es un
  placeholder, no algo identificable contra datos.

  Es la crítica clásica que se le hace a modelos de información heterogénea aplicados a mercados con data pública abundante: "if
  everyone reads the OMR, where's the heterogeneity?".

  2. La verdadera fuente de incertidumbre: la duración T

  Tenés razón: en el cierre de Ormuz lo que el mercado no sabe es cuánto va a durar. T depende de:

  - Decisiones iranéficas de re-escalamiento o de-escalamiento.
  - Respuesta militar (5ta Flota, operaciones de re-apertura, MCM).
  - Diplomacia (Qatar, Omán como mediadores).
  - Daño físico al Strait (minado, infraestructura energética).

  T no es observable, no es semanal, y los analistas geopolíticos serios difieren significativamente. Esto sí justifica un objeto
   con dispersión informacional.

  La consecuencia operacional es exacta lo que decís: el mismo h actual se interpreta como mucho o poco según el T esperado. Con
  h_0 = 7.951 mb y dot_R ≈ 4 mb/d:

  ┌──────────┬────────────────────────────────────────┬───────────┐
  │    T     │          h al final del shock          │  Régimen  │
  ├──────────┼────────────────────────────────────────┼───────────┤
  │ 30 días  │ ~7.831 mb (sobrado)                    │ clásico   │
  ├──────────┼────────────────────────────────────────┼───────────┤
  │ 90 días  │ ~7.591 mb (cerca del stress threshold) │ composite │
  ├──────────┼────────────────────────────────────────┼───────────┤
  │ 180 días │ ~7.231 mb (debajo del threshold)       │ run       │
  ├──────────┼────────────────────────────────────────┼───────────┤
  │ 365 días │ ~6.491 mb (debajo del floor)           │ colapso   │
  └──────────┴────────────────────────────────────────┴───────────┘

  El estado h no determina el régimen; lo determinan h y T juntos. Pero T es lo único realmente incierto.

  3. Reformulación natural del modelo: el global game sobre T

  La estructura se preserva pero cambia el espacio de señales:

  Setup
  - T ∼ F(τ; θ_geo) duración aleatoria, con θ_geo capturando la situación geopolítica.
  - Cada tenedor de inventario recibe s_i = T + ε_i, con ε_i ∼ N(0, σ_T²).
  - σ_T mide dispersión de expectativas geopolíticas — esto sí es heterogéneo y observable (encuestas a analistas, dispersión de
  pronósticos en Bloomberg/Reuters).

  Decisión
  Cada agente, dado su pronóstico s_i de T, calcula su payoff esperado:
  - Si s_i es bajo (Ormuz reabre rápido): el sistema no se drena hasta h*, no se materializa el run, conviene liberar inventario
  ahora a P_C.
  - Si s_i es alto: el sistema se drena, h cruza h*, conviene retener para vender a P_R más adelante.

  Umbral del game
  Existe s* tal que el agente retiene sii s_i > s*. La fracción agregada que retiene es:

  $$q(T, h_0) = 1 - \Phi!\left(\frac{s^* - T}{\sigma_T}\right)$$

  donde s* se calibra de modo que τ_crítico(h_0) = E[T crítico para que el sistema cruce h*]. Es decir, s* es la duración crítica
   del shock para el h actual, una función de h_0 y la dinámica de drenado.

  Precio observado
  En lugar de P(h) = (1−q(h))P_C(h) + q(h)P_R(h), ahora:

  $$P_t = (1 - q_t) \cdot P_C(h_t) + q_t \cdot P_R(h_t)$$

  con q_t = q(E_t[T], h_t). El precio se mueve porque (a) h_t baja con el tiempo y (b) las creencias sobre T se actualizan con
  noticias geopolíticas.

  4. Qué cambia y qué se mantiene

  ┌──────────────────┬──────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
  │     Elemento     │        Estado actual         │                    Versión "incertidumbre sobre T"                     │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ h                │ abstracto, calibrado a       │ observable cada semana                                                 │
  │                  │ stocks                       │                                                                        │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ σ                │ dispersión de info sobre h   │ dispersión de expectativas sobre T                                     │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ h*               │ umbral teórico del game      │ derivable de τ_crítico dado h_0                                        │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ P_C, P_R         │ sin cambios                  │ sin cambios                                                            │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ dot_R            │ sin cambios                  │ sin cambios                                                            │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ θ                │ wedge diagnóstico            │ se reinterpreta: prob. de que T sea corto (de hecho θ ≈ P(T <          │
  │                  │                              │ τ_crítico))                                                            │
  ├──────────────────┼──────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
  │ P* con           │ sin cambios                  │ sin cambios                                                            │
  │ reposición       │                              │                                                                        │
  └──────────────────┴──────────────────────────────┴────────────────────────────────────────────────────────────────────────┘

  Lo elegante es que θ y σ_T se convierten en el mismo objeto bajo dos lecturas: ambos miden cuánto cree el mercado en una
  resolución rápida. La identificación se vuelve más limpia.

  5. Cómo implementarlo en la app

  Tres cambios concretos en la UI:

  1. Reemplazar slider de σ por σ_T (días de dispersión en pronósticos de T). Default ~30-60 días.
  2. Agregar slider de E[T] (duración esperada del shock, en días). Default ~60-90 días según el contexto.
  3. Computar internamente τ_crítico(h_0) integrando dot_R(h(t)) desde h_0 hasta h*. Eso te da s*.

  La figura principal puede cambiar: en vez de P vs. h, mostrar P vs. E[T] para h_0 fijo. Es más intuitivo para usuarios
  geopolíticos: "si la duración esperada del cierre es de 60 días, el precio es X; si es 120 días, es Y".

  Mantenete la figura (h, P) como vista alternativa ("model space"), pero la principal pasa a ser (T, P).

  6. Recomendación

  La reformulación es la dirección correcta y es la versión que tiene chance de ser leída por gente del mercado petrolero. Tres
  pasos sugeridos:

  1. Primer paso (rápido): agregar a la app actual una "vista T" donde fijás h_0 y barés E[T]. Eso ya te da el 80% del insight
  sin reescribir el core.
  2. Segundo paso (medio): derivar τ_crítico(h_0) y reemplazar el global game (h*, σ_h) por (E[T], σ_T).
  3. Tercer paso (modeling work): pensar formalmente la distribución de T (probablemente Weibull o exponencial con hazard
  variable según señales) y endogenizar las creencias.

  ¿Querés que armemos primero la "vista T" como overlay sobre el modelo actual, o preferís hacer el cambio de fondo desde el
  principio?