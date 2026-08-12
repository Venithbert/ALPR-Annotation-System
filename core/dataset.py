from pathlib import Path


#get path and possible image 
folder_path = Path("C:/data")    
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def scan_folder():
    registeryArray = []

    for image in folder_path.iterdir():

        #check if it's supported format
        if image.suffix.lower() not in image_extensions:
            continue
        
        registeryArray.append(image.name)
    
    registeryArray.sort()
  
    with open("results.csv", "w") as file:
        for member in registeryArray:
            file.write(f"{member}\n")
