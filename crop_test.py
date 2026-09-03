import os
import shutil
import csv
import re
from pathlib import Path

# --- KENDİ PROJENDEN İMPORT EDİLENLER ---
from parseq_reader import read_plate

# --- KLASÖR VE DOSYA AYARLARI ---
INPUT_FOLDER = Path("girdi_croplar")
OUTPUT_FOLDER = Path("crop_ciktilar")
OK_FOLDER = OUTPUT_FOLDER / "ok"
ERROR_FOLDER = OUTPUT_FOLDER / "error"
CSV_FILE = "crop_sonuclar.csv"

def clean_plate_text(text):
    # Metinden sadece harf ve rakamları bırakır
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def crop_testini_baslat():
    if not INPUT_FOLDER.exists():
        print(f"Hata: '{INPUT_FOLDER}' klasörü bulunamadı!")
        return

    # Çıktı klasörlerini temizle ve oluştur
    if OUTPUT_FOLDER.exists():
        shutil.rmtree(OUTPUT_FOLDER)
    OK_FOLDER.mkdir(parents=True, exist_ok=True)
    ERROR_FOLDER.mkdir(parents=True, exist_ok=True)

    print(f"'{INPUT_FOLDER}' klasöründeki crop resimler PARSeq ile okunuyor...\n")

    ok_sayisi = 0
    error_sayisi = 0

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'plate', 'confidence', 'status'])

        for img_path in INPUT_FOLDER.iterdir():
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            dosya_adi = img_path.name
            tahmin_edilen = ""
            final_conf = 0.0
            status = "error"

            try:
                
                ham_sonuc, final_conf = read_plate(str(img_path))
                tahmin_edilen = clean_plate_text(ham_sonuc)
                
                
                if len(tahmin_edilen) > 0 and final_conf > 0.0:
                    status = "ok"
                else:
                    
                    tahmin_edilen = ""
                    final_conf = 0.0
                    status = "error"
                    
            except Exception as e:
                print(f"Okuma hatası ({dosya_adi}): {e}")
                tahmin_edilen = ""
                final_conf = 0.0
                status = "error"

            
            conf_str = f"{final_conf:.2f}" if status == "ok" else "0.0"
            writer.writerow([dosya_adi, tahmin_edilen, conf_str, status])

            
            if status == "ok":
                shutil.copy(img_path, OK_FOLDER / dosya_adi)
                ok_sayisi += 1
                print(f"[OK] {dosya_adi} -> Okunan: '{tahmin_edilen}' (Skor: {conf_str})")
            else:
                shutil.copy(img_path, ERROR_FOLDER / dosya_adi)
                error_sayisi += 1
                print(f"[ERROR - BOŞ] {dosya_adi} -> Plaka okunamadı!")

    print("\n--- CROP TESTİ BİTTİ ---")
    print(f"OK (Okunabilen Resim Sayısı): {ok_sayisi}")
    print(f"ERROR (Hiç Okunamayan / Boş Kalan): {error_sayisi}")
    print(f"CSV Raporu '{CSV_FILE}' adıyla kaydedildi!")

if __name__ == "__main__":
    crop_testini_baslat()