import random
import subprocess
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 16,
    "axes.titlesize": 20,
    "axes.labelsize": 18,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 14,
})

data_dir = Path(__file__).parent
binary = data_dir / "measure_modulation"
n_runs = 500


def stem_to_hz(stem):
    """Parse names like '60HZ', '2500HZ', 'KHZ', '2KHZ' into a frequency in Hz."""
    name = stem.upper()
    if name.endswith("KHZ"):
        prefix = name[:-3]
        return float(prefix or 1) * 1000
    if name.endswith("HZ"):
        return float(name[:-2])
    raise ValueError(stem)


def wall_time(args):
    t0 = time.perf_counter()
    subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return time.perf_counter() - t0


spectra = []
for data_path in data_dir.glob("*.csv"):
    try:
        spectra.append((stem_to_hz(data_path.stem), data_path))
    except ValueError:
        continue
spectra.sort()

# Baseline: launching the binary with no arguments (prints usage and exits),
# so the cost of process startup can be separated from the actual analysis.
jobs = [("baseline", [str(binary)])] + [
    (freq_hz, [str(binary), str(path)]) for freq_hz, path in spectra
]

# Warm up the filesystem cache, then interleave the runs in a random order so
# slow drift in machine load affects every spectrum equally.
for _, args in jobs:
    wall_time(args)
times = {key: [] for key, _ in jobs}
schedule = [job for job in jobs for _ in range(n_runs)]
random.shuffle(schedule)
for key, args in schedule:
    times[key].append(wall_time(args))

baseline_ms = np.array(times.pop("baseline")) * 1e3
freqs = np.array([f for f, _ in spectra])
runs_ms = [np.array(times[f]) * 1e3 for f in freqs]
medians = np.array([np.median(r) for r in runs_ms])
q25 = np.array([np.percentile(r, 25) for r in runs_ms])
q75 = np.array([np.percentile(r, 75) for r in runs_ms])

print(f"{'f_mod (Hz)':>10}  {'median (ms)':>11}  {'IQR (ms)':>15}")
print(f"{'baseline':>10}  {np.median(baseline_ms):11.3f}  "
      f"{np.percentile(baseline_ms, 25):6.3f} - {np.percentile(baseline_ms, 75):6.3f}")
for f, m, lo, hi in zip(freqs, medians, q25, q75):
    print(f"{f:10g}  {m:11.3f}  {lo:6.3f} - {hi:6.3f}")

plt.figure(figsize=(10, 5))
plt.axhspan(np.percentile(baseline_ms, 25), np.percentile(baseline_ms, 75),
            color="gray", alpha=0.2, linewidth=0)
plt.axhline(np.median(baseline_ms), color="gray", linestyle="--", linewidth=1.5,
            label="Process startup only (no file)")
plt.errorbar(freqs, medians, yerr=[medians - q25, q75 - medians], fmt="o",
             color="red", markersize=8, capsize=4, linewidth=1.5,
             label="measure_modulation on one spectrum")
plt.xscale("log")
plt.xticks(freqs, [f"{f:g}" for f in freqs], rotation=45)
plt.minorticks_off()
plt.xlabel("Modulation frequency (Hz)")
plt.ylabel("Wall time (ms)")
plt.title(f"measure_modulation wall time (median, IQR; {n_runs} runs each)")
plt.ylim(bottom=0)
plt.legend(loc="lower right")
plt.grid(True, alpha=0.3)
plt.tight_layout()

figures_dir = data_dir / "figures"
figures_dir.mkdir(exist_ok=True)
figure_path = figures_dir / "measure_modulation_wall_time.png"
plt.savefig(figure_path, dpi=300)
print(f"Saved {figure_path.resolve()}")
