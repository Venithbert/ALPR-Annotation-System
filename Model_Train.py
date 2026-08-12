import os
import shutil
import subprocess
import sys

def start_training():
    models_dir = 'Models'
    yolov5_dir = 'yolov5'
    data_set_dir = 'auto_dataset'
    data_yaml = os.path.abspath(f'../plaka_tanima_sistemi/{data_set_dir}/data.yaml')
    model_name = 'model'
    new_model = False
    weights_path = 'yolov5s.pt'  # Sıfırdan eğitim için varsayılan model

    IMG_SIZE = 800
    BATCH_SIZE = 4
    EPOCHS = 50
    past_version = None  # Örn: "model4(bestv1)"

    # 1. Klasör ve Model Dosyalarının Kontrolü
    if not os.path.exists(models_dir):
        print(f"Hata: '{models_dir}' klasörü bulunamadı, oluşturuluyor...")
        os.makedirs(models_dir, exist_ok=True)

    # Klasör içindeki ilgili .pt dosyalarını filtreleme
    pt_files = [
        os.path.join(models_dir, f) 
        for f in os.listdir(models_dir) 
        if f.endswith('.pt') and model_name in f
    ]
    
    if not pt_files:
        print(f"Uyarı: '{models_dir}' içinde '{model_name}' içeren .pt uzantılı model bulunamadı!")
        new_model = True
        print(f"Yeni Model Oluşturuluyor! (Baz Model: {weights_path})")
    else:
        latest_model_path = max(pt_files, key=os.path.getmtime)
        if not past_version:
            weights_path = os.path.abspath(latest_model_path)
        else:
            weights_path = os.path.abspath(f'{models_dir}/{past_version}.pt')

    # 2. Dataset Kontrolü
    dataset_img_dir = os.path.join('auto_dataset')
    if not os.path.exists(dataset_img_dir) or len(os.listdir(dataset_img_dir)) == 0:
        print("Hata: 'auto_dataset' dizini boş veya bulunamadı!")
        return

    print("\nYOLOv5 Eğitimi Başlatılıyor...")
    print(f"Veri Seti: {data_yaml}")
    print(f"Başlangıç Ağırlığı: {weights_path}\n")

    # 3. YOLOv5 train.py Komut Parametreleri
    cmd = [
        sys.executable, os.path.join(yolov5_dir, "train.py"),
        '--img', str(IMG_SIZE),
        '--batch', str(BATCH_SIZE),
        '--epochs', str(EPOCHS),
        '--data', data_yaml,
        '--weights', weights_path,
        '--project', 'runs/train',
        '--name', 'auto_trained_model',
        '--exist-ok'
    ]

    # 4. Eğitimi Başlatma ve Sonuç Modeli Kopyalama
    try:
        subprocess.run(cmd, check=True)
        
        trained_best_weights = os.path.join('runs', 'train', 'auto_trained_model', 'weights', 'best.pt')
        
        if os.path.exists(trained_best_weights):
            # Sadece .pt dosyalarını sayarak versiyonlama
            existing_pt_count = len([f for f in os.listdir(models_dir) if f.endswith('.pt')])
            new_model_name = f"{model_name}_model_{existing_pt_count + 1}.pt"
            destination_path = os.path.join(models_dir, new_model_name)
            
            shutil.copy2(trained_best_weights, destination_path)
            print(f"\nYeni eğitilen model kaydedildi: {destination_path}")
        else:
            print("\nUyarı: Eğitim bitti ancak 'best.pt' dosyası bulunamadı.")

        print("\nEğitim başarıyla tamamlandı! Çıktılar 'runs/train/auto_trained_model' klasöründe.")
        
    except subprocess.CalledProcessError as e:
        print(f"\nEğitim sırasında bir hata oluştu: {e}")

if __name__ == '__main__':
    start_training()