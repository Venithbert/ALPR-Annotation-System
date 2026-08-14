from pathlib import Path
from PIL import Image, ImageEnhance

from plate_detector import detect_plate
from parseq_reader import read_plate


# ============================================================
# AYARLAR
# ============================================================

TEST_FOLDER = Path("double_line_tests")
OUTPUT_FOLDER = Path("outputs/double_line_tests")

OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# PARSeq'e vermeden önce crop'u kaç kat büyüteceğiz?
SCALE_FACTOR = 3

# Kontrast artırma miktarı
CONTRAST_FACTOR = 1.25


# ============================================================
# TEST GÖRSELLERİNİ BUL
# ============================================================

test_images = sorted(
    [
        p for p in TEST_FOLDER.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]
)

print("Kullanılan cihaz: cuda")
print("Toplam test görüntüsü:", len(test_images))
print()

found_count = 0


# ============================================================
# PLAKA CROP'UNU SIKIŞTIR
# ============================================================

def tighten_plate_crop(image):

    width, height = image.size

    # Kenarlardaki gereksiz bölgeleri çok az temizle
    left = int(width * 0.03)
    right = int(width * 0.97)

    # Üstten ve alttan küçük miktarda boşluk kaldır
    top = int(height * 0.04)
    bottom = int(height * 0.94)

    return image.crop(
        (left, top, right, bottom)
    )


# ============================================================
# KONTRASTI ARTIR
# ============================================================

def improve_contrast(image):

    enhancer = ImageEnhance.Contrast(image)

    return enhancer.enhance(CONTRAST_FACTOR)


# ============================================================
# ÇİFT SATIRI AYIR
# ============================================================

def split_two_line_plate(image):

    width, height = image.size

    # Şimdilik ortadan bölüyoruz.
    middle = height // 2

    top = image.crop(
        (0, 0, width, middle)
    )

    bottom = image.crop(
        (0, middle, width, height)
    )

    return top, bottom


# ============================================================
# CROP'U BÜYÜT
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
# ANA TEST
# ============================================================

for image_path in test_images:

    image_name = image_path.name

    # --------------------------------------------------------
    # 1. YOLO ile plakayı bul
    # --------------------------------------------------------

    plate, confidence = detect_plate(str(image_path))

    if plate is None:
        print(f"{image_path.stem} → PLAKA BULUNAMADI")
        continue

    found_count += 1

    # --------------------------------------------------------
    # 2. YOLO crop dosyasını bul
    # --------------------------------------------------------

    crop_path = Path("outputs/crops") / image_name

    if not crop_path.exists():
        print(f"{image_path.stem} → CROP BULUNAMADI")
        continue

    image = Image.open(crop_path).convert("RGB")

    # --------------------------------------------------------
    # 3. Gereksiz kenarları temizle
    # --------------------------------------------------------

    image = tighten_plate_crop(image)

    # --------------------------------------------------------
    # 4. Kontrastı hafif artır
    # --------------------------------------------------------

    image = improve_contrast(image)

    # --------------------------------------------------------
    # 5. Üst ve alt satırı ayır
    # --------------------------------------------------------

    top, bottom = split_two_line_plate(image)

    # --------------------------------------------------------
    # 6. Crop'ları 3× büyüt
    # --------------------------------------------------------

    top = enlarge_image(top, SCALE_FACTOR)
    bottom = enlarge_image(bottom, SCALE_FACTOR)

    # --------------------------------------------------------
    # 7. Büyütülmüş crop'ları kaydet
    # --------------------------------------------------------

    stem = image_path.stem

    top_path = OUTPUT_FOLDER / f"{stem}_top.jpg"
    bottom_path = OUTPUT_FOLDER / f"{stem}_bottom.jpg"

    top.save(top_path)
    bottom.save(bottom_path)

    # --------------------------------------------------------
    # 8. PARSeq ile oku
    # --------------------------------------------------------

    top_result = read_plate(str(top_path))
    bottom_result = read_plate(str(bottom_path))

    # --------------------------------------------------------
    # 9. Sonuçları temizle
    # --------------------------------------------------------

    top_result = top_result.replace(" ", "")
    bottom_result = bottom_result.replace(" ", "")

    final_result = top_result + bottom_result

    # --------------------------------------------------------
    # 10. Sonucu göster
    # --------------------------------------------------------

    print(
        f"{image_path.stem} → {final_result}"
        f" | YOLO confidence: {confidence:.2f}"
    )


# ============================================================
# ÖZET
# ============================================================

not_found_count = len(test_images) - found_count

print()
print("--------------------------------")
print(f"Plaka bulunan: {found_count}/{len(test_images)}")
print(f"Plaka bulunamayan: {not_found_count}/{len(test_images)}")
print("--------------------------------")