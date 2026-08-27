import shutil
import pandas as pd

from pathlib import Path

def reorderData(folder, merged_csv, reordered_folder):


    merged_df = pd.read_csv(merged_csv)

    (reordered_folder / "agreed").mkdir(parents=True, exist_ok=True)
    (reordered_folder / "disagreed").mkdir(parents=True, exist_ok=True)
    (reordered_folder / "manual").mkdir(parents=True, exist_ok=True)


    buckets = dict(zip(merged_df["filename"], merged_df["bucket"]))

    for image in folder.iterdir():
        bucket = buckets.get(image.name)
        if bucket is None:
            continue
        shutil.copy2(image, reordered_folder / bucket / image.name)