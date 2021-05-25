import os
import glob
from typing import *
from PIL import Image

import numpy as np
import torch
import torchvision.transforms as T
import torch.nn.functional as F
import torchvision.transforms.functional as TF
import clip
import PIL
from dall_e import map_pixels, unmap_pixels, load_model

target_img_size = 256
embed_size = target_img_size // 8
dalle_latent_dim = 8192

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print("USING ", DEVICE)

clip_model, clip_preprocess = clip.load("ViT-B/32", device=DEVICE)
clip_model.eval()
# NOTE: just adding the normalization transformation
clip_transform = T.Compose([
    clip_preprocess.transforms[4],
])

dalle_enc = load_model("https://cdn.openai.com/dall-e/encoder.pkl", DEVICE)
dalle_enc.eval()
dalle_dec = load_model("https://cdn.openai.com/dall-e/decoder.pkl", DEVICE)
dalle_dec.eval()


def dalle_img_preprocess(img):
    img = img.convert("RGB")

    min_img_dim = min(img.size)

    scale_factor = target_img_size / min_img_dim
    scaled_img_dim = (round(scale_factor * img.size[0]),
                      round(scale_factor * img.size[1]))
    img = img.resize(scaled_img_dim, PIL.Image.LANCZOS)
    img = TF.center_crop(img, output_size=2 * [target_img_size])
    img_tensor = torch.unsqueeze(T.ToTensor()(img), 0).to(DEVICE)

    return map_pixels(img_tensor)


def get_dalle_img_encodings(
    img_batch,
    do_preprocess=False,
):
    if do_preprocess:
        img_batch = dalle_img_preprocess(img_batch)

    z_logits = dalle_enc(img_batch)

    return z_logits


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


def generate_from_prompt(
    prompt: str,
    lr: float = 3e-1,
    img_save_freq: int = 1,
    num_generations: int = 200,
    num_random_crops: int = 20,
    img_batch=None,
):
    gen_img_list = []

    # z_logits = .5 * torch.randn(1, dalle_latent_dim, embed_size,
    #                             embed_size).cuda()
    # z_logits = torch.sinh(1.9 * torch.arcsinh(z_logits))
    # z_logits = z_logits.clip(-6, 6)

    rand_img = torch.zeros((1, 3, target_img_size, target_img_size)).to(DEVICE)
    rand_img = map_pixels(rand_img)
    with torch.no_grad():
        z_logits = get_dalle_img_encodings(rand_img)

    # z_logits = z_logits / 10

    # z_logits = torch.randn(
    #     (1, dalle_latent_dim, embed_size, embed_size)).to(DEVICE)

    if img_batch is not None:
        dalle_img_z_logits = get_dalle_img_encodings(img_batch)
        dalle_img_z_logits = dalle_img_z_logits.detach().clone()
        clip_img_z_logits = get_clip_img_encodings(img_batch)
        clip_img_z_logits = clip_img_z_logits.detach().clone()

    z_logits = torch.nn.Parameter(z_logits.clone(), requires_grad=True)

    optimizer = torch.optim.AdamW(
        params=[z_logits],
        lr=lr,
        betas=(0.9, 0.999),
        weight_decay=0.1,
    )

    temp = 1
    for step in range(num_generations):
        loss = 0

        print(z_logits.max())

        z = F.gumbel_softmax(
            z_logits.permute(0, 2, 3, 1).reshape(1, embed_size**2,
                                                 dalle_latent_dim),
            tau=temp,
            hard=False,
            dim=-1,
        ).view(1, embed_size, embed_size,
               dalle_latent_dim).permute(0, 3, 1, 2)

        x_stats = dalle_dec(z).float()
        x_rec = unmap_pixels(torch.sigmoid(x_stats[:, :3]))

        x_rec_stacked = get_stacked_random_crops(
            img=x_rec,
            num_random_crops=num_random_crops,
        )

        # loss += 10 * compute_clip_loss(x_rec_stacked, prompt)

        # if img_batch is not None:
        #     loss += -torch.cosine_similarity(z_logits,
        #                                      dalle_img_z_logits).mean()
        if img_batch is not None:
            loss += -torch.cosine_similarity(get_clip_img_encodings(x_rec),
                                             clip_img_z_logits).mean()

        print(loss)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % img_save_freq == 0:
            print("Saving generation...")
            x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
            gen_img_list.append(x_rec_img)

            x_rec_img.save(f"test_imgs/{step}.png")

    return gen_img_list


if __name__ == "__main__":
    prompt = "The logo of CHANEL"

    img_tensor_list = []
    for img_path in glob.glob("./img-refs/*"):
        img = Image.open(img_path)
        img_tensor_list.append(dalle_img_preprocess(img))

    img = torch.cat(img_tensor_list)

    # img = Image.open('ref_imgs/1.png')
    # img = dalle_img_preprocess(img)

    _ = generate_from_prompt(
        prompt=prompt,
        lr=0.5,
        img_save_freq=1,
        num_generations=10000,
        num_random_crops=1,
        img_batch=img,
    )
