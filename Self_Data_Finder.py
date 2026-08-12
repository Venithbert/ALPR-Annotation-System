import os
import cv2
import torch
import numpy as np
import yaml
import random
from pathlib import Path

# Models klasöründeki tüm .pt dosyalarını tara
models_dir = Path('Models')
pt_files = list(models_dir.glob('*.pt'))

if not pt_files:
    raise FileNotFoundError("Models/ klasöründe hiç .pt dosyası bulunamadı!")

# Son değiştirilme tarihine göre en yeni olan dosyayı seç
latest_model = max(pt_files, key=lambda f: f.stat().st_mtime)
print(f"Yüklenen model: {str(latest_model)}")

# Modeli yükle
model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(latest_model))
Data_path = 'training_bin/'

# Otomatik veri seti dizinlerini oluştur
os.makedirs('auto_dataset/images/train', exist_ok=True)
os.makedirs('auto_dataset/labels/train', exist_ok=True)
os.makedirs('auto_dataset/images/val', exist_ok=True)
os.makedirs('auto_dataset/labels/val', exist_ok=True)

CONF_THRESHOLD = 0.5  # Sadece %80 ve üzeri emin olunan tespitler
CROP_SIZE = 800        # Kırpılacak hedef boyut (800x800)
HALF_SIZE = CROP_SIZE // 2
Train_Val_Split = 0.8  # %80 eğitim, %20 doğrulama

total_saved_count = 0

def process_frames(frame, prefix, frame_idx, crop_idx):
    if frame is None:
        return crop_idx

    h, w, _ = frame.shape

    # Görsel boyutu 800x800'den küçükse kırpma yapmadan atla veya boyutlandır
    if h < CROP_SIZE or w < CROP_SIZE:
        frame = cv2.resize(frame, (max(w, CROP_SIZE), max(h, CROP_SIZE)))
        h, w, _ = frame.shape

    # YOLOv5 Tahmini
    results = model(frame)
    detections = results.pandas().xyxy[0]
    
    # Yüksek güvenli tespitleri filtrele
    high_conf_detections = detections[detections['confidence'] >= CONF_THRESHOLD]

    # Tespit edilen nesne yoksa fonksiyondan çık
    if high_conf_detections.empty:
        return crop_idx

    # 1. Merkez Noktası: En yüksek güven skoruna sahip ilk nesne
    ana_nesne = high_conf_detections.iloc[0]
    center_x = int((ana_nesne['xmin'] + ana_nesne['xmax']) / 2)
    center_y = int((ana_nesne['ymin'] + ana_nesne['ymax']) / 2)

    # 2. 800x800 Kırpma Penceresi Sınırlarını Hesapla
    x1 = max(0, center_x - HALF_SIZE)
    x2 = x1 + CROP_SIZE
    if x2 > w:
        x2 = w
        x1 = max(0, w - CROP_SIZE)

    y1 = max(0, center_y - HALF_SIZE)
    y2 = y1 + CROP_SIZE
    if y2 > h:
        y2 = h
        y1 = max(0, h - CROP_SIZE)

    crop = frame[y1:y2, x1:x2].copy()
    crop_h, crop_w, _ = crop.shape

    etiket_satirlari = []
    gecerli_nesne_sayisi = 0

    # 3. Kırpılan Alanın İçine Düşen Nesneleri Kontrol Et
    for idx, row in high_conf_detections.iterrows():
        obj_center_x = (row['xmin'] + row['xmax']) / 2
        obj_center_y = (row['ymin'] + row['ymax']) / 2

        if x1 <= obj_center_x <= x2 and y1 <= obj_center_y <= y2:
            new_xmin = max(0, row['xmin'] - x1)
            new_xmax = min(crop_w, row['xmax'] - x1)
            new_ymin = max(0, row['ymin'] - y1)
            new_ymax = min(crop_h, row['ymax'] - y1)

            # Normalize et (0-1 arası)
            norm_x_center = ((new_xmin + new_xmax) / 2) / crop_w
            norm_y_center = ((new_ymin + new_ymax) / 2) / crop_h
            norm_width = (new_xmax - new_xmin) / crop_w
            norm_height = (new_ymax - new_ymin) / crop_h
            cls = int(row['class'])

            # Sınır taşmalarını engelle
            norm_x_center = max(0.0, min(1.0, norm_x_center))
            norm_y_center = max(0.0, min(1.0, norm_y_center))
            norm_width = max(0.0, min(1.0, norm_width))
            norm_height = max(0.0, min(1.0, norm_height))

            etiket_satirlari.append(f"{cls} {norm_x_center:.6f} {norm_y_center:.6f} {norm_width:.6f} {norm_height:.6f}\n")
            gecerli_nesne_sayisi += 1

    # Etiket varsa kaydet
    if etiket_satirlari:
        crop_idx += 1
        split = 'train' if random.random() < Train_Val_Split else 'val'
        
        file_identifier = f"{prefix}_f{frame_idx}_crop{crop_idx}"
        img_path = os.path.join(f'auto_dataset/images/{split}', f"{file_identifier}.jpg")
        label_path = os.path.join(f'auto_dataset/labels/{split}', f"{file_identifier}.txt")

        cv2.imwrite(img_path, crop)

        with open(label_path, 'w') as f:
            f.writelines(etiket_satirlari)

        print(f"Kaydedildi: {img_path} (Nesne sayısı: {gecerli_nesne_sayisi})")
    
    return crop_idx


# --- VERİ SETİ TRAMA DÖNGÜSÜ ---
for data_file in os.listdir(Data_path):
    file_ext = os.path.splitext(data_file)[1].lower()
    
    # 1. Görselleri İşle
    if file_ext in ['.png', '.jpg', '.jpeg']:
        img_path = os.path.join(Data_path, data_file)
        frame = cv2.imread(img_path)
        prefix = os.path.splitext(data_file)[0]
        
        saved_crops = process_frames(frame, prefix=prefix, frame_idx=0, crop_idx=0)
        total_saved_count += saved_crops

    # 2. Videoları İşle
    elif file_ext in ['.mp4', '.avi', '.mov']:
        video_path = os.path.join(Data_path, data_file)
        cap = cv2.VideoCapture(video_path)
    
        if not cap.isOpened():
            continue
    
        frame_count = 0
        saved_count = 0
        video_prefix = os.path.splitext(data_file)[0]

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % 30 == 0:  # Her 30 karede bir işle
                saved_count = process_frames(frame, prefix=video_prefix, frame_idx=frame_count, crop_idx=saved_count)
                
        cap.release()
        total_saved_count += saved_count
        print(f"{data_file} tamamlandı. {saved_count} adet kırpılmış görsel üretildi.")

# 4. data.yaml Dosyasını Oluştur
data_yaml_path = 'auto_dataset/data.yaml'
with open(data_yaml_path, 'w') as f:
    yaml.dump({
        'path': os.path.abspath('auto_dataset'),
        'train': 'images/train',
        'val': 'images/val',
        'nc': 1,
        'names': ['plate']
    }, f, default_flow_style=False)

print(f"\nTüm süreç tamamlandı. Toplam {total_saved_count} görsel auto_dataset içine dağıtıldı.")

if input("training_bin dosyasını temizlemek istiyor musunuz? (y/n): ").lower() == 'y':
    for file in os.listdir(Data_path):
        if not file.endswith(".gitkeep"):
            os.remove(os.path.join(Data_path, file))