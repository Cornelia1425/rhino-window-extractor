# Rhino Window Extractor (2020)

A Python notebook that reads a Rhino `.3dm` building model and turns every window into a row in a spreadsheet. I wrote it in May 2020 for a window take-off task with View Inc.

## What it does

1. Opens the model with `rhino3dm` and finds every object named `window`.
2. Reads each window's bounding box to get width, height, depth and area.
3. Works out which way each window faces (N, S, E or W) from its position relative to the building's center.
4. Finds each window's floor by comparing its height with the floor slabs (objects named `floor`).
5. Names each window by floor, direction and number, for example `F1N15`.
6. Exports the table to `windows_information.csv`.

On the sample 5-floor model it extracts 95 windows.

## Files

- `rhino3d_windows_information.ipynb`: the notebook, with the method written out step by step
- `building_model_5floor.3dm`: the sample 5-floor model
- `windows_information.csv`: the output

## Run it

```bash
pip install rhino3dm pandas numpy jupyter
jupyter notebook rhino3d_windows_information.ipynb
```

The notebook expects the model file to be named `Building_model_5floor.3dm`. On a case-sensitive system, rename the file or edit that line.
