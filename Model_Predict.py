import cv2
import torch
from pathlib import Path
import pathlib

# --- WINDOWS POSIXPATH HATASI İÇİN YAMA (PATCH) ---
# Linux'ta kaydedilen modeli Windows'ta açabilmek için PosixPath'i WindowsPath'e eşitliyoruz.
pathlib.PosixPath = pathlib.WindowsPath
# --------------------------------------------------

# 1. Modeli yükleyin (String olarak tam yol vermek daha güvenlidir)
model_path = r"C:\Users\Ceng\Desktop\Optima staj ortak proje\ALPR-Evaluation-System\model_16.pt"
model = torch.hub.load("ultralytics/yolov5", "custom", path=model_path, force_reload=True)

# 2. Görseli yükleyin
# Eğer test_images klasörü ALPR-Evaluation-System içindeyse:
img_path = r"C:\Users\Ceng\Desktop\Optima staj ortak proje\ALPR-Evaluation-System\test_images\cyprus (1).jpg"
img = cv2.imread(img_path)

# 3. Görseli modele gönderin (Tahmin yapın)
if img is not None:
    results = model(img)
    results.print()
    results.show()
else:
    print("Hata: Görsel belirtilen yolda bulunamadı!")
