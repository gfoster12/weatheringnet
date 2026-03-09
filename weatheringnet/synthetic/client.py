"""
weatheringnet/synthetic/client.py
==================================
Thin client for the Foster Rx Synthetic Data Engine.

WeatheringNet uses this module as its sole integration point with the Foster Rx
engine. The engine is separately licensed; see https://www.fosterrx.com for
access and partnership information.

Environment variables (set in .env or CI secrets — never commit values):
    FOSTER_RX_API_URL   Base URL of the Foster Rx engine instance
                        Default: http://localhost:8000 (local Docker dev)
    FOSTER_RX_API_KEY   Licensed API key for certified generation
                        Leave empty to use open-source mode (no certificate issued)

Usage:
    from weatheringnet.synthetic.client import generate_cohort
    parquet_path = generate_cohort(
        params_path=Path("configs/synthetic_params.yaml"),
        n=10_000,
        seed=42,
    )
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

import httpx
import yaml

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_API_URL = os.environ.get("FOSTER_RX_API_URL", "http://localhost:8000")
_API_KEY = os.environ.get("FOSTER_RX_API_KEY", "")
_POLL_INTERVAL_S = 5
_TIMEOUT_S = 600  # 10 min ceiling for large n runs


class FosterRxError(RuntimeError):
    """Raised when the Foster Rx engine returns an error or times out."""


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def generate_cohort(
    params_path: Path,
    n: int = 10_000,
    seed: int = 42,
    schema_version: str = "0.2.0",
    output_dir: Path | None = None,
) -> Path:
    """
    Request a certified synthetic cohort from the Foster Rx engine.

    Reads stratification and parameter configuration from *params_path*
    (configs/synthetic_params.yaml), submits a WorkflowRequest to the engine,
    polls until the job completes, downloads the resulting parquet file, and
    returns its path.

    Parameters
    ----------
    params_path : Path
        Path to synthetic_params.yaml relative to repo root.
    n : int
        Number of synthetic subjects. Use 10_000 for development,
        50_000 for the final paper run (see DECISION-025).
    seed : int
        Random seed for reproducibility (see DECISION-002).
    schema_version : str
        synthetic_params.yaml schema version — must match engine expectation.
    output_dir : Path, optional
        Directory to write the downloaded parquet. Defaults to data/synthetic/.

    Returns
    -------
    Path
        Absolute path to the downloaded synthetic cohort parquet file.

    Raises
    ------
    FosterRxError
        If the engine returns an error, the job fails, or the timeout is reached.
    """
    output_dir = output_dir or Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    params = _load_params(params_path)
    stratification_config = _extract_stratification(params)

    job_id = _submit_job(
        params_path=params_path,
        n=n,
        seed=seed,
        schema_version=schema_version,
        stratification_config=stratification_config,
    )
    log.info(
        "Foster Rx engine job submitted: job_id=%s  n=%d  seed=%d", job_id, n, seed
    )

    artifact_uri = _poll_until_complete(job_id)
    out_path = _download_artifact(artifact_uri, output_dir, job_id)

    log.info("Synthetic cohort ready: %s", out_path)
    return out_path


def verify_certificate(job_id: str) -> dict:
    """
    Retrieve and verify the SYNTHETIC_DATA certificate for a completed job.

    Certificate verification uses the public endpoint — no API key required.
    Returns the full certificate bundle as a dict.
    """
    cert_id = _get_certificate_id(job_id)
    url = f"{_API_URL}/v1/certificates/{cert_id}/verify"
    resp = httpx.get(url, timeout=30)
    _raise_for_status(resp, context="certificate verification")
    return resp.json()


def check_engine_health() -> bool:
    """Return True if the Foster Rx engine is reachable and healthy."""
    try:
        resp = httpx.get(f"{_API_URL}/v1/health", timeout=10)
        return resp.status_code == 200
    except httpx.RequestError:
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_params(params_path: Path) -> dict:
    with open(params_path) as f:
        return yaml.safe_load(f)


def _extract_stratification(params: dict) -> dict:
    """
    Pull the WeatheringNet-specific stratification config from synthetic_params.yaml
    and map it to the Foster Rx WorkflowRequest stratification_config schema.
    """
    pop = params.get("population", {})
    return {
        "race_sex_strata": list(pop.get("race_sex_strata", {}).keys()),
        "age_groups": pop.get("age_groups", {}),
        "target_age_range": pop.get("target_age_range", [20, 65]),
        "biomarker_algorithm": params.get("allostatic_load", {}).get(
            "biomarker_algorithm", "Geronimus2006_NHANES_IV"
        ),
    }


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if _API_KEY:
        h["Authorization"] = f"Bearer {_API_KEY}"
    return h


def _submit_job(
    params_path: Path,
    n: int,
    seed: int,
    schema_version: str,
    stratification_config: dict,
) -> str:
    """Submit a WorkflowRequest and return the job_id."""
    payload = {
        "data_categories": ["SYNTHETIC_COHORT"],
        "intended_use": "WEATHERINGNET_SIMULATION",
        "target_record_count": n,
        "stratification_config": stratification_config,
        "generation_config": {
            "params_uri": str(params_path),
            "schema_version": schema_version,
            "seed": seed,
            "output_format": "parquet",
        },
    }
    resp = httpx.post(
        f"{_API_URL}/v1/generate",
        json=payload,
        headers=_headers(),
        timeout=30,
    )
    _raise_for_status(resp, context="job submission")
    return resp.json()["job_id"]


def _poll_until_complete(job_id: str) -> str:
    """Poll GET /v1/jobs/{job_id} until status is 'complete'. Returns artifact_uri."""
    deadline = time.time() + _TIMEOUT_S
    while time.time() < deadline:
        resp = httpx.get(
            f"{_API_URL}/v1/jobs/{job_id}",
            headers=_headers(),
            timeout=30,
        )
        _raise_for_status(resp, context="job polling")
        body = resp.json()
        status = body.get("status")

        if status == "complete":
            return body["artifact_uri"]
        if status == "failed":
            raise FosterRxError(
                f"Foster Rx engine job {job_id} failed: {body.get('error', 'unknown error')}"
            )

        log.debug("Job %s status=%s — waiting %ds", job_id, status, _POLL_INTERVAL_S)
        time.sleep(_POLL_INTERVAL_S)

    raise FosterRxError(
        f"Foster Rx engine job {job_id} did not complete within {_TIMEOUT_S}s"
    )


def _download_artifact(artifact_uri: str, output_dir: Path, job_id: str) -> Path:
    """Download the artifact parquet to output_dir and return the local path."""
    out_path = output_dir / f"cohort_{job_id}.parquet"
    with httpx.stream("GET", artifact_uri, headers=_headers(), timeout=120) as resp:
        _raise_for_status(resp, context="artifact download")
        with open(out_path, "wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)
    return out_path


def _get_certificate_id(job_id: str) -> str:
    resp = httpx.get(
        f"{_API_URL}/v1/jobs/{job_id}",
        headers=_headers(),
        timeout=30,
    )
    _raise_for_status(resp, context="certificate ID lookup")
    cert_id = resp.json().get("certificate_id")
    if not cert_id:
        raise FosterRxError(f"No certificate found for job {job_id}")
    return cert_id


def _raise_for_status(resp: httpx.Response, context: str) -> None:
    if resp.status_code >= 400:
        raise FosterRxError(
            f"Foster Rx engine error during {context}: "
            f"HTTP {resp.status_code} — {resp.text[:300]}"
        )
