import re

from pathlib import Path

#get path and possible image 
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def scan_folder(folder_path):
    """Find images in folder_path and parse each filename with parse_filename(name).
    Returns records aka {key=file name: value=plate name}.
    """

    registeryArray = []

    for image in folder_path.iterdir():

        #check if it's supported format
        if image.suffix.lower() not in image_extensions:
            continue

        registeryArray.append(image.name)
    
    registeryArray.sort()

    records = {}   
    for name in registeryArray: 
        records[name] = parse_filename(name)

    return records


def parse_filename(name): 
    """Extract the ALPR reading from a filename.
    "T7_063400_11-1111____Unknown.jpg" -> "11-1111"
     """
    
    regex_pattern = r"_([^_]+)_{4}(?!_)"
    match = re.search(regex_pattern, name)

    if match:
        return match.group(1)
    else:
        return ""               


