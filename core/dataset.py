import re

from pathlib import Path

#get path and possible image 
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def scan_folder(folder_path):
    registeryArray = []

    for image in folder_path.iterdir():

        #check if it's supported format
        if image.suffix.lower() not in image_extensions:
            continue

        registeryArray.append(image.name)
    
    registeryArray.sort()

    records = {}  #putting everyhing in a dict key=file name  value=plate name 
    for name in registeryArray: 
        records[name] = parse_filename(name)

    return records


def parse_filename(name):
    regex_pattern = r"_([^_]+)_{4}(?!_)"
    match = re.search(regex_pattern, name)

    if match:
        return match.group(1)
    else:
        return ""               


