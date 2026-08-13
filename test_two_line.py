from pathlib import Path
from PIL import Image

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


# ============================================================
# TEST GÖRSELLERİNİ BUL
# ============================================================

test_images = sorted(
    [
        p for p in TEST_FOLDER.iterdir()
        if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]
)

print("Toplam test görüntüsü:", len(test_images))

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
    bottom = int(height * 0.88)

    return image.crop(
        (left, top, right, bottom)
    )

# ============================================================
# ÇİFT SATIRI AYIR
# ============================================================

def split_two_line_plate(image):

    width, height = image.size

    # Şimdilik aynı şekilde ortadan bölüyoruz.
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

    print("\n------------------------------")
    print("Test edilen görüntü:", image_name)

    # --------------------------------------------------------
    # 1. YOLO ile plakayı bul
    # --------------------------------------------------------

    plate = detect_plate(str(image_path))

    if plate is None:
        print("YOLO plakayı bulamadı.")
        continue

    # YOLO crop
    crop_path = Path("outputs/crops") / image_name

    if not crop_path.exists():
        print("YOLO crop dosyası bulunamadı:", crop_path)
        continue

    image = Image.open(crop_path).convert("RGB")

    print("YOLO crop boyutu:", image.size)

    image = tighten_plate_crop(image)

    print("Daraltılmış crop boyutu:", image.size)

    # --------------------------------------------------------
    # 2. Üst ve alt satırı ayır
    # --------------------------------------------------------

    top, bottom = split_two_line_plate(image)

    print("Normal üst crop boyutu:", top.size)
    print("Normal alt crop boyutu:", bottom.size)

    # --------------------------------------------------------
    # 3. Crop'ları 3× büyüt
    # --------------------------------------------------------

    top = enlarge_image(top, SCALE_FACTOR)
    bottom = enlarge_image(bottom, SCALE_FACTOR)

    print("Büyütülmüş üst crop boyutu:", top.size)
    print("Büyütülmüş alt crop boyutu:", bottom.size)

    # --------------------------------------------------------
    # 4. Büyütülmüş crop'ları kaydet
    # --------------------------------------------------------

    stem = image_path.stem

    top_path = OUTPUT_FOLDER / f"{stem}_top.jpg"
    bottom_path = OUTPUT_FOLDER / f"{stem}_bottom.jpg"

    top.save(top_path)
    bottom.save(bottom_path)

    print("Üst crop:", top_path)
    print("Alt crop:", bottom_path)

    # --------------------------------------------------------
    # 5. Üst satırı PARSeq ile oku
    # --------------------------------------------------------

    print("Üst satır okunuyor...")

    top_result = read_plate(str(top_path))

    # --------------------------------------------------------
    # 6. Alt satırı PARSeq ile oku
    # --------------------------------------------------------

    print("Alt satır okunuyor...")

    bottom_result = read_plate(str(bottom_path))

    # --------------------------------------------------------
    # 7. Sonuçları temizle
    # --------------------------------------------------------

    top_result = top_result.replace(" ", "")
    bottom_result = bottom_result.replace(" ", "")

    final_result = top_result + bottom_result

    # --------------------------------------------------------
    # 8. Sonuçları göster
    # --------------------------------------------------------

    print()
    print("Üst satır:", top_result)
    print("Alt satır:", bottom_result)
    print("BİRLEŞTİRİLMİŞ:", final_result)