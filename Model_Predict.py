import os
from pathlib import Path
import cv2
import torch
from paddleocr import TextRecognition

# Reader.py modülünü import ediyoruz
import Reader

# 1. Ayarlar ve Yol Tanımları
models_dir = Path('Models')
pt_files = list(models_dir.glob('*.pt'))
past_version = None 
example_video_name = 'demo44.mp4'

if not pt_files and not past_version:
    raise FileNotFoundError("Models/ klasöründe hiç .pt dosyası bulunamadı!")

latest_model = max(pt_files, key=lambda f: f.stat().st_mtime) if pt_files else None

# 2. Modelleri Yükle
if not past_version:
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(latest_model))
    print(f"Yüklenen model: {latest_model}")
else:
    model = torch.hub.load('ultralytics/yolov5', 'custom', path=str(f'Models/{past_version}.pt'), force_reload=True)
    print(f"Yüklenen model: {past_version}.pt")

# YOLO NMS Time Limit Uyarısını Engelleme
if hasattr(model, 'model'):
    model.model.nms_time_limit = 10.0

ocr_model = TextRecognition(engine="paddle")

# 3. Video Ayarları
input_video_path = f'Examples/Input/{example_video_name}'
output_video_path = f'Examples/Output/{os.path.splitext(example_video_name)[0]}_output.mp4'

os.makedirs('Examples/Output', exist_ok=True)

cap = cv2.VideoCapture(input_video_path)
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Orijinal FPS ve Hedef FPS ayarı
original_fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
target_fps = 10
frame_skip_interval = max(1, round(original_fps / target_fps))

# Çıktı videosunu 10 FPS olarak kaydedecek şekilde VideoWriter'a geçiriyoruz
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(output_video_path, fourcc, target_fps, (frame_width, frame_height))

frame_count = 0

# 4. Video İşleme Döngüsü
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Sadece hedef FPS dilimine uyan kareleri işle (Frame Skipping)
    if frame_count % frame_skip_interval == 0:
        annotated_frame = Reader.process_image_or_frame(frame, model, ocr_model)
        out.write(annotated_frame)

    frame_count += 1

# Kaynakları Serbest Bırak
cap.release()
out.release()
cv2.destroyAllWindows()