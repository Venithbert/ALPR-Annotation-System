import os
import shutil
import re
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
import numpy as np
import cv2

# --- KENDİ PROJENDEN İMPORT EDİLENLER ---
from plate_detector import detect_plate
from parseq_reader import read_plate

# --- ALPR AYARLARI ---
SCALE_FACTOR = 3
CONTRAST_FACTOR = 1.25
MAX_TWO_LINE_RATIO = 2.65

# --- ALPR YARDIMCI FONKSİYONLARI ---
def tighten_plate_crop(image):
    width, height = image.size
    
    # Yanlardan %5 kesiyoruz (TR logosunu ve vida deliklerini silmek için)
    left = int(width * 0.05)
    right = int(width * 0.95)
    
    # Üstten %5, Alttan ise %18 kesiyoruz! (Plakalık/Reklam yazılarını tamamen uçurmak için)
    top = int(height * 0.05)
    bottom = int(height * 0.82) 
    
    return image.crop((left, top, right, bottom))

def improve_contrast(image):
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(CONTRAST_FACTOR)

def find_horizontal_split_line(pil_image):
    gray = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    row_sums = np.sum(thresh, axis=1)
    h = len(row_sums)
    start_y, end_y = int(h * 0.25), int(h * 0.75)
    min_search_zone = row_sums[start_y:end_y]
    if len(min_search_zone) == 0:
        return h // 2, False
    is_valid_split = (np.min(min_search_zone) / (np.max(row_sums) + 1e-5)) < 0.40
    return start_y + np.argmin(min_search_zone), is_valid_split

def split_two_line_plate(image):
    width, height = image.size
    split_y, is_valid_split = find_horizontal_split_line(image)
    if not is_valid_split: return None, None
    return image.crop((0, 0, width, max(1, split_y))), image.crop((0, min(height, split_y), width, height))

def clean_plate_text(text):
    """
    Sadece harf ve rakamları tutar, KKTC plaka formatlarına göre
    optik karakter karışıklıklarını (6->G, 8->B vb.) otomatik düzeltir.
    """
    text = re.sub(r'[^A-Z0-9]', '', text.upper())
    
    num_to_char = {'0': 'O', '1': 'I', '2': 'Z', '4': 'A', '5': 'S', '6': 'G', '8': 'B'}
    
    # KURAL 1: 2 Harf + 4 Rakam (Örn: AB7266 -> AB726G)
    if len(text) == 6 and re.match(r'^[A-Z]{2}[0-9]{4}$', text):
        last_char = text[-1]
        if last_char in num_to_char:
            text = text[:-1] + num_to_char[last_char]

    # KURAL 2: 3 Harf + 4 Rakam (Örn: ZAA8196 -> ZAA819G)
    elif len(text) == 7 and re.match(r'^[A-Z]{3}[0-9]{4}$', text):
        last_char = text[-1]
        if last_char in num_to_char:
            text = text[:-1] + num_to_char[last_char]
            
    return text

def enlarge_image(image, scale):
    return image.resize((image.size[0] * scale, image.size[1] * scale), Image.Resampling.LANCZOS)

def gercek_plakayi_bul(dosya_adi):
    parcalar = dosya_adi.split('_')
    if len(parcalar) >= 3:
        return parcalar[2].replace(" ", "").upper()
    return "BULUNAMADI"

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

# --- ANA TEST MERKEZİ ---
def testi_baslat():
    girdi_klasoru = Path("gercek_veriler")
    
    # --------------------------------------------------------
    # TÜM ÇIKTI KLASÖRLERİNİ OTOMATİK TEMİZLE VE YENİDEN OLUŞTUR
    # --------------------------------------------------------
    temizlenecek_klasorler = [
        Path("outputs/gercek_sonuclar/dogru"),
        Path("outputs/gercek_sonuclar/hatali"),
        Path("outputs/crops"),
        Path("outputs/detections"),
        Path("outputs/ocr_inputs")
    ]
    
    print("Eski test sonuçları ve tüm kalıntı dosyalar otomatik temizleniyor...")
    for klasor in temizlenecek_klasorler:
        if klasor.exists():
            shutil.rmtree(klasor)
        klasor.mkdir(parents=True, exist_ok=True)
    # --------------------------------------------------------

    dogru_klasor = Path("outputs/gercek_sonuclar/dogru")
    hatali_klasor = Path("outputs/gercek_sonuclar/hatali")
    OCR_INPUTS_FOLDER = Path("outputs/ocr_inputs")

    print(f"'{girdi_klasoru}' klasöründeki veriler inceleniyor...\n")

    dogru_say = 0
    hatali_say = 0

    for image_path in girdi_klasoru.iterdir():
        if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue
            
        dosya_adi = image_path.name
        gercek_plaka = gercek_plakayi_bul(dosya_adi)
        
        # --- MODEL ÇALIŞIYOR ---
        plate_res = detect_plate(str(image_path))
        
        if plate_res is None or plate_res[0] is None:
            print(f"[HATALI - YOLODA BULUNAMADI] Dosya: {dosya_adi} | Gerçek: {gercek_plaka}")
            shutil.copy(image_path, hatali_klasor / dosya_adi)
            hatali_say += 1
            continue
            
        _, det_conf = plate_res

        try:
            image = Image.open(Path("outputs/crops") / dosya_adi).convert("RGB")
            image = tighten_plate_crop(image)
            image = improve_contrast(image)
            width, height = image.size
            if height == 0: continue

            final_ocr_conf = 0.0

            # --- YENİ MANTIK: 1. AŞAMA (ÖNCE TEK SATIR OKU) ---
            single_image = enlarge_image(image, SCALE_FACTOR)
            single_path = OCR_INPUTS_FOLDER / f"{image_path.stem}_single.jpg"
            single_image.save(single_path)
            single_result, single_conf = read_plate(str(single_path))
            tahmin_edilen = clean_plate_text(single_result)
            final_ocr_conf = single_conf

            # --- YENİ MANTIK: 2. AŞAMA (EĞER TEK SATIR KÖTÜYSE ÇİFT SATIRI DENE) ---
            if (single_conf < 0.85 or len(tahmin_edilen) < 5) and (width / height) < MAX_TWO_LINE_RATIO:
                top, bottom = split_two_line_plate(image)
                if top is not None and bottom is not None:
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
                    
                    # Üst ve alt satır anlamlı karakter sayısındaysa birleştir
                    if len(cleaned_top) >= 2 and len(cleaned_bottom) >= 2:
                        tahmin_edilen = clean_plate_text(cleaned_top + cleaned_bottom)
                        final_ocr_conf = (top_conf + bottom_conf) / 2
                        
            write_result_on_detection(image_path, tahmin_edilen, detection_conf=det_conf, ocr_conf=final_ocr_conf)
            
        except Exception as e:
             print(f"Hata oluştu {dosya_adi}: {e}")
             tahmin_edilen = "HATA"

        # --- KIYASLAMA VE KOPYALAMA ---
        if gercek_plaka == tahmin_edilen:
            shutil.copy(image_path, dogru_klasor / dosya_adi)
            print(f"[DOĞRU] Dosya: {dosya_adi} | Gerçek: {gercek_plaka} | Model: {tahmin_edilen}")
            dogru_say += 1
        else:
            shutil.copy(image_path, hatali_klasor / dosya_adi)
            print(f"[HATALI] Dosya: {dosya_adi} | Gerçek: {gercek_plaka} | Model: {tahmin_edilen}")
            hatali_say += 1

    print("\n--- TEST BİTTİ ---")
    print(f"Doğru Klasörüne Giden: {dogru_say}")
    print(f"Hatalı Klasörüne Giden: {hatali_say}")

if __name__ == "__main__":
    testi_baslat()