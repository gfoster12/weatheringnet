"""
Download NHANES XPT files for the ALI pipeline.

Usage:
    python scripts/download_nhanes.py --cycles 2010-2020 --output data/raw
"""

import argparse
import time
from pathlib import Path

import requests
from loguru import logger

# NHANES base URL
NHANES_BASE = "https://wwwn.cdc.gov/Nchs/Nhanes"

# Files to download per cycle (maps friendly name → NHANES file stem pattern)
NHANES_FILES = {
    "DEMO":   "Demographic Variables and Sample Weights",
    "BPX":    "Blood Pressure",
    "BMX":    "Body Measures",
    "GHB":    "Glycohemoglobin",
    "GLU":    "Plasma Fasting Glucose",
    "TCHOL":  "Total Cholesterol",
    "CBC":    "Complete Blood Count with 5-part Differential",
    "HSCRP":  "High-Sensitivity C-Reactive Protein",
}

CYCLES = {
    "2009-2010": "2009-2010",
    "2011-2012": "2011-2012",
    "2013-2014": "2013-2014",
    "2015-2016": "2015-2016",
    "2017-2018": "2017-2020",   # NHANES paused; 2017-2020 pre-pandemic combined
    "2019-2020": "2017-2020",
}


def download_file(url: str, dest: Path) -> bool:
    if dest.exists():
        logger.debug(f"Already downloaded: {dest.name}")
        return True
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        dest.write_bytes(r.content)
        logger.info(f"Downloaded: {dest.name} ({len(r.content) / 1024:.0f} KB)")
        time.sleep(0.5)   # be kind to CDC servers
        return True
    except Exception as e:
        logger.warning(f"Failed to download {url}: {e}")
        return False


def download_nhanes(output_dir: Path, cycles: list[str]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    for cycle in cycles:
        cycle_dir = output_dir / cycle
        cycle_dir.mkdir(exist_ok=True)
        logger.info(f"Downloading NHANES cycle: {cycle}")

        for stem, description in NHANES_FILES.items():
            # NHANES URL pattern: /Nchs/Nhanes/{cycle}/{STEM}_{suffix}.XPT
            # Suffix depends on cycle (B, C, D, E, F, G, H, I, J...)
            cycle_letter = _cycle_to_letter(cycle)
            filename = f"{stem}_{cycle_letter}.XPT" if cycle_letter else f"{stem}.XPT"
            url = f"{NHANES_BASE}/{CYCLES.get(cycle, cycle)}/{filename}"
            dest = cycle_dir / filename
            success = download_file(url, dest)
            if not success:
                # Try without cycle suffix
                url_alt = f"{NHANES_BASE}/{CYCLES.get(cycle, cycle)}/{stem}.XPT"
                download_file(url_alt, cycle_dir / f"{stem}.XPT")

    logger.info(f"Download complete. Files saved to {output_dir}")


def _cycle_to_letter(cycle: str) -> str:
    cycle_map = {
        "2009-2010": "F",
        "2011-2012": "G",
        "2013-2014": "H",
        "2015-2016": "I",
        "2017-2018": "J",
        "2019-2020": "L",
    }
    return cycle_map.get(cycle, "")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download NHANES data for WeatheringNet ALI pipeline")
    parser.add_argument("--cycles", nargs="+",
                        default=list(CYCLES.keys()),
                        help="NHANES cycles to download")
    parser.add_argument("--output", type=Path, default=Path("data/raw"),
                        help="Output directory")
    args = parser.parse_args()

    download_nhanes(args.output, args.cycles)
