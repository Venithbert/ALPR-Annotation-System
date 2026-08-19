import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import cv2
import csv 
from plate_detector import detect_plate
from parseq_reader import read_plate


# ============================================================
# AYARLAR
# ============================================================

IMAGE_FOLDER = Path("test_images")
OCR_INPUTS_FOLDER = Path("outputs/ocr_inputs")
OCR_INPUTS_FOLDER.mkdir(parents=True, exist_ok=True)

SCALE_FACTOR = 3
CONTRAST_FACTOR = 1.25
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}

MAX_TWO_LINE_RATIO = 2.65

# ============================================================
# CSV RAPOR DOSYASINI HAZIRLA
# ============================================================
CSV_REPORT_PATH = Path("degerlendirme_raporu.csv")

# Program her çalıştığında temiz bir rapor dosyası oluşturur başlıkları yazar
with open(CSV_REPORT_PATH, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Dosya Adi', 'Okunan Plaka', 'PARSeq Skor'])


# ============================================================
# CROP VE KONTRAST TEMİZLEME
# ============================================================

def tighten_plate_crop(image):
    width, height = image.size
    left = int(width * 0.02)
    right = int(width * 0.98)
    top = int(height * 0.05)
    bottom = int(height * 0.93)
    return image.crop((left, top, right, bottom))


def improve_contrast(image):
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(CONTRAST_FACTOR)


# ============================================================
# AKILLI ÇİFT SATIR BÖLME
# ============================================================

def find_horizontal_split_line(pil_image):
    gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    row_sums = np.sum(thresh, axis=1)
    h = len(row_sums)
    
    start_y = int(h * 0.25)
    end_y = int(h * 0.75)
    
    min_search_zone = row_sums[start_y:end_y]
    if len(min_search_zone) == 0:
        return h // 2, False

    min_val = np.min(min_search_zone)
    max_val = np.max(row_sums)
    
    is_valid_split = (min_val / (max_val + 1e-5)) < 0.40
    split_y = start_y + np.argmin(min_search_zone)
    
    return split_y, is_valid_split


def split_two_line_plate(image):
    width, height = image.size
    split_y, is_valid_split = find_horizontal_split_line(image)

    if not is_valid_split:
        return None, None

    top = image.crop((0, 0, width, max(1, split_y)))
    bottom = image.crop((0, min(height, split_y), width, height))

    return top, bottom


def clean_plate_text(text):
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def enlarge_image(image, scale):
    width, height = image.size
    return image.resize((width * scale, height * scale), Image.Resampling.LANCZOS)


# ============================================================
# DETECTION GÖRSELİNE SONUCU YAZ
# ============================================================

def write_result_on_detection(image_path, result, detection_conf=0.90, ocr_conf=0.90):
    detection_path = Path("outputs/detections") / image_path.name

    if not detection_path.exists():
        return

    detection_image = Image.open(detection_path).convert("RGB")
    draw = ImageDraw.Draw(detection_image)

    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except:
        font = ImageFont.load_default()

    label_text = f"{result} | D:{detection_conf:.2f} | S:{ocr_conf:.2f}"

    pixels = detection_image.load()
    image_width, image_height = detection_image.size

    min_x, min_y = image_width, image_height
    max_x, max_y = 0, 0

    for y in range(image_height):
        for x in range(image_width):
            r, g, b = pixels[x, y]
            if b > 120 and b > r * 1.3 and b > g * 1.1:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)

    if max_x > min_x and max_y > min_y:
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        text_x = min_x
        text_y = max(0, min_y - text_height - 8)

        draw.rectangle(
            (text_x - 4, text_y - 4, text_x + text_width + 4, text_y + text_height + 4),
            fill="blue"
        )
        draw.text((text_x, text_y), label_text, fill="white", font=font)

    detection_image.save(detection_path)


# ============================================================
# ANA İŞLEM
# ============================================================

for image_path in IMAGE_FOLDER.iterdir():

    if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
        continue

    plate_result = detect_plate(str(image_path))

    if plate_result is None or plate_result[0] is None:
        print("Plaka bulunamadı, sonraki resme geçiliyor.")
        continue

    image = Image.open(Path("outputs/crops") / image_path.name).convert("RGB")
    image = tighten_plate_crop(image)
    image = improve_contrast(image)

    width, height = image.size
    if height == 0:
        continue

    aspect_ratio = width / height

    is_two_line = False
    top, bottom = None, None

    if aspect_ratio < MAX_TWO_LINE_RATIO:
        top, bottom = split_two_line_plate(image)
        if top is not None and bottom is not None:
            is_two_line = True

    if is_two_line:
        top_img = enlarge_image(top, SCALE_FACTOR)
        bottom_img = enlarge_image(bottom, SCALE_FACTOR)

        top_path = OCR_INPUTS_FOLDER / f"{image_path.stem}_top.jpg"
        bottom_path = OCR_INPUTS_FOLDER / f"{image_path.stem}_bottom.jpg"

        top_img.save(top_path)
        bottom_img.save(bottom_path)

        top_result, top_conf = read_plate(str(top_path))
        bottom_result, bottom_conf = read_plate(str(bottom_path))

        cleaned_top = clean_plate_text(top_result)
        cleaned_bottom = clean_plate_text(bottom_result)

        # AKILLI FİLTRELEME VE TEK SATIRA DÜŞME MANTIĞI:
        # 1. Eğer üst satır 3 harften uzunsa veya alt satır gürültüyse (<=1 karakter) -> Çift satır kararı hatalıdır!
        if len(cleaned_top) > 3 or len(cleaned_bottom) <= 1:
            is_two_line = False
        else:
            final_result = cleaned_top + cleaned_bottom
            final_ocr_conf = (top_conf + bottom_conf) / 2

    if not is_two_line:
        single_image = enlarge_image(image, SCALE_FACTOR)
        single_path = OCR_INPUTS_FOLDER / f"{image_path.stem}_single.jpg"
        single_image.save(single_path)

        single_result, final_ocr_conf = read_plate(str(single_path))
        final_result = clean_plate_text(single_result)

    print(f"İşlendi: {image_path.name} -> Plaka: {final_result} (Skor: {final_ocr_conf:.2f})")

    with open(CSV_REPORT_PATH, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([image_path.name, final_result, f"{final_ocr_conf:.2f}"])

    

    write_result_on_detection(image_path, final_result, detection_conf=0.90, ocr_conf=final_ocr_conf)