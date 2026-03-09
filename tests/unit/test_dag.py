"""Tests for WeatheringDAG structure and causal assumptions."""

import pytest
from weatheringnet.causal.dag import WeatheringDAG


@pytest.fixture
def dag():
    return WeatheringDAG()


class TestWeatheringDAG:

    def test_dag_has_exposure_and_outcome(self, dag):
        assert "race_ses" in dag.NODES
        assert "aid_risk" in dag.NODES
        assert dag.NODES["race_ses"]["type"] == "exposure"
        assert dag.NODES["aid_risk"]["type"] == "outcome"

    def test_dag_is_acyclic(self, dag):
        """DAG must be acyclic — cycles invalidate causal identification."""
        import networkx as nx
        assert nx.is_directed_acyclic_graph(dag.graph), "DAG contains cycles — invalid causal model"

    def test_path_exists_from_exposure_to_outcome(self, dag):
        import networkx as nx
        assert nx.has_path(dag.graph, "race_ses", "aid_risk")

    def test_stress_pathway_present(self, dag):
        """Core paper pathway: race_ses → sdrs → ali → HPA → epigenetic → aid_risk"""
        G = dag.graph
        assert G.has_edge("race_ses", "sdrs")
        assert G.has_edge("sdrs", "ali")
        assert G.has_edge("ali", "hpa_dysreg")
        assert G.has_edge("epigenetic_mod", "aid_risk")

    def test_paper_study_edges_present(self, dag):
        """Spot-check edges grounded in specific paper studies."""
        G = dag.graph
        # Han et al. (study 1): inflammation → TLR dysregulation
        assert G.has_edge("inflammation", "tlr_dysreg")
        # Liu et al. (study 5): inflammation → T-cell shift
        assert G.has_edge("inflammation", "tcell_shift")
        # Waldorf (study 9): infection → TLR dysregulation
        assert G.has_edge("infection_risk", "tlr_dysreg")
        # Assad (study 7): sex hormones → AID risk
        assert G.has_edge("sex_hormones", "aid_risk")

    def test_dagitty_export(self, dag):
        dagitty_str = dag.to_dagitty()
        assert "dag {" in dagitty_str
        assert "race_ses [exposure]" in dagitty_str
        assert "aid_risk [outcome]" in dagitty_str
        assert "->" in dagitty_str

    def test_all_edges_have_evidence(self, dag):
        """Every edge should cite a source — enforces evidence-based DAG construction."""
        for cause, effect, evidence in dag.EDGES:
            assert evidence, f"Edge {cause}→{effect} has no evidence citation"
            assert len(evidence) > 5, f"Edge {cause}→{effect} evidence too short: '{evidence}'"
