# RIFT_SIMLAB_TUNED_with_analysis

Minimal environment setup and usage instructions.

## Quickstart (Windows / PowerShell)
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run analysis
Place (or generate) a sweep CSV at `simlab/paper/wm_sweep.csv` (or set env var `RIFT_SWEEP_CSV`). Then:
```powershell
python -m simlab.experiments.analyze_wm_sweep
```
Outputs (created if absent):
- `simlab/paper/figures/A_wm_effects.csv`
- `simlab/paper/figures/A_wm_acc_diff_CI.png`

## Notes
- Dependencies kept minimal: numpy + matplotlib.
- Adjust versions in `requirements.txt` if you need stricter reproducibility (pin exact versions, e.g. `numpy==1.26.4`).
