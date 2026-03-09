"""
Causal — DAG specification and mediation analysis for the weathering model.

Encodes the causal structure from Foster (2023) as a formal directed acyclic
graph, enabling identification of valid adjustment sets and quantification
of mediated effects through the stress/allostatic load pathway.

Classes:
    WeatheringDAG       — DAG encoding the weathering → AID causal model.
    MediationAnalyzer   — Counterfactual mediation analysis (NDE/NIE decomposition).

Functions:
    identify_adjustment_set — Identify valid conditioning sets for causal estimation.
"""

from weatheringnet.causal.dag import WeatheringDAG
from weatheringnet.causal.mediation import MediationAnalyzer, identify_adjustment_set

__all__ = [
    "WeatheringDAG",
    "MediationAnalyzer",
    "identify_adjustment_set",
]
