from ultralytics import YOLO
from PIL import Image

import torch
import pathlib


def load_model(model_path):
    original = pathlib.PosixPath
    pathlib.PosixPath = pathlib.WindowsPath
    try:
        return torch.hub.load("ultralytics/yolov5", "custom", path=str(model_path))
    finally:
        pathlib.PosixPath = original

def detect_plate(model, folder, crops_folder):
    """Run YOLO on every image, save the best crop in crops folder, record confidence on record dict and return it. """

    records = {}
    crops_folder.mkdir(exist_ok=True)

    for image in folder.iterdir():
        result = model(str(image))
        boxes = result.pandas().xyxy[0]

        if len(boxes) == 0:
            records[image.name] = None
            continue

        best = boxes.iloc[0]
        box = (best["xmin"], best["ymin"], best["xmax"], best["ymax"])
        Image.open(image).crop(box).save(crops_folder / image.name)
        records[image.name] = best["confidence"]
            
    return records