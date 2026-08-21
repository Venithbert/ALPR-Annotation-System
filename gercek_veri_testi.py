import os
import shutil
import re
from pathlib import Path
from PIL import Image, ImageEnhance
import numpy as np
import cv2

# --- KENDİ PROJENDEN İMPORT EDİLENLER ---
from plate_detector import detect_plate
from parseq_reader import read_plate

# --- ALPR AYARLARI ---
SCALE_FACTOR = 3
CONTRAST_FACTOR = 1.25
MAX_TWO_LINE_RATIO = 2.65
OCR_INPUTS_FOLDER = Path("outputs/ocr_inputs")
OCR_INPUTS_FOLDER.mkdir(parents=True, exist_ok=True)

# --- ALPR YARDIMCI FONKSİYONLARI ---
def tighten_plate_crop(image):
    width, height = image.size
    return image.crop((int(width * 0.02), int(height * 0.05), int(width * 0.98), int(height * 0.93)))

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
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def enlarge_image(image, scale):
    return image.resize((image.size[0] * scale, image.size[1] * scale), Image.Resampling.LANCZOS)

# --- DOSYA İSMİNDEN GERÇEK PLAKAYI ÇIKARMA ---
def gercek_plakayi_bul(dosya_adi):
    parcalar = dosya_adi.split('_')
    if len(parcalar) >= 3:
        return parcalar[2].replace(" ", "").upper()
    return "BULUNAMADI"

# --- ANA TEST MERKEZİ ---
def testi_baslat():
    girdi_klasoru = Path("gercek_veriler")
    dogru_klasor = Path("outputs/gercek_sonuclar/dogru")
    hatali_klasor = Path("outputs/gercek_sonuclar/hatali")

    print("Eski test sonuçları otomatik temizleniyor...")
    if dogru_klasor.exists(): shutil.rmtree(dogru_klasor)
    if hatali_klasor.exists(): shutil.rmtree(hatali_klasor)

    dogru_klasor.mkdir(parents=True, exist_ok=True)
    hatali_klasor.mkdir(parents=True, exist_ok=True)

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

        try:
            image = Image.open(Path("outputs/crops") / dosya_adi).convert("RGB")
            image = tighten_plate_crop(image)
            image = improve_contrast(image)
            width, height = image.size
            if height == 0: continue

            # --- YENİ MANTIK: 1. AŞAMA (ÖNCE TEK SATIR OKU) ---
            single_image = enlarge_image(image, SCALE_FACTOR)
            single_path = OCR_INPUTS_FOLDER / f"{image_path.stem}_single.jpg"
            single_image.save(single_path)
            single_result, single_conf = read_plate(str(single_path))
            tahmin_edilen = clean_plate_text(single_result)

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
                    
                    # Üst ve alt satır anlamlı karakter sayısındaysa (hayalet karakterleri yoksay) birleştir
                    if len(cleaned_top) >= 2 and len(cleaned_bottom) >= 2:
                        tahmin_edilen = cleaned_top + cleaned_bottom
                        
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