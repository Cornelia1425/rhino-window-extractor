"""Rhino window extractor.

Reads a Rhino .3dm building model and writes:
  - windows.csv              one row per window (name, floor, orientation, size, area)
  - wwr_by_orientation.csv   window-to-wall ratio for each facade (N, E, S, W) and in total

Same method as the 2020 notebook (rhino3d_windows_information.ipynb), packaged as a
command-line script, plus the window-to-wall ratio.

Usage:
    python window_extractor.py building_model_5floor.3dm --out output

Assumptions (same as the notebook):
  - windows, walls and floor slabs are objects named "window", "wall" and "floor"
  - the building is a rectangle aligned with the X/Y axes, with +Y as north
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import rhino3dm as rh

ORIENTATIONS = ["N", "E", "S", "W"]


def _boxes(model, name):
    """Bounding boxes of every object with the given name."""
    return [obj.Geometry.GetBoundingBox() for obj in model.Objects if obj.Attributes.Name == name]


def extract_windows(model):
    """One row per window: size, position, orientation, floor and name."""
    rows = []
    for bbox in _boxes(model, "window"):
        d = bbox.Diagonal
        # the thin horizontal dimension is the depth; the other one is the width
        if d.X < d.Y:
            width, depth, group = d.Y, d.X, "WE"
        else:
            width, depth, group = d.X, d.Y, "NS"
        rows.append(dict(width=width, height=d.Z, depth=depth, orientation_group=group,
                         x=bbox.Min.X, y=bbox.Min.Y, z=bbox.Min.Z))
    if not rows:
        raise SystemExit('No objects named "window" found in the model.')
    df = pd.DataFrame(rows)
    df["area"] = df.width * df.height

    # N vs S (and E vs W): compare each window with the middle of its group
    y_mean = np.mean(list(set(df[df.orientation_group == "NS"].y)))
    x_mean = np.mean(list(set(df[df.orientation_group == "WE"].x)))

    def find_orientation(row):
        if row.orientation_group == "NS":
            return "N" if row.y > y_mean else "S"
        return "E" if row.x > x_mean else "W"

    df["orientation"] = df.apply(find_orientation, axis=1)

    # floor: which pair of slabs the window sits between
    floor_z = sorted(b.Min.Z for b in _boxes(model, "floor"))
    if len(floor_z) < 2:
        raise SystemExit('Need at least two objects named "floor" to work out floors.')

    def map_z_to_floor(row):
        for f in range(len(floor_z) - 1):
            if floor_z[f] < row.z < floor_z[f + 1]:
                return f
        raise SystemExit(f"A window at z={row.z:.2f} is not between two floor slabs.")

    df["floor"] = df.apply(map_z_to_floor, axis=1)

    # name: F<floor><orientation><number on that floor>, for example F1N15.
    # Within a facade, windows are numbered by position (along the facade, then upward),
    # so the same model always gives the same names.
    df["along"] = np.where(df.orientation_group == "NS", df.x, df.y)
    df = df.sort_values(["floor", "orientation", "along", "z"], kind="stable").reset_index(drop=True)
    df["idx"] = df.groupby("floor").cumcount() + 1
    df["name"] = "F" + df.floor.astype(str) + df.orientation + df.idx.astype(str)
    df["index"] = df.index + 1
    return df


def facade_areas(model):
    """Gross wall area of each facade: overall facade width x total wall height."""
    walls = _boxes(model, "wall")
    if not walls:
        raise SystemExit('No objects named "wall" found in the model.')
    width_x = max(b.Max.X for b in walls) - min(b.Min.X for b in walls)
    width_y = max(b.Max.Y for b in walls) - min(b.Min.Y for b in walls)
    height = max(b.Max.Z for b in walls) - min(b.Min.Z for b in walls)
    return {"N": width_x * height, "S": width_x * height,
            "E": width_y * height, "W": width_y * height}


def wwr_table(windows, wall_area):
    """Window-to-wall ratio per orientation, plus a Total row."""
    rows = []
    for o in ORIENTATIONS:
        w = windows[windows.orientation == o]
        rows.append(dict(orientation=o, windows=len(w), window_area=w.area.sum(),
                         wall_area=wall_area[o]))
    t = pd.DataFrame(rows)
    total = dict(orientation="Total", windows=t.windows.sum(),
                 window_area=t.window_area.sum(), wall_area=t.wall_area.sum())
    t = pd.concat([t, pd.DataFrame([total])], ignore_index=True)
    t["wwr_percent"] = 100 * t.window_area / t.wall_area
    return t.round(2)


def main():
    p = argparse.ArgumentParser(description="Extract window data and window-to-wall ratio from a Rhino .3dm model.")
    p.add_argument("model", help="path to the .3dm file")
    p.add_argument("--out", default="output", help="folder for the CSV files (default: output)")
    args = p.parse_args()

    model = rh.File3dm.Read(args.model)
    if model is None:
        raise SystemExit(f"Could not read {args.model}")

    windows = extract_windows(model)
    wwr = wwr_table(windows, facade_areas(model))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cols = ["index", "name", "floor", "orientation", "width", "height", "depth", "area"]
    windows[cols].round(2).to_csv(out / "windows.csv", index=False)
    wwr.to_csv(out / "wwr_by_orientation.csv", index=False)

    print(f"{len(windows)} windows -> {out / 'windows.csv'}")
    print(wwr.to_string(index=False))
    print(f"Units are the model's units ({model.Settings.ModelUnitSystem}).")


if __name__ == "__main__":
    main()
