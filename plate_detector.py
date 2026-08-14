from ultralytics import YOLO
from PIL import Image, ImageDraw


model = YOLO("license_plate_detector.pt")


def detect_plate(image_path):
    image = Image.open(image_path).convert("RGB")

    results = model(
        image,
        conf=0.10,
        imgsz=1280
    )
    boxes = results[0].boxes

    if len(boxes) == 0:
        print("0.10 confidence ile plaka bulunamadı.")
        print("Düşük confidence ile tekrar deneniyor...")

        results = model(image, conf=0.05)
        boxes = results[0].boxes

    if len(boxes) == 0:
        return None, None

    # --------------------------------------------------------
    # Kutulu görüntüyü oluştur ve kaydet
    # --------------------------------------------------------

    detection_image = image.copy()
    draw = ImageDraw.Draw(detection_image)

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

    image_name = image_path.split("/")[-1].split("\\")[-1]

    detection_path = f"outputs/detections/{image_name}"
    detection_image.save(detection_path)

    # --------------------------------------------------------
    # Plaka adaylarını değerlendir
    # --------------------------------------------------------

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
        if 2.0 <= aspect_ratio <= 5.0:
            candidates.append(
                (i, confidence, aspect_ratio, area)
            )

    # --------------------------------------------------------
    # En uygun adayı seç
    # --------------------------------------------------------

    if candidates:

        max_area = max(
            candidate[3]
            for candidate in candidates
        )

        scored_candidates = []

        for i, confidence, aspect_ratio, area in candidates:

            area_ratio = area / max_area

            score = (
                confidence * 0.6
                + (1 - area_ratio) * 0.4
            )

            scored_candidates.append(
                (i, confidence, aspect_ratio, area, score)
            )

        best_index, confidence, aspect_ratio, area, score = max(
            scored_candidates,
            key=lambda x: x[4]
        )

    else:

        best_index = boxes.conf.argmax().item()
        confidence = boxes.conf[best_index].item()

    # --------------------------------------------------------
    # Plaka crop
    # --------------------------------------------------------

    x1, y1, x2, y2 = boxes.xyxy[best_index].tolist()

    x1, y1, x2, y2 = map(
        int,
        (x1, y1, x2, y2)
    )

    plate_crop = image.crop(
        (x1, y1, x2, y2)
    )

    crop_path = f"outputs/crops/{image_name}"
    plate_crop.save(crop_path)

    return plate_crop, confidence