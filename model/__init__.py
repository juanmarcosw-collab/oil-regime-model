"""
Model package: núcleo del modelo estructural del petróleo.
"""

from .calibration import ModelParams, default_params
from .core import (
    release_rate, delta_run,
    P_classical, P_run, q_run, P_composite
)
from .empirics import (
    theta_implicit, P_cap, P_floor
)

__all__ = [
    # Calibration
    "ModelParams",
    "default_params",
    # Core functions
    "release_rate",
    "delta_run",
    "P_classical",
    "P_run",
    "q_run",
    "P_composite",
    # Empirics
    "theta_implicit",
    "P_cap",
    "P_floor",
]
