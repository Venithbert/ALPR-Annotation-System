from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont

from plate_detector import detect_plate
from parseq_reader import read_plate


# ============================================================
# AYARLAR
# ============================================================

IMAGE_FOLDER = Path("test_images")

SCALE_FACTOR = 3
CONTRAST_FACTOR = 1.25

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Plakanın genişlik / yükseklik oranı
# Bu değerin altında kalan plakalar çift satır kabul edilir.
TWO_LINE_RATIO = 2.0


# ============================================================
# PLAKA CROP'UNU SIKIŞTIR
# ============================================================

def tighten_plate_crop(image):

    width, height = image.size

    left = int(width * 0.03)
    right = int(width * 0.97)

    top = int(height * 0.04)
    bottom = int(height * 0.94)

    return image.crop(
        (left, top, right, bottom)
    )


# ============================================================
# KONTRASTI İYİLEŞTİR
# ============================================================

def improve_contrast(image):

    enhancer = ImageEnhance.Contrast(image)

    return enhancer.enhance(CONTRAST_FACTOR)


# ============================================================
# ÇİFT SATIRI AYIR
# ============================================================

def split_two_line_plate(image):

    width, height = image.size

    middle = height // 2

    top = image.crop(
        (0, 0, width, middle)
    )

    bottom = image.crop(
        (0, middle, width, height)
    )

    return top, bottom


# ============================================================
# GÖRÜNTÜYÜ BÜYÜT
# ============================================================

def enlarge_image(image, scale):

    width, height = image.size

    new_width = width * scale
    new_height = height * scale

    return image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS
    )


# ============================================================
# DETECTION GÖRSELİNE SONUCU YAZ
# ============================================================

def write_result_on_detection(image_path, result):

    detection_path = (
        Path("outputs/detections")
        / image_path.name
    )

    if not detection_path.exists():
        return

    detection_image = Image.open(
        detection_path
    ).convert("RGB")

    draw = ImageDraw.Draw(detection_image)

    try:
        font = ImageFont.truetype(
            "arial.ttf",
            32
        )
    except:
        font = ImageFont.load_default()

    # --------------------------------------------------------
    # Mavi YOLO kutusunu bul
    # --------------------------------------------------------

    pixels = detection_image.load()

    image_width, image_height = detection_image.size

    min_x = image_width
    min_y = image_height
    max_x = 0
    max_y = 0

    for y in range(image_height):

        for x in range(image_width):

            r, g, b = pixels[x, y]

            if (
                b > 120
                and b > r * 1.3
                and b > g * 1.1
            ):
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    # --------------------------------------------------------
    # Kutuyu bulduysak sonucu üstüne yaz
    # --------------------------------------------------------

    if max_x > min_x and max_y > min_y:

        bbox = draw.textbbox(
            (0, 0),
            result,
            font=font
        )

        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = min_x

        text_y = max(
            0,
            min_y - text_height - 8
        )

        draw.rectangle(
            (
                text_x - 4,
                text_y - 4,
                text_x + text_width + 4,
                text_y + text_height + 4
            ),
            fill="blue"
        )

        draw.text(
            (
                text_x,
                text_y
            ),
            result,
            fill="white",
            font=font
        )

    detection_image.save(
        detection_path
    )


# ============================================================
# ANA İŞLEM
# ============================================================

for image_path in IMAGE_FOLDER.iterdir():

    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    print("\n------------------------------")
    print("İşlenen görüntü:", image_path.name)

    # --------------------------------------------------------
    # 1. YOLO ile plakayı bul
    # --------------------------------------------------------

    plate_result = detect_plate(
        str(image_path)
    )

    if plate_result is None:
        print("Plaka bulunamadı.")
        continue

    # plate_detector.py şu anda:
    # (plate_crop, confidence)
    # döndürüyor.

    plate = plate_result[0]

    confidence = plate_result[1]

    print(
        f"YOLO confidence: {confidence:.2f}"
    )

    # --------------------------------------------------------
    # 2. YOLO crop'unu al
    # --------------------------------------------------------

    crop_path = (
        Path("outputs/crops")
        / image_path.name
    )

    if not crop_path.exists():

        print("Crop bulunamadı.")
        continue

    image = Image.open(
        crop_path
    ).convert("RGB")

    # --------------------------------------------------------
    # 3. Crop'u temizle
    # --------------------------------------------------------

    image = tighten_plate_crop(
        image
    )

    # --------------------------------------------------------
    # 4. Kontrastı iyileştir
    # --------------------------------------------------------

    image = improve_contrast(
        image
    )

    # --------------------------------------------------------
    # 5. TEK SATIR / ÇİFT SATIR KARARI
    # --------------------------------------------------------

    width, height = image.size

    if height == 0:
        continue

    aspect_ratio = width / height

    print(
        f"Plaka oranı: {aspect_ratio:.2f}"
    )

    # ========================================================
    # ÇİFT SATIR
    # ========================================================

    if aspect_ratio < TWO_LINE_RATIO:

        print("Plaka tipi: ÇİFT SATIR")

        top, bottom = split_two_line_plate(
            image
        )

        # ----------------------------------------------------
        # Üst satırı büyüt
        # ----------------------------------------------------

        top = enlarge_image(
            top,
            SCALE_FACTOR
        )

        # ----------------------------------------------------
        # Alt satırı büyüt
        # ----------------------------------------------------

        bottom = enlarge_image(
            bottom,
            SCALE_FACTOR
        )

        # ----------------------------------------------------
        # Geçici dosyalar
        # ----------------------------------------------------

        top_path = (
            Path("outputs")
            / f"{image_path.stem}_top.jpg"
        )

        bottom_path = (
            Path("outputs")
            / f"{image_path.stem}_bottom.jpg"
        )

        top.save(top_path)
        bottom.save(bottom_path)

        # ----------------------------------------------------
        # PARSeq
        # ----------------------------------------------------

        top_result = read_plate(
            str(top_path),
            2
        )

        bottom_result = read_plate(
            str(bottom_path),
            4
        )

        # ----------------------------------------------------
        # Temizle
        # ----------------------------------------------------

        top_result = top_result.replace(
            " ",
            ""
        )

        bottom_result = bottom_result.replace(
            " ",
            ""
        )

        final_result = (
            top_result
            + bottom_result
        )

        print(
            "Üst satır:",
            top_result
        )

        print(
            "Alt satır:",
            bottom_result
        )

    # ========================================================
    # TEK SATIR
    # ========================================================

    else:

        print("Plaka tipi: TEK SATIR")

        # ----------------------------------------------------
        # Tek satırı büyüt
        # ----------------------------------------------------

        image = enlarge_image(
            image,
            SCALE_FACTOR
        )

        # ----------------------------------------------------
        # Geçici dosya
        # ----------------------------------------------------

        single_path = (
            Path("outputs")
            / f"{image_path.stem}_single.jpg"
        )

        image.save(
            single_path
        )

        # ----------------------------------------------------
        # PARSeq'e tamamını gönder
        # ----------------------------------------------------

        final_result = read_plate(
            str(single_path),
            6
        )

        final_result = final_result.replace(
            " ",
            ""
        )

        print(
            "Tek satır sonucu:",
            final_result
        )

    # ========================================================
    # SONUÇ
    # ========================================================

    print(
        "PLAKA:",
        final_result
    )

    # --------------------------------------------------------
    # Detection görseline yaz
    # --------------------------------------------------------

    write_result_on_detection(
        image_path,
        final_result
    )