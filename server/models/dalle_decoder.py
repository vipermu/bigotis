import os
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
embed_size = int(target_img_size / 8)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("USING ", device)

clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
clip_model.eval()
clip_transform = T.Compose([
    # clip_preprocess.transforms[2],
    clip_preprocess.transforms[4],
])

dalle_enc = load_model("https://cdn.openai.com/dall-e/encoder.pkl", device)
dalle_dec = load_model("https://cdn.openai.com/dall-e/decoder.pkl", device)
dalle_enc.eval()
dalle_dec.eval()


def preprocess(img):
    img = img.convert("RGB")

    min_img_dim = min(img.size)

    scale_factor = target_img_size / min_img_dim
    scaled_img_dim = (round(scale_factor * img.size[0]),
                      round(scale_factor * img.size[1]))
    img = img.resize(scaled_img_dim, PIL.Image.LANCZOS)
    img = TF.center_crop(img, output_size=2 * [target_img_size])
    img_tensor = torch.unsqueeze(T.ToTensor()(img), 0).to(device)

    return map_pixels(img_tensor)


def compute_clip_loss(img, text):
    img = clip_transform(img)
    img = F.upsample_bilinear(img, (224, 224))
    img_logits = clip_model.encode_image(img)

    tokenized_text = clip.tokenize([text]).to(device).detach().clone()
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


def get_img_encodings(img_batch, do_preprocess=False):
    if do_preprocess:
        img_batch = preprocess(img_batch)

    z_logits = dalle_enc(img_batch)

    # z = torch.argmax(z_logits, axis=1)
    # z = F.one_hot(
    #     z,
    #     num_classes=dalle_enc.vocab_size,
    # ).permute(0, 3, 1, 2).float()

    return z_logits


def generate_from_prompt(
    prompt: str,
    lr: float = 3e-1,
    img_save_freq: int = 1,
    num_generations: int = 200,
    num_random_crops: int = 20,
    img_batch=None,
):
    gen_img_list = []

    # z_logits = torch.randn((1, 8192, embed_size, embed_size)).to(device)
    z_logits = torch.rand((1, 3, target_img_size, target_img_size)).to(device)
    with torch.no_grad():
        z_logits = get_img_encodings(z_logits)

    if img_batch is not None:
        img_z_logits = get_img_encodings(img_batch)
        img_z_logits = img_z_logits.detach().clone()
        # z_logits = img_z_logits

    z_logits = torch.nn.Parameter(z_logits, requires_grad=True)

    optimizer = torch.optim.Adam(
        params=[z_logits],
        lr=lr,
        betas=(0.9, 0.999),
    )

    temp = 1
    for counter in range(num_generations):
        loss = 0
        z = F.gumbel_softmax(
            z_logits.permute(0, 2, 3, 1).reshape(1, embed_size**2, 8192),
            tau=temp,
            hard=False,
            dim=-1,
        ).view(1, embed_size, embed_size, 8192).permute(0, 3, 1, 2)

        x_stats = dalle_dec(z).float()
        x_rec = unmap_pixels(torch.sigmoid(x_stats[:, :3]))

        # x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
        # x_rec_img.save(f"test_imgs/{counter}.png")

        x_rec_stacked = get_stacked_random_crops(
            img=x_rec,
            num_random_crops=num_random_crops,
        )

        loss += 10 * compute_clip_loss(x_rec_stacked, prompt)
        loss += torch.mean((z_logits - img_z_logits)**2) / 1000

        print(loss)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if counter % img_save_freq == 0:
            print("Saving generation...")
            x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
            gen_img_list.append(x_rec_img)

            x_rec_img.save(f"test_imgs/{counter}.png")

    return gen_img_list


if __name__ == "__main__":
    prompt = "The image of a red rose"

    img = Image.open('ref_imgs/rose.jpeg')
    img = preprocess(img)
    # img = None

    _ = generate_from_prompt(
        prompt=prompt,
        lr=0.9,
        img_save_freq=1,
        num_generations=400,
        num_random_crops=1,
        img_batch=img,
    )
