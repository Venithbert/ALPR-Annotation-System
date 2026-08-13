from ultralytics import YOLO
from PIL import Image, ImageDraw


model = YOLO("license_plate_detector.pt")


def detect_plate(image_path):
    image = Image.open(image_path).convert("RGB")

    results = model(image, conf=0.15)
    boxes = results[0].boxes

    if len(boxes) == 0:
        print("0.15 confidence ile plaka bulunamadı.")
        print("Düşük confidence ile tekrar deneniyor...")

        results = model(image, conf=0.05)
        boxes = results[0].boxes

    if len(boxes) == 0:
        print("0.05 confidence ile de plaka bulunamadı.")
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

    # Plaka adayları arasından uygun oranlı olanı seç
    candidates = []

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        confidence = box.conf[0].item()

        width = x2 - x1
        height = y2 - y1

        if height <= 0:
            continue

        aspect_ratio = width / height
        area = width * height

        # Çok dar veya aşırı geniş kutuları ele
        if 1.2 <= aspect_ratio <= 5.0:
            candidates.append((i, confidence, aspect_ratio, area))

    if candidates:
       # en büyük adayın alanını bul
       max_area = max(
           candidate[3]
           for candidate in candidates
       )

       scored_candidates = []

       for i, confidence, aspect_ratio, area in candidates:

           # büyük gereksiz kutulara küçük bir ceza 
           area_ratio = area / max_area

           score = (
               confidence * 0.7
                 + (1 - area_ratio) * 0.3
           )

           scored_candidates.append(
               (i, confidence, aspect_ratio, area, score)
           )


       # Uygun oranlı adaylar içinde confidence en yüksek olanı seç
       best_index, confidence, aspect_ratio, area, score = max(
           scored_candidates,
           key=lambda x: x[4]
        )

       print(
           f"Seçim skoru: {score:.3f}, "
           f"aspect ratio: {aspect_ratio:.2f},"
           f"alan: {area:.0f}"
       )
       
    else:
        # Hiçbiri uygun değilse eski yönteme dön
        best_index = boxes.conf.argmax().item()
        confidence = boxes.conf[best_index].item()
        aspect_ratio = None

    x1, y1, x2, y2 = boxes.xyxy[best_index].tolist()

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