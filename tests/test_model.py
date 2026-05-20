"""
Tests unitarios para el modelo estructural del petróleo.

Verifica propiedades matemáticas y de calibración del modelo.
"""

import pytest
from model import (
    ModelParams, default_params,
    P_classical, P_run, q_run,
    theta_implicit, P_cap, P_floor
)


class TestClassicalRegime:
    """Tests del régimen clásico."""

    def test_P_cap_at_h_zero(self):
        """P_C(h=0) debe ser aproximadamente igual a P_cap."""
        params = default_params()
        P_C_zero = P_classical(0.001, params)  # h muy pequeño
        P_cap_val = P_cap(params)
        # Tolerancia: 5% porque el solver es numérico y hay release pequeño
        assert abs(P_C_zero - P_cap_val) / P_cap_val < 0.05

    def test_P_floor_at_large_h(self):
        """P_C(h→∞) debe ser aproximadamente igual a P_floor."""
        params = default_params()
        P_C_large = P_classical(100.0, params)
        P_floor_val = P_floor(params)
        assert abs(P_C_large - P_floor_val) / P_floor_val < 0.01

    def test_P_classical_positive(self):
        """El precio clásico debe ser siempre positivo."""
        params = default_params()
        for h in [0.1, 0.24, 0.5, 1.0]:
            P_C = P_classical(h, params)
            assert P_C > 0


class TestRunRegime:
    """Tests del régimen de run."""

    def test_P_run_convergence_at_zero(self):
        """P_R(0) debe aproximarse a P_C(0) cuando no hay release."""
        params = default_params()
        P_C_zero = P_classical(0.001, params)
        P_R_zero = P_run(0.001, params)
        # En el límite h→0, ambas deben coincidir (no hay inventario que hoarb)
        assert abs(P_R_zero - P_C_zero) / P_C_zero < 0.05

    def test_P_run_positive(self):
        """El precio en run debe ser siempre positivo."""
        params = default_params()
        for h in [0.1, 0.24, 0.5, 1.0]:
            P_R = P_run(h, params)
            assert P_R > 0


class TestGlobalGame:
    """Tests del global game Goldstein-Pauzner."""

    def test_q_at_h_star(self):
        """q(h*) debe ser 0.5 (probabilidad equiparable en el umbral)."""
        params = default_params()
        q_star = q_run(params.h_star, params)
        assert abs(q_star - 0.5) < 0.001

    def test_q_decreasing(self):
        """q(h) debe ser decreciente en h (menos buffer → más riesgo de run)."""
        params = default_params()
        q1 = q_run(0.2, params)
        q2 = q_run(0.3, params)
        q3 = q_run(0.4, params)
        assert q1 > q2 > q3

    def test_q_bounds(self):
        """q(h) debe estar siempre en [0, 1]."""
        params = default_params()
        for h in [0.01, 0.1, 0.24, 0.5, 1.0, 2.0]:
            q = q_run(h, params)
            assert 0 <= q <= 1


class TestTheta:
    """Tests de la probabilidad implícita de normalización."""

    def test_theta_positive_when_model_above_observed(self):
        """θ > 0 cuando P_modelo > P_observado (el mercado espera normalización)."""
        params = default_params()
        P_model = 120.0
        P_observed = 110.0
        theta = theta_implicit(P_model, P_observed, params)
        assert theta > 0

    def test_theta_negative_when_model_below_observed(self):
        """θ < 0 cuando P_modelo < P_observado (el mercado es más pesimista)."""
        params = default_params()
        P_model = 100.0
        P_observed = 110.0
        theta = theta_implicit(P_model, P_observed, params)
        assert theta < 0

    def test_theta_zero_when_model_equals_observed(self):
        """θ = 0 cuando P_modelo = P_observado."""
        params = default_params()
        P_model = 115.0
        P_observed = 115.0
        theta = theta_implicit(P_model, P_observed, params)
        assert theta == 0

    def test_theta_one_when_observed_equals_P_star(self):
        """θ = 1 cuando P_observado = P* (mercado presiona normalización completa)."""
        params = default_params()
        P_model = 120.0
        P_observed = params.P_star
        theta = theta_implicit(P_model, P_observed, params)
        assert abs(theta - 1.0) < 0.001


class TestParameterSensitivity:
    """Tests de sensibilidad a variaciones de parámetros."""

    def test_P_increases_with_demand(self):
        """El precio debe aumentar cuando aumenta la demanda."""
        params_low = ModelParams(D_0=100.0)
        params_high = ModelParams(D_0=110.0)

        h_test = 0.3
        P_low = P_classical(h_test, params_low)
        P_high = P_classical(h_test, params_high)
        assert P_high > P_low

    def test_P_decreases_with_supply(self):
        """El precio debe disminuir cuando aumenta la oferta."""
        params_low = ModelParams(S_f0=90.0)
        params_high = ModelParams(S_f0=100.0)

        h_test = 0.3
        P_low = P_classical(h_test, params_low)
        P_high = P_classical(h_test, params_high)
        assert P_low > P_high

    def test_P_decreases_with_release(self):
        """El precio debe disminuir cuando aumenta la capacidad de release."""
        params_low = ModelParams(R_max=4.0)
        params_high = ModelParams(R_max=8.0)

        h_test = 0.3
        P_low = P_classical(h_test, params_low)
        P_high = P_classical(h_test, params_high)
        assert P_low > P_high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
