try:
   
    ham_sonuc, final_conf = read_plate(str(img_path))
    tahmin_edilen = clean_plate_text(ham_sonuc)
    
    
    if len(tahmin_edilen) > 0 and final_conf > 0.0:
        status = "ok"
    else:
        tahmin_edilen, final_conf, status = "", 0.0, "error"
        
except Exception as e:
    print(f"Okuma hatası ({dosya_adi}): {e}")
    tahmin_edilen, final_conf, status = "", 0.0, "error"


conf_str = f"{final_conf:.2f}" if status == "ok" else "0.0"
writer.writerow([dosya_adi, tahmin_edilen, conf_str, status])


hedef_klasor = OK_FOLDER if status == "ok" else ERROR_FOLDER
shutil.copy(img_path, hedef_klasor / dosya_adi)