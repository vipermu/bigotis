import os
from typing import *

import numpy as np
import torch
import torchvision.transforms as T
import torchvision.transforms.functional as TF
import clip
import PIL
from dall_e import map_pixels, unmap_pixels, load_model

target_img_size = 256
final_img_size = 512

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("USING ", device)

clip_model, clip_preprocess = clip.load("ViT-B/32", device=device)
clip_model.eval()
clip_transform = T.Compose([
    # clip_preprocess.transforms[2],
    clip_preprocess.transforms[4],
])

dec = load_model("https://cdn.openai.com/dall-e/decoder.pkl", device)
dec.eval()


def preprocess(img):
    min_img_dim = min(img.size)

    if min_img_dim < target_img_size:
        raise ValueError(f'min dim for img {min_img_dim} < {target_img_size}')

    img_ratio = target_img_size / min_img_dim
    min_img_dim = (round(img_ratio * img.size[1]),
                   round(img_ratio * img.size[0]))
    img = TF.resize(img, min_img_dim, interpolation=PIL.Image.LANCZOS)
    img = TF.center_crop(img, output_size=2 * [target_img_size])
    img = torch.unsqueeze(T.ToTensor()(img), 0)
    return map_pixels(img)


def compute_clip_loss(img, text):
    img = clip_transform(img)
    img = torch.nn.functional.upsample_bilinear(img, (224, 224))
    img_logits = clip_model.encode_image(img)

    tokenized_text = clip.tokenize([text]).to(device).detach().clone()
    text_logits = clip_model.encode_text(tokenized_text)

    loss = 10 * -torch.cosine_similarity(text_logits, img_logits).mean()

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

        crop = torch.nn.functional.upsample_bilinear(crop, (224, 224))

        crop_list.append(crop)

    img = torch.cat(crop_list, axis=0)

    return img


def generate_from_prompt(
    prompt: str,
    lr: float = 3e-1,
    img_save_freq: int = 1,
    num_generations: int = 200,
    num_random_crops: int = 20,
):
    gen_img_list = []

    z_logits = torch.rand((1, 8192, 64, 64)).to(device)
    z_logits = torch.nn.Parameter(z_logits, requires_grad=True)

    optimizer = torch.optim.Adam(
        params=[z_logits],
        lr=lr,
        betas=(0.9, 0.999),
    )

    counter = 0
    while True:
        z = torch.nn.functional.gumbel_softmax(
            z_logits.permute(0, 2, 3, 1).reshape(1, 64**2, 8192),
            hard=False,
            dim=1,
        ).view(1, 8192, 64, 64)

        x_stats = dec(z).float()
        x_rec = unmap_pixels(torch.sigmoid(x_stats[:, :3]))

        x_rec_stacked = get_stacked_random_crops(
            img=x_rec,
            num_random_crops=num_random_crops,
        )

        loss = compute_clip_loss(x_rec_stacked, prompt)

        print(loss)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        counter += 1

        if counter % img_save_freq == 0:
            print("Saving generation...")
            x_rec_img = T.ToPILImage(mode='RGB')(x_rec[0])
            gen_img_list.append(x_rec_img)

        if counter > num_generations:
            break

    return gen_img_list


# if __name__ == "__main__":
#     prompt = "The image of a delicious avocado"
#     _ = generate_img_from_prompt(
#         prompt=prompt,
#         out_img_path=f"public/environments/img/{prompt}.png",
#         lr=0.8,
#         img_save_freq=2,
#     )
