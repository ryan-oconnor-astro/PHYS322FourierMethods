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
    "legend.title_fontsize": 15,
})

# Each CSV is a headerless, comma-separated file with two numeric columns.
data_dir = Path(__file__).parent

for data_path in sorted(data_dir.glob("*.csv")):
    try:
        data = np.loadtxt(data_path, delimiter=",", usecols=(0, 1))
    except (ValueError, UnicodeDecodeError):
        print(f"Skipping {data_path.name}: not a two-column numeric CSV")
        continue
    x = data[:, 0]
    y = data[:, 1]

    plt.figure(figsize=(10, 5))
    plt.plot(x, y, linewidth=1.5, color="red")
    if data_path.stem == "60HZ":
        # three highest local maxima reported by ./measure_modulation 60HZ.csv
        for peak_hz in (5890.62, 6125, 5953.12):
            plt.axvline(peak_hz, color="black", linestyle=":", linewidth=1.5)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Power Spectral Density (V^2/Hz)")
    plt.title(f"{data_path.stem} data")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # save png in a figures folder
    figures_dir = data_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    figure_path = figures_dir / f"{data_path.stem}.png"
    plt.savefig(figure_path, dpi=300)

    print(f"Loaded {len(data)} rows from {data_path.resolve()}")


def stem_to_hz(stem):
    """Parse names like '60HZ', '2500HZ', 'KHZ', '2KHZ' into a frequency in Hz."""
    name = stem.upper()
    if name.endswith("KHZ"):
        prefix = name[:-3]
        return float(prefix or 1) * 1000
    if name.endswith("HZ"):
        return float(name[:-2])
    raise ValueError(stem)


# Overlay the 125 Hz - 3 kHz spectra, colored in order of frequency
spectra = []
for data_path in data_dir.glob("*.csv"):
    try:
        freq_hz = stem_to_hz(data_path.stem)
    except ValueError:
        continue
    if not 125 <= freq_hz <= 3000:
        continue
    data = np.loadtxt(data_path, delimiter=",", usecols=(0, 1))
    spectra.append((freq_hz, data_path.stem, data))
spectra.sort(key=lambda s: s[0])

colors = ["blue", "deepskyblue", "green",
          "gold", "orange", "purple", "hotpink"]
plt.figure(figsize=(10, 5))
for color, (freq_hz, stem, data) in zip(colors, spectra):
    plt.plot(data[:, 0], data[:, 1], linewidth=1.2, color=color,
             label=f"{freq_hz:g} Hz")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power Spectral Density (V^2/Hz)")
plt.title("Spectra overlay, 125 Hz - 3 kHz")
plt.legend(title="Modulation frequency")
plt.grid(True, alpha=0.3)
plt.tight_layout()

figures_dir = data_dir / "figures"
figures_dir.mkdir(exist_ok=True)
overlay_path = figures_dir / "overlay_125HZ_3KHZ.png"
plt.savefig(overlay_path, dpi=300)
print(f"Saved overlay of {len(spectra)} spectra to {overlay_path.resolve()}")
