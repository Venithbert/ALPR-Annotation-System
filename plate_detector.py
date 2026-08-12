from ultralytics import YOLO
from PIL import Image, ImageDraw


model = YOLO("license_plate_detector.pt")


def detect_plate(image_path):
    image = Image.open(image_path).convert("RGB")

    results = model(image)
    boxes = results[0].boxes

    if len(boxes) == 0:
        print("Plaka bulunamadı.")
        return None

    # Orijinal görüntünün kopyası
    detection_image = image.copy()
    draw = ImageDraw.Draw(detection_image)

    # Bütün detection'ları görsel üzerinde göster
    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
        confidence = box.conf[0].item()

        draw.rectangle(
            (x1, y1, x2, y2),
            outline="blue",
            width=4
        )

        draw.text(
            (x1, max(0, y1 - 20)),
            f"license_plate {confidence:.2f}",
            fill="blue"
        )

    # Kutulu görüntüyü kaydet
    image_name = image_path.split("/")[-1].split("\\")[-1]
    detection_path = f"outputs/detections/{image_name}"
    detection_image.save(detection_path)

    # YOLO'nun bulduğu bütün adayları göster
    print("Bulunan plaka adayları:")

    for i, box in enumerate(boxes):
        confidence = box.conf[0].item()
        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

        print(
            f"Aday {i + 1}: "
            f"confidence={confidence:.2f}, "
            f"koordinatlar={x1} {y1} {x2} {y2}"
        )

    # En yüksek confidence'lı plakayı seç
    best_index = boxes.conf.argmax()

    x1, y1, x2, y2 = boxes.xyxy[best_index].tolist()
    confidence = boxes.conf[best_index].item()

    x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))

    # Plakayı otomatik crop et
    plate_crop = image.crop((x1, y1, x2, y2))

    # Crop'u görüntünün adıyla kaydet
    crop_path = f"outputs/crops/{image_name}"
    plate_crop.save(crop_path)

    print("Plaka bulundu.")
    print(f"Seçilen plaka confidence: {confidence:.2f}")
    print("Koordinatlar:", x1, y1, x2, y2)
    print("Kutulu görüntü:", detection_path)
    print("Crop:", crop_path)

    return plate_crop