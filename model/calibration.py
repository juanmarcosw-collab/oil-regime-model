"""
Calibración del modelo estructural del precio del petróleo.

Valores por defecto y sus fuentes, con referencias a secciones del PDF
"Modelo estructural del precio del petróleo bajo stress de oferta" (BCCh, mayo 2026).
"""

from dataclasses import dataclass


@dataclass
class ModelParams:
    """
    Calibración del modelo estructural del petróleo.

    Todos los valores por defecto corresponden a la calibración reportada en
    la sección 8 del documento de trabajo BCCh (mayo 2026).
    """

    # === Parámetros estructurales (Sección 8.1) ===
    # Fundamentos bien anclados en literatura

    P_star: float = 70.0
    """
    Precio de referencia pre-shock (USD/bbl).

    Precio de equilibrio de mercado antes del cierre de Ormuz (febrero 2026).
    Brent spot a principios de febrero 2026.
    """

    D_0: float = 104.0
    """
    Demanda mundial de petróleo al precio P* (millones de barriles/día).

    Calibración: promedio pre-guerra (2024-febrero 2026).
    Fuente: IEA Oil Market Report.
    """

    S_f0: float = 95.0
    """
    Oferta de flujo mundial durante el shock (millones de barriles/día).

    Asume cierre persistente del Estrecho de Ormuz (~13.6% de la oferta mundial).
    Producción mundial en mayo 2026: ~95 mb/d vs. ~104 mb/d pre-guerra.
    """

    eps_d: float = 0.05
    """
    Elasticidad short-run de la demanda.

    Valora el cambio porcentual en cantidad demandada ante un cambio del 1% en precio.
    Calibración BCCh (sección 8.1): 0.05, en el rango bajo [0.08-0.20] reportado
    por Caldara et al. (2019) para otros shocks. Justificación: consumo de petróleo
    es esencial en el corto plazo, poco sustitución posible.
    """

    eps_s: float = 0.05
    """
    Elasticidad short-run de la oferta.

    Cambio porcentual en cantidad ofrecida ante un cambio del 1% en precio.
    Calibración BCCh (sección 8.1): 0.05. La oferta es poco elástica en el corto plazo
    porque la capacidad de producción está limitada por inversiones de largo plazo
    (shale, deepwater).
    """

    # === Función de release (Sección 8.2) ===
    # Parámetros de la liberación coordinada de reservas estratégicas

    R_max: float = 6.0
    """
    Capacidad técnica máxima de liberación coordinada de reservas (millones de barriles/día).

    Calibración: capacidad histórica observada de la IEA al pico. Aproximadamente 6 mb/d
    en coordenadas de releases G7 (2011 Libia, 2022 Ucrania). Sección 8.2 del PDF.
    """

    h_R: float = 0.12
    """
    Parámetro de saturación de la función de release.

    Determina la velocidad a la cual release_rate(h) se acerca a R_max.
    Forma funcional: dot_R(h) = R_max · h / (h + h_R) (Michaelis-Menten).

    Con calibración h_R = 0.12: a h ≈ 0.24 (condición estimada mayo 2026),
    el release está en ~2/3 de saturación (~4.0 mb/d), consistente con OMR.
    """

    # === Régimen de run (Sección 8.4) ===
    # Dinámica de pánico coordinado

    mu: float = 0.5
    """
    Fracción del release de reservas retenida por hoarders en el run.

    En el régimen de pánico, los holders de inventario anticipan precios futuros
    mayores y retienen una fracción μ del flujo liberado. La interpretación:
    μ = 0: todos aceptan el release en el mercado (clásico puro).
    μ = 1: todos retienen (intensidad máxima del hoarding).

    Calibración: 0.5 (default razonable sin evidencia empírica fuerte para este parámetro).
    Ver sección 6.4 del PDF.
    """

    delta_0: float = 0.0
    """
    Demanda especulativa adicional en el run (millones de barriles/día saturada).

    En el régimen de pánico, los speculators compran inventario anticipando precios
    mayores. delta(h) = delta_0 · dot_R(h) / R_max (saturada en el release disponible).

    Calibración: 0.0 (neutral). Un valor positivo aumentaría la presión al alza en el run.
    Ver sección 6.4 del PDF.
    """

    # === Global game Goldstein-Pauzner (Sección 8.3) ===
    # Probabilidad de transición entre regímenes

    h_star: float = 0.30
    """
    Umbral crítico del global game (nivel de buffer slack).

    En la teoría de Goldstein-Pauzner (2005), existe un nivel crítico h* tal que:
    - Para h > h*: régimen clásico es el equilibrio único (q(h) baja).
    - Para h < h*: existe riesgo de transición coordinada al régimen run.
    - Para h = h*: ambos equilibrios son igualmente probables (q(h*) = 0.5).

    Calibración: 0.30 (estimación razonable; sensibilidad importante).
    """

    sigma: float = 0.08
    """
    Dispersión de señales privadas en el global game (desviación estándar).

    Controla la suavidad de la transición entre regímenes. Con σ pequeño,
    la transición es abrupta (tipo salto) cerca de h*. Con σ grande, es gradual.

    Probabilidad de régimen run: q(h) = Φ((h* - h) / σ), donde Φ es la CDF normal.

    Calibración: 0.08 (transición suave pero pronunciada). Ver sección 8.3 del PDF.
    """


# Función helper para crear instancias
def default_params() -> ModelParams:
    """Retorna una instancia de ModelParams con calibración BCCh (mayo 2026)."""
    return ModelParams()
