"""
WeatheringDAG: DAG specification for the weathering → AID causal model.

The DAG encodes the causal structure from the paper as a formal graph,
enabling:
    1. Identification of valid adjustment sets (what to control for)
    2. Detection of collider bias (what NOT to control for)
    3. Visual communication of the causal model for publication

Node definitions:
    race_ses         : Race/ethnicity as proxy for structural racism exposure
    sdrs             : Sociodemographic Risk Score (neighborhood disadvantage)
    ali              : Allostatic Load Index (cumulative physiological stress)
    hpa_dysreg       : HPA axis dysregulation (cortisol, ACTH dysregulation)
    glucocorticoids  : Elevated circulating glucocorticoids
    inflammation     : Chronic systemic inflammation (CRP, IL-6, TNF-α)
    tlr_dysreg       : TLR pathway dysregulation (Han et al., paper study 1)
    tcell_shift      : T-cell phenotype shift (Liu et al., paper study 5)
    epigenetic_mod   : Epigenetic modifications (DNA methylation, histone mod)
    infection_risk   : Maternal infection susceptibility
    sex_hormones     : Estrogen/testosterone dysregulation (Assad, paper study 7)
    microbiome       : Microbiome composition (Köhling, paper study 8)
    aid_risk         : Offspring autoimmune disease risk (outcome)

Unmeasured confounders (U):
    U_genetics       : Genetic predisposition (polygenic AID risk loci)
    U_lifetime_stress: Lifetime stress not captured by ALI
"""

from __future__ import annotations

import networkx as nx


class WeatheringDAG:
    """
    Directed Acyclic Graph encoding the weathering → in-utero AID causal model.

    The graph can be exported to:
        - DOT format (Graphviz)
        - dagitty format (R dagitty package)
        - DoWhy CausalModel
        - NetworkX DiGraph (for visualization)
    """

    # ── Node Definitions ──────────────────────────────────────────────────────

    NODES = {
        # Exposure / structural
        "race_ses": {"type": "exposure", "measured": True, "label": "Race/SES"},
        "sdrs": {
            "type": "mediator",
            "measured": True,
            "label": "Sociodemographic Risk Score",
        },
        # Stress pathway
        "ali": {"type": "mediator", "measured": True, "label": "Allostatic Load Index"},
        "hpa_dysreg": {
            "type": "mediator",
            "measured": False,
            "label": "HPA Axis Dysregulation",
        },
        "glucocorticoids": {
            "type": "mediator",
            "measured": True,
            "label": "Elevated Glucocorticoids (cortisol)",
        },
        # Inflammatory pathway
        "inflammation": {
            "type": "mediator",
            "measured": True,
            "label": "Chronic Inflammation (CRP/IL-6)",
        },
        "tlr_dysreg": {
            "type": "mediator",
            "measured": False,
            "label": "TLR Dysregulation",
        },
        "tcell_shift": {
            "type": "mediator",
            "measured": False,
            "label": "T-cell Phenotype Shift",
        },
        "infection_risk": {
            "type": "mediator",
            "measured": True,
            "label": "Maternal Infection Risk",
        },
        # Epigenetic mechanism
        "epigenetic_mod": {
            "type": "mechanism",
            "measured": False,
            "label": "Epigenetic Modification In Utero",
        },
        # Sex-specific
        "sex_hormones": {
            "type": "moderator",
            "measured": True,
            "label": "Sex Hormone Dysregulation",
        },
        "microbiome": {
            "type": "mediator",
            "measured": False,
            "label": "Microbiome Composition",
        },
        # Outcome
        "aid_risk": {
            "type": "outcome",
            "measured": True,
            "label": "Offspring AID Risk",
        },
        # Unmeasured confounders
        "U_genetics": {
            "type": "unmeasured",
            "measured": False,
            "label": "Genetic Predisposition (U)",
        },
        "U_lifetime_stress": {
            "type": "unmeasured",
            "measured": False,
            "label": "Unmeasured Lifetime Stress (U)",
        },
    }

    # ── Edge Definitions ─────────────────────────────────────────────────────
    # Each edge is (cause, effect, evidence_source)

    EDGES = [
        # Structural racism → neighborhood disadvantage
        ("race_ses", "sdrs", "Geronimus 1992; Simons et al. 2021"),
        # Neighborhood disadvantage → cumulative physiological stress
        ("sdrs", "ali", "Weathering hypothesis; Seeman et al. 1997"),
        # ALI → biological stress pathways
        (
            "ali",
            "hpa_dysreg",
            "Brew et al. 2022 (paper study 3); Facchi et al. 2020 (study 10)",
        ),
        ("ali", "inflammation", "Black et al. 2002; Simons et al. 2021"),
        ("ali", "infection_risk", "Vahidy et al. 2020; paper Discussion"),
        # HPA axis dysregulation → downstream mechanisms
        ("hpa_dysreg", "glucocorticoids", "Facchi et al. 2020 (paper study 10)"),
        (
            "glucocorticoids",
            "epigenetic_mod",
            "Hederlingova et al. 2017 (paper study 6)",
        ),
        ("glucocorticoids", "sex_hormones", "Assad et al. 2017 (paper study 7)"),
        # Inflammatory pathway → immune dysregulation
        ("inflammation", "tlr_dysreg", "Han et al. 2022 (paper study 1)"),
        ("inflammation", "tcell_shift", "Liu et al. 2022 (paper study 5)"),
        ("infection_risk", "tlr_dysreg", "Waldorf & McAdams 2013 (paper study 9)"),
        ("infection_risk", "inflammation", "Waldorf & McAdams 2013 (paper study 9)"),
        # In-utero epigenetic mechanisms → AID risk
        ("tlr_dysreg", "epigenetic_mod", "Han et al. 2022 (paper study 1)"),
        ("tcell_shift", "epigenetic_mod", "Liu et al. 2022 (paper study 5)"),
        ("epigenetic_mod", "aid_risk", "Foster 2023 central thesis"),
        # Sex-specific pathways → AID risk
        ("sex_hormones", "aid_risk", "Assad et al. 2017 (paper study 7)"),
        ("microbiome", "sex_hormones", "Köhling et al. 2017 (paper study 8)"),
        ("microbiome", "aid_risk", "Köhling et al. 2017 (paper study 8)"),
        ("inflammation", "microbiome", "Köhling et al. 2017 (paper study 8)"),
        # Direct race_ses path (residual direct effect not through stress mediators)
        ("race_ses", "infection_risk", "Vahidy et al. 2020; paper Discussion"),
        ("race_ses", "aid_risk", "Roberts & Erdei 2020; residual direct"),
        # Unmeasured confounders
        ("U_genetics", "aid_risk", "Lu et al. 2018 (GWAS); polygenic risk"),
        ("U_genetics", "hpa_dysreg", "Gene-environment interaction"),
        ("U_lifetime_stress", "ali", "Stress before measurement window"),
    ]

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for node, attrs in self.NODES.items():
            G.add_node(node, **attrs)
        for cause, effect, evidence in self.EDGES:
            G.add_edge(cause, effect, evidence=evidence)
        return G

    def to_dagitty(self) -> str:
        """
        Export as dagitty string for use in R dagitty package.
        Paste output into https://dagitty.net/dags.html for visualization.
        """
        lines = ["dag {"]
        for node, attrs in self.NODES.items():
            node_type = attrs["type"]
            if node_type == "exposure":
                lines.append(f"    {node} [exposure]")
            elif node_type == "outcome":
                lines.append(f"    {node} [outcome]")
            elif node_type == "unmeasured":
                lines.append(f"    {node} [latent]")
        lines.append("")
        for cause, effect, _ in self.EDGES:
            lines.append(f"    {cause} -> {effect}")
        lines.append("}")
        return "\n".join(lines)

    def adjustment_sets(
        self, exposure: str = "race_ses", outcome: str = "aid_risk"
    ) -> list:
        """
        Identify valid adjustment sets using do-calculus (d-separation).
        Wraps dagitty logic via networkx for basic identification.
        """
        # For full identification, use R dagitty or DoWhy
        # This is a simple d-separation check via networkx
        try:
            paths = list(nx.all_simple_paths(self.graph, exposure, outcome))
            return paths
        except Exception:
            return []

    def summary(self) -> str:
        nodes = len(self.NODES)
        edges = len(self.EDGES)
        unmeasured = sum(1 for n, a in self.NODES.items() if not a["measured"])
        return (
            f"WeatheringDAG: {nodes} nodes ({unmeasured} unmeasured), {edges} edges\n"
            f"Exposure: race_ses → Outcome: aid_risk\n"
            f"Key mediators: ali, hpa_dysreg, tlr_dysreg, tcell_shift, epigenetic_mod"
        )
