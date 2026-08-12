#3.gün oluşturdum bu dosyayı

from pathlib import Path

from plate_detector import detect_plate
from parseq_reader import read_plate


image_folder = Path("test_images")

image_extensions = {".jpg", ".jpeg", ".png"}

for image_path in image_folder.iterdir():

    # Sadece görüntü dosyalarını al
    if image_path.suffix.lower() not in image_extensions:
        continue

    # YOLO'nun daha önce oluşturduğu crop'u tekrar giriş olarak alma
    if image_path.name == "auto_plate_crop.jpg":
        continue

    print("\n------------------------------")
    print("İşlenen görüntü:", image_path.name)

    plate = detect_plate(str(image_path))

    if plate is not None:
        crop_path = Path("outputs/crops") / image_path.name
        result = read_plate(str(crop_path))
        print("PARSeq sonucu:", result)