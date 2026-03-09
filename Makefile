.PHONY: setup synthetic ali sdrs model figures test reproduce-paper clean help

PYTHON := .venv/bin/python
DVC := .venv/bin/dvc

help: ## Show this help message
	@echo "WeatheringNet — Makefile targets"
	@echo "================================"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Install dependencies and pre-commit hooks
	@echo "==> Setting up WeatheringNet development environment..."
	python3 -m venv .venv || true
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	PRE_COMMIT_HOME="$$(pwd)/.pre-commit-cache" .venv/bin/pre-commit install
	@echo "==> Setup complete."

synthetic: ## Generate synthetic cohort data
	@echo "==> Generating synthetic cohort data..."
	$(DVC) repro generate_synthetic
	@echo "==> Synthetic data generated."

ali: ## Run Allostatic Load Index pipeline on NHANES data
	@echo "==> Running ALI pipeline..."
	$(DVC) repro ali
	@echo "==> ALI pipeline complete."

sdrs: ## Build Sociodemographic Risk Score for US census tracts
	@echo "==> Building SDRS..."
	$(DVC) repro sdrs
	@echo "==> SDRS complete."

model: ## Train AID risk prediction model
	@echo "==> Training AID risk model..."
	$(DVC) repro model
	@echo "==> Model training complete."

figures: ## Generate publication figures (SHAP, equity plots)
	@echo "==> Generating figures..."
	$(DVC) repro figures
	@echo "==> Figures complete."

test: ## Run test suite with coverage
	@echo "==> Running tests..."
	$(PYTHON) -m pytest tests/ -v --tb=short
	@echo "==> Tests complete."

reproduce-paper: ## Reproduce full paper pipeline end-to-end
	@echo "==> Reproducing full paper pipeline..."
	$(DVC) repro
	@echo "==> Full pipeline reproduced."

clean: ## Remove generated artifacts and caches
	@echo "==> Cleaning generated files..."
	rm -rf data/processed/*.parquet data/processed/*.csv data/processed/figures
	rm -rf data/processed/model.pkl
	rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "==> Clean complete."
