
# (same content as previous cell, preserved)
import os
import csv
import numpy as np
from pathlib import Path

FIGDIR = Path(__file__).resolve().parents[1] / "paper" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

def _load_rows(csv_path):
    rows = []
    with open(csv_path, "r", newline="") as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append({
                "cond": r["cond"],
                "distractor": float(r["distractor"]),
                "seed": int(r["seed"]),
                "acc": float(r["acc"]),
                "R": float(r["R"]),
                "R_cluster": float(r["R_cluster"]),
                "PAC": float(r["PAC"]),
            })
    return rows

def _bootstrap_ci(arr, n_boot=10000, alpha=0.05, rng=None):
    rng = np.random.default_rng(0) if rng is None else rng
    arr = np.array(arr, dtype=float)
    if arr.size == 0:
        return (float("nan"), float("nan"), float("nan"))
    boots = []
    n = arr.size
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boots.append(arr[idx].mean())
    boots = np.sort(np.array(boots))
    lo = boots[int((alpha/2)*len(boots))]
    hi = boots[int((1-alpha/2)*len(boots))-1]
    return float(arr.mean()), float(lo), float(hi)

def _paired_dz(diffs):
    diffs = np.array(diffs, dtype=float)
    if diffs.size < 2:
        return float("nan")
    mu = float(np.mean(diffs))
    sd = float(np.std(diffs, ddof=1))
    return mu / sd if sd > 0 else float("inf") if mu>0 else float("-inf") if mu<0 else 0.0

def _perm_pvalue_signflip(diffs, n_perm=10000, rng=None):
    rng = np.random.default_rng(1) if rng is None else rng
    diffs = np.array(diffs, dtype=float)
    if diffs.size == 0:
        return float("nan")
    obs = float(np.mean(diffs))
    if obs == 0.0:
        return 1.0
    n = diffs.size
    ge = 0
    for _ in range(n_perm):
        signs = rng.choice([-1.0, 1.0], size=n, replace=True)
        m = float(np.mean(signs * diffs))
        if abs(m) >= abs(obs):
            ge += 1
    p = (ge + 1) / (n_perm + 1)
    return p

def analyze(csv_path=None):
    csv_path = csv_path or os.environ.get("RIFT_SWEEP_CSV") or str(FIGDIR / "wm_sweep.csv")
    rows = _load_rows(csv_path)
    ds = sorted(set([r["distractor"] for r in rows]))
    out_rows = []
    for d in ds:
        seeds = sorted(set([r["seed"] for r in rows if r["distractor"] == d]))
        base = []
        pulse = []
        for s in seeds:
            rb = [r for r in rows if r["distractor"] == d and r["seed"] == s and r["cond"] == "baseline"]
            rp = [r for r in rows if r["distractor"] == d and r["seed"] == s and r["cond"] == "pulse"]
            if len(rb) == 1 and len(rp) == 1:
                base.append(rb[0]["acc"])
                pulse.append(rp[0]["acc"])
        base = np.array(base, dtype=float)
        pulse = np.array(pulse, dtype=float)
        diffs = pulse - base
        base_mean = float(base.mean()) if base.size else float("nan")
        pulse_mean = float(pulse.mean()) if pulse.size else float("nan")
        diff_mean, diff_lo, diff_hi = _bootstrap_ci(diffs)
        dz = _paired_dz(diffs)
        pval = _perm_pvalue_signflip(diffs, n_perm=10000)
        out_rows.append({
            "distractor": d,
            "n_seeds": int(len(diffs)),
            "acc_base_mean": base_mean,
            "acc_pulse_mean": pulse_mean,
            "acc_diff_mean": float(diff_mean),
            "acc_diff_lo": float(diff_lo),
            "acc_diff_hi": float(diff_hi),
            "cohen_dz": float(dz),
            "perm_p": float(pval),
        })
    out_csv = FIGDIR / "A_wm_effects.csv"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    xs = [r["distractor"] for r in out_rows]
    means = [r["acc_diff_mean"] for r in out_rows]
    lowers = [r["acc_diff_mean"] - r["acc_diff_lo"] for r in out_rows]
    uppers = [r["acc_diff_hi"] - r["acc_diff_mean"] for r in out_rows]
    errs = [[lo, up] for lo, up in zip(lowers, uppers)]
    import matplotlib.pyplot as plt
    plt.figure(figsize=(6,4))
    yerr = np.array(errs).T
    plt.errorbar(xs, means, yerr=yerr, fmt="o-")
    for r, y in zip(out_rows, means):
        plt.text(r["distractor"], y + 0.01, f"p={r['perm_p']:.3f}, d={r['cohen_dz']:.2f}", ha="center", fontsize=8)
    plt.axhline(0, linestyle="--", linewidth=1)
    plt.xlabel("Distractor probability")
    plt.ylabel("Accuracy difference (pulse - baseline)")
    plt.title("WM: Accuracy improvement with pulses (95% CI)")
    plt.tight_layout()
    plt.savefig(FIGDIR / "A_wm_acc_diff_CI.png", dpi=180)
    plt.close()
    print(f"Saved effects to: {out_csv}")
    print(f"Saved plot to: {FIGDIR / 'A_wm_acc_diff_CI.png'}")

if __name__ == "__main__":
    analyze()
