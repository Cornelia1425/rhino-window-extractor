"""Draws docs/facades.png from the extracted window data.

Usage (from the repo folder):
    python docs/make_figure.py building_model_5floor.3dm docs/facades.png
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import rhino3dm as rh
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import window_extractor as we

SURFACE, INK, MUTED, FILL = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6"
model = rh.File3dm.Read(sys.argv[1])
win = we.extract_windows(model)
wwr = we.wwr_table(win, we.facade_areas(model)).set_index("orientation")
walls = we._boxes(model, "wall")
x0, x1 = min(b.Min.X for b in walls), max(b.Max.X for b in walls)
y0, y1 = min(b.Min.Y for b in walls), max(b.Max.Y for b in walls)
z0, z1 = min(b.Min.Z for b in walls), max(b.Max.Z for b in walls)
floors = sorted(b.Min.Z for b in we._boxes(model, "floor"))
names = {"N": "North", "E": "East", "S": "South", "W": "West"}
fig, axes = plt.subplots(1, 4, figsize=(11, 5.2), facecolor=SURFACE,
                         gridspec_kw={"width_ratios": [x1 - x0, y1 - y0, x1 - x0, y1 - y0]})
for ax, o in zip(axes, ["N", "E", "S", "W"]):
    a0, a1 = (x0, x1) if o in "NS" else (y0, y1)
    ax.set_facecolor(SURFACE)
    ax.add_patch(Rectangle((a0, z0), a1 - a0, z1 - z0, fill=False, ec=MUTED, lw=1))
    for z in floors[1:-1]:
        ax.plot([a0, a1], [z, z], color=MUTED, lw=0.5, alpha=0.5)
    for r in win[win.orientation == o].itertuples():
        ax.add_patch(Rectangle((r.along, r.z), r.width, r.height, fc=FILL, ec=SURFACE, lw=0.8))
    ax.set_xlim(a0 - 1, a1 + 1); ax.set_ylim(z0 - 1, z1 + 1)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"{names[o]}\n{int(wwr.loc[o, 'windows'])} windows · WWR {wwr.loc[o, 'wwr_percent']:.2f}%",
                 fontsize=10.5, color=INK, pad=8)
fig.suptitle(f"Windows found on each facade of the sample model · whole building WWR {wwr.loc['Total', 'wwr_percent']:.2f}%",
             fontsize=12, color=INK, x=0.5, y=0.985)
fig.text(0.5, 0.02, "Drawn from the extracted data (window position and size), not from a Rhino screenshot.",
         ha="center", fontsize=8.5, color=MUTED)
fig.subplots_adjust(left=0.02, right=0.98, top=0.82, bottom=0.07, wspace=0.08)
fig.savefig(sys.argv[2], dpi=160, facecolor=SURFACE)
