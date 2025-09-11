"""Figure generation entry point.

This script ensures a working sweep CSV exists (synthetic fallback if missing)
then calls the WM sweep analysis to produce summary CSV + plot.

Usage (from repo root):
    python -m simlab.experiments.make_figs

Environment variables:
    RIFT_SWEEP_CSV (optional): path to an existing sweep CSV to use instead

The expected CSV header columns:
    cond,distractor,seed,acc,R,R_cluster,PAC

If no CSV is found, a synthetic one is created at:
    simlab/paper/figures/wm_sweep.csv
"""
from __future__ import annotations

import os
import csv
from pathlib import Path
import numpy as np

from . import __name__ as _pkg  # noqa: F401 (may be useful later)
from .analyze_wm_sweep import analyze, FIGDIR

SWEEP_NAME = "wm_sweep.csv"
DEFAULT_CSV = FIGDIR / SWEEP_NAME


def _have_data(csv_path: Path) -> bool:
    return csv_path.exists() and csv_path.stat().st_size > 0


def _maybe_make_synthetic(csv_path: Path) -> Path:
    if _have_data(csv_path):
        return csv_path
    rng = np.random.default_rng(42)
    distractors = [0.0, 0.1, 0.2, 0.3, 0.4]
    seeds = list(range(10))
    rows = []
    for d in distractors:
        for s in seeds:
            base_acc = 0.75 - 0.30 * d + rng.normal(0, 0.01)
            pulse_gain = 0.05 * (1 - d) + rng.normal(0, 0.005)
            pulse_acc = base_acc + pulse_gain
            # clip to [0,1]
            base_acc = float(np.clip(base_acc, 0, 1))
            pulse_acc = float(np.clip(pulse_acc, 0, 1))
            # Fake ancillary metrics
            R = float(rng.uniform(0.2, 0.9))
            R_cluster = float(R + rng.normal(0, 0.05))
            PAC = float(rng.uniform(0.0, 1.0))
            rows.append({
                "cond": "baseline",
                "distractor": d,
                "seed": s,
                "acc": base_acc,
                "R": R,
                "R_cluster": R_cluster,
                "PAC": PAC,
            })
            rows.append({
                "cond": "pulse",
                "distractor": d,
                "seed": s,
                "acc": pulse_acc,
                "R": R + rng.normal(0, 0.02),
                "R_cluster": R_cluster + rng.normal(0, 0.02),
                "PAC": float(np.clip(PAC + rng.normal(0, 0.05), 0, 1)),
            })
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["cond", "distractor", "seed", "acc", "R", "R_cluster", "PAC"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[make_figs] Created synthetic sweep data: {csv_path}")
    return csv_path


def main():
    custom = os.environ.get("RIFT_SWEEP_CSV")
    if custom:
        csv_path = Path(custom)
        if not _have_data(csv_path):
            raise FileNotFoundError(f"Env RIFT_SWEEP_CSV points to missing/empty file: {csv_path}")
    else:
        csv_path = _maybe_make_synthetic(DEFAULT_CSV)
    analyze(str(csv_path))
    print("[make_figs] Done.")


if __name__ == "__main__":  # pragma: no cover
    main()
