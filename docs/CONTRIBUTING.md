# Contributing to WeatheringNet

Thank you for your interest in contributing to this project.

## Guiding Principles

1. **Evidence-based**: Every biological mechanism, biomarker threshold, and causal edge must be traceable to a peer-reviewed source. Add citations in code comments.
2. **Equity-centered**: We treat race as a social construct and proxy for structural racism exposure — never as a biological determinant. See the Ethical Considerations section of the README.
3. **Reproducible**: All pipelines must be reproducible from raw public data with a single command.
4. **Interpretable**: Model components must map to biological mechanisms from the literature.

## Development Setup

```bash
git clone https://github.com/yourusername/weatheringnet.git
cd weatheringnet
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Python: Black + Ruff
- All public functions must have docstrings citing the relevant paper/mechanism
- Type hints required for all function signatures

## Adding a New Biomarker to ALI

1. Add a `BiomarkerConfig` entry in `weatheringnet/ali/biomarkers.py`
2. Include `nhanes_code`, `risk_threshold`, `mechanism`, and `reference`
3. Add to `PRIMARY_ALI_BIOMARKERS` or `EXTENDED_ALI_BIOMARKERS` as appropriate
4. Add a test in `tests/unit/test_ali_calculator.py`

## Adding a New Causal Edge to the DAG

1. Add the edge tuple to `WeatheringDAG.EDGES` in `weatheringnet/causal/dag.py`
2. Include the evidence citation (author, year, study description)
3. Update `tests/unit/test_dag.py` to verify the new edge
4. Ensure the DAG remains acyclic (the test suite checks this)

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/biomarker-cortisol`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/`
4. Update documentation if needed
5. Submit PR with description referencing the biological motivation

## Questions

Open an issue or reach out — this project sits at the intersection of
epidemiology, causal inference, and ML engineering, and contributions from
all three communities are welcome.
