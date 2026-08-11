import torch
from strhub.models.utils import create_model
from PIL import Image
from strhub.data.module import SceneTextDataModule


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Kullanılan cihaz:", device)

model = create_model("parseq", pretrained=True).to(device)

img_transform = SceneTextDataModule.get_transform(model.hparams.img_size)


def read_plate(image_path):
    image = Image.open(image_path).convert("RGB")

    image_tensor = img_transform(image).unsqueeze(0).to(device)

    logits = model(image_tensor)

    prob = logits.softmax(-1)
    pred, confidence = model.tokenizer.decode(prob)

    return pred[0]