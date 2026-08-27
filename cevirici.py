import json
import os

def convert_coco_to_yolo(json_path, output_folder):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    os.makedirs(output_folder, exist_ok=True)
    
    # Resim bilgilerini eşleştirelim
    for img in data['images']:
        img_id = img['id']
        file_name = img['file_name']
        img_w, img_h = img['width'], img['height']
        
        txt_name = os.path.splitext(file_name)[0] + '.txt'
        txt_path = os.path.join(output_folder, txt_name)
        
        with open(txt_path, 'w', encoding='utf-8') as out_f:
            for ann in data['annotations']:
                if ann['image_id'] == img_id:
                    # COCO bbox yapısı: [x_min, y_min, width, height]
                    x_min, y_min, bbox_w, bbox_h = ann['bbox']
                    
                    # YOLO mantığına (merkez_x, merkez_y, oran_genişlik, oran_yükseklik) çevir
                    x_center = (x_min + bbox_w / 2.0) / img_w
                    y_center = (y_min + bbox_h / 2.0) / img_h
                    norm_w = bbox_w / img_w
                    norm_h = bbox_h / img_h
                    
                    # 0 sınıfı (cyprus_plate) olarak txt dosyasına yazdır
                    out_f.write(f"0 {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}\n")
                    
    print(f"Bitti! Tüm etiketler '{output_folder}' klasörüne YOLO formatında çıkarıldı.")

# İndirdiğin JSON dosyasının adını buraya yazıyorsun
JSON_DOSYASI = "labels_my-project-name_2026-08-26-04-10-33.json" 

convert_coco_to_yolo(JSON_DOSYASI, "yolo_etiketler")