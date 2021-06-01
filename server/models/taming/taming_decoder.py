import os
import yaml
from typing import *

import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import torch.nn.functional as F
from PIL import Image
import numpy as np
import clip
from omegaconf import OmegaConf

# from cmodels.taming.vqgan import VQModel
from models.taming.vqgan import VQModel

if not os.path.exists('./server/models/taming/last.ckpt'):
    os.system(
        " wget 'https://heibox.uni-heidelberg.de/f/867b05fc8c4841768640/?dl=1' -O 'server/models/taming/last.ckpt'"
    )

if not os.path.exists('./server/models/taming/model.yaml'):
    os.system(
        "wget 'https://heibox.uni-heidelberg.de/f/274fb24ed38341bfa753/?dl=1' -O 'server/models/taming/model.yaml'"
    )

target_img_size = 256
embed_size = target_img_size // 16
dalle_latent_dim = 8192

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print("USING ", DEVICE)

clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
clip_model.eval()
# NOTE: just adding the normalization transformation
clip_transform = T.Compose([
    clip_preprocess.transforms[4],
])


def load_config(config_path, display=False):
    config = OmegaConf.load(config_path)

    if display:
        print(yaml.dump(OmegaConf.to_container(config)))

    return config


def load_vqgan(config, ckpt_path=None):
    model = VQModel(**config.model.params)

    ckpt_path = "server/models/taming/last.ckpt"
    if ckpt_path is not None:
        sd = torch.load(ckpt_path, map_location="cpu")["state_dict"]
        missing, unexpected = model.load_state_dict(sd, strict=False)

    return model.eval()


def preprocess_vqgan(x):
    x = 2. * x - 1.
    return x


def custom_to_pil(x):
    x = x.detach().cpu()
    x = torch.clamp(x, -1., 1.)
    x = (x + 1.) / 2.
    x = x.permute(1, 2, 0).numpy()
    x = (255 * x).astype(np.uint8)
    x = Image.fromarray(x)

    if not x.mode == "RGB":
        x = x.convert("RGB")

    return x


def reconstruct_with_vqgan(x, model):
    # could also use model(x) for reconstruction but use explicit encoding and decoding here
    z, _, [_, _, indices] = model.encode(x)
    print(f"VQGAN: latent shape: {z.shape[2:]}")
    xrec = model.decode(z)
    return xrec


def get_stacked_random_crops(img, num_random_crops=64):
    img_size = [img.shape[2], img.shape[3]]

    crop_list = []
    for _ in range(num_random_crops):
        crop_size_y = int(img_size[0] * torch.zeros(1, ).uniform_(.75, .95))
        crop_size_x = int(img_size[1] * torch.zeros(1, ).uniform_(.75, .95))

        y_offset = torch.randint(0, img_size[0] - crop_size_y, ())
        x_offset = torch.randint(0, img_size[1] - crop_size_x, ())

        crop = img[:, :, y_offset:y_offset + crop_size_y,
                   x_offset:x_offset + crop_size_x]

        crop = F.upsample_bilinear(crop, (224, 224))

        crop_list.append(crop)

    img = torch.cat(crop_list, axis=0)

    return img


def get_clip_img_encodings(
    img_batch,
    do_preprocess=True,
):
    if do_preprocess:
        img_batch = clip_transform(img_batch)
        img_batch = F.upsample_bilinear(img_batch, (224, 224))

    img_logits = clip_model.encode_image(img_batch)

    return img_logits


def compute_clip_loss(img, text):
    img_logits = get_clip_img_encodings(img)

    tokenized_text = clip.tokenize([text]).to(DEVICE).detach().clone()
    text_logits = clip_model.encode_text(tokenized_text)

    loss = -torch.cosine_similarity(text_logits, img_logits).mean()

    return loss


config_xl = load_config(
    "server/models/taming/model.yaml",
    display=False,
)
vqgan_model = load_vqgan(
    config_xl,
    ckpt_path="server/models.taming/last.ckpt",
).to(DEVICE)


def generate_from_prompt(
    prompt: str,
    lr: float = 0.5,
    img_save_freq: int = 1,
    num_generations: int = 200,
    num_random_crops: int = 20,
    img_batch=None,
):
    batch_size = 1

    z_logits = .5 * torch.randn(
        batch_size,
        256,
        embed_size,
        embed_size,
    ).cuda()

    z_logits = torch.nn.Parameter(torch.sinh(1.9 * torch.arcsinh(z_logits)), )

    optimizer = torch.optim.AdamW(
        params=[z_logits],
        lr=lr,
        betas=(0.9, 0.999),
        weight_decay=0.1,
    )

    gen_img_list = []

    for step in range(num_generations):
        loss = 0

        z = vqgan_model.post_quant_conv(z_logits)
        x_rec = vqgan_model.decoder(z)
        x_rec = (x_rec.clip(-1, 1) + 1) / 2

        x_rec_stacked = get_stacked_random_crops(
            img=x_rec,
            num_random_crops=num_random_crops,
        )

        loss += 10 * compute_clip_loss(x_rec_stacked, prompt)

        # if img_batch is not None:
        #     loss += -torch.cosine_similarity(z_logits,
        #                                      dalle_img_z_logits).mean()
        # if img_batch is not None:
        #     loss += -torch.cosine_similarity(get_clip_img_encodings(x_rec),
        #                                      clip_img_z_logits).mean()

        print(loss)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % img_save_freq == 0:
            print("Saving generation...")
            x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
            gen_img_list.append(x_rec_img)

            # x_rec_img.save(f"test_imgs/{step}.png")

        torch.cuda.empty_cache()

    return gen_img_list


if __name__ == '__main__':
    generate_from_prompt(prompt="penguins wearing chanel", )
