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
    return re.sub(r'[^A-Z0-9]', '', text.upper())

# --- DOSYA İSMİNDEN GERÇEK PLAKAYI ÇIKARMA ---
def gercek_plakayi_cikart(dosya_adi):
    # Arkadaşının dosya ismi formatına göre (Örn: T7_032940_20-11408___Unknown.jpg)
    # Genelde aradaki tireli veya alt tireli kısımlar gerçek plakayı verir.
    # Senin ekran görüntündeki örneklere göre ayarlıyoruz:
    parcalar = dosya_adi.split('_')
    for parca in parcalar:
        # Eğer parçanın içinde plaka formatı varsa (örneğin rakam-tire içeriyorsa)
        if '-' in parca and len(parca) >= 3:
            return clean_plate_text(parca)
    
    # Eğer yukarıdaki format uymuyorsa standart 3. parçaya bakalım (eski sistemimiz gibi)
    if len(parcalar) >= 3:
        return clean_plate_text(parcalar[2])
        
    return "BILINMIYOR"

def crop_testini_baslat():
    if not INPUT_FOLDER.exists():
        print(f"Hata: '{INPUT_FOLDER}' klasörü bulunamadı!")
        return

    if OUTPUT_FOLDER.exists():
        shutil.rmtree(OUTPUT_FOLDER)
    OK_FOLDER.mkdir(parents=True, exist_ok=True)
    ERROR_FOLDER.mkdir(parents=True, exist_ok=True)

    print(f"'{INPUT_FOLDER}' klasöründeki crop resimler PARSeq ile okunup dosya adlarıyla karşılaştırılıyor...\n")

    ok_sayisi = 0
    error_sayisi = 0

    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'plate', 'confidence', 'status'])

        for img_path in INPUT_FOLDER.iterdir():
            if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                continue

            dosya_adi = img_path.name
            gercek_plaka = gercek_plakayi_cikart(dosya_adi)
            tahmin_edilen = ""
            final_conf = 0.0
            status = "error"

            try:
                # Plakayı oku
                ham_sonuc, final_conf = read_plate(str(img_path))
                tahmin_edilen = clean_plate_text(ham_sonuc)
                
                # --- KARŞILAŞTIRMA MANTIĞI ---
                # Modelin okuduğu ile dosya adındaki gerçek plaka BİREBİR TUTUYOR MU?
                if tahmin_edilen != "" and tahmin_edilen == gercek_plaka:
                    status = "ok"
                else:
                    status = "error"
                    
            except Exception as e:
                print(f"Okuma hatası ({dosya_adi}): {e}")
                status = "error"

            # CSV'ye yaz
            writer.writerow([dosya_adi, tahmin_edilen, f"{final_conf:.2f}", status])

            # Klasörlere ayır
            if status == "ok":
                shutil.copy(img_path, OK_FOLDER / dosya_adi)
                ok_sayisi += 1
                print(f"[OK] {dosya_adi} -> Gerçek: {gercek_plaka} | Okunan: {tahmin_edilen}")
            else:
                shutil.copy(img_path, ERROR_FOLDER / dosya_adi)
                error_sayisi += 1
                print(f"[ERROR] {dosya_adi} -> Gerçek: {gercek_plaka} | Okunan: {tahmin_edilen}")

    print("\n--- CROP KARŞILAŞTIRMA TESTİ BİTTİ ---")
    print(f"OK (Doğru Eşleşen): {ok_sayisi}")
    print(f"ERROR (Yanlış/Uyuşmayan): {error_sayisi}")
    print(f"CSV Raporu '{CSV_FILE}' adıyla kaydedildi!")

if __name__ == "__main__":
    crop_testini_baslat()