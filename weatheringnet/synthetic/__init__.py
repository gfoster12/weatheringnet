"""
Synthetic — Foster Rx synthetic cohort generation client.

Provides a thin client for the Foster Rx Synthetic Data Engine, used to
generate certified synthetic cohorts for WeatheringNet simulation and
power analysis.

Functions:
    generate_cohort     — Request a synthetic cohort from the Foster Rx engine.
    verify_certificate  — Verify a SYNTHETIC_DATA certificate for a completed job.
    check_engine_health — Check if the Foster Rx engine is reachable.

Exceptions:
    FosterRxError       — Raised on engine errors or timeouts.
"""

from weatheringnet.synthetic.client import (
    FosterRxError,
    check_engine_health,
    generate_cohort,
    verify_certificate,
)

__all__ = [
    "generate_cohort",
    "verify_certificate",
    "check_engine_health",
    "FosterRxError",
]
