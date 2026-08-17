import re
import torch
from strhub.models.utils import create_model
from PIL import Image 
from strhub.data.module import SceneTextDataModule

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Kullanılan cihaz:", device)

# Pretrained PARSeq modelini yüklüyoruz
model = create_model("parseq", pretrained=True).to(device).eval()
img_transform = SceneTextDataModule.get_transform(model.hparams.img_size)


def clean_plate_text(text):
    """Sadece harf ve rakamları tutar, özel karakterleri temizler."""
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def read_plate(image_path, max_length=None):
    image = Image.open(image_path).convert("RGB")
    image_tensor = img_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(image_tensor)

    prob = logits.softmax(-1)
    pred, confidence = model.tokenizer.decode(prob)

    raw_text = pred[0]
    cleaned_text = clean_plate_text(raw_text)

    # Karakter bazlı ortalama confidence skorunu alıyoruz
    if isinstance(confidence[0], torch.Tensor):
        mean_conf = confidence[0].mean().item()
    elif isinstance(confidence[0], (list, tuple)):
        mean_conf = sum(confidence[0]) / max(len(confidence[0]), 1)
    else:
        mean_conf = float(confidence[0])

    print(f"PARSeq ham sonuç: '{raw_text}' -> Temizlenen: '{cleaned_text}' (Skor: {mean_conf:.2f})")

    return cleaned_text, mean_conf