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
  
    return registeryArray
