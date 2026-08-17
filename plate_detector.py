from ultralytics import YOLO
from PIL import Image, ImageDraw


model = YOLO("license_plate_detector.pt")


def detect_plate(image_path):
    image = Image.open(image_path).convert("RGB")

    # 1. Yanlış nesneleri engellemek için conf=0.25 ve iç içe kutuları silmek için iou=0.45 ekledik
    results = model(
        image,
        conf=0.25,
        iou=0.45,
        imgsz=1280
    )
    boxes = results[0].boxes

    # Eğer 0.25 ile plaka bulunamazsa 0.15 ile tekrar dene
    if len(boxes) == 0:
        results = model(image, conf=0.15, iou=0.45, imgsz=1280)
        boxes = results[0].boxes

    if len(boxes) == 0:
        return None, None

    # --------------------------------------------------------
    # Kutulu görüntüyü oluştur ve kaydet
    # --------------------------------------------------------

    image_name = image_path.split("/")[-1].split("\\")[-1]
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

        print(
            f"Aday {i + 1}: "
            f"confidence={confidence:.2f}, "
            f"oran={aspect_ratio:.2f}, "
            f"alan={area:.0f}"
        )
        
        # Kare (çift satır) ve uzun (tek satır) plakaları kapsayacak aralık
        if 1.1 <= aspect_ratio <= 5.5:
            candidates.append(
                (i, confidence, aspect_ratio, area)
            )

    # --------------------------------------------------------
    # En uygun adayı seç
    # --------------------------------------------------------

    if candidates:
        max_area = max(c[3] for c in candidates)

        scored_candidates = []

        for i, confidence, aspect_ratio, area in candidates:
            area_ratio = area / max_area

            # Confidence yüksek olan ve alanı büyük/net olan kutuyu seç
            score = (confidence * 0.7) + (area_ratio * 0.3)

            scored_candidates.append(
                (i, confidence, aspect_ratio, area, score)
            )

        best_candidate = max(scored_candidates, key=lambda x: x[4])
        best_index = best_candidate[0]
        confidence = best_candidate[1]

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