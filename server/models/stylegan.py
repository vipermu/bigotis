import os
import math
import argparse

import torch
import torchvision
import clip
import numpy as np
from PIL import Image

from models.stylegan_models import g_synthesis

torch.manual_seed(20)

parser = argparse.ArgumentParser()
parser.add_argument(
    '--output_path',
    type=str,
    default='./generations',
    help='',
)
parser.add_argument(
    '--batch_size',
    type=int,
    default=1,
    help='Batch Size',
)
parser.add_argument(
    '--prompt',
    type=str,
    default=
    'An image with the face of a blonde woman with blonde hair and purple eyes',
    help='',
)
parser.add_argument(
    '--lr',
    type=float,
    default=3e-2,
    help='',
)
parser.add_argument(
    '--img_save_freq',
    type=int,
    default=5,
    help='',
)


# TODO: put this in a utils func or something
def tensor_to_pil_img(img):
    img = (img.clamp(-1, 1) + 1) / 2.0
    img = img[0].permute(1, 2, 0).detach().cpu().numpy() * 255
    img = Image.fromarray(img.astype('uint8'))
    return img


class StyleGAN:
    def __init__(self, ):
        args = parser.parse_args()

        output_path = args.output_path
        self.batch_size = args.batch_size
        self.prompt = args.prompt
        self.lr = args.lr

        output_dir = os.path.join(output_path, f'"{self.prompt}"')

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print("USING ", self.device)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.clip_model, self.clip_preprocess = clip.load(
            "ViT-B/32",
            device=self.device,
        )
        g_synthesis.eval()
        g_synthesis.to(self.device)

        self.latent_shape = (self.batch_size, 1, 512)

        self.normal_generator = torch.distributions.normal.Normal(
            torch.tensor([0.0]),
            torch.tensor([1.]),
        )

        self.clip_transform = torchvision.transforms.Compose([
            # clip_preprocess.transforms[2],
            self.clip_preprocess.transforms[4],
        ])

        self.clip_normalize = torchvision.transforms.Normalize(
            mean=(0.48145466, 0.4578275, 0.40821073),
            std=(0.26862954, 0.26130258, 0.27577711),
        )

    def truncation(
        self,
        x,
        threshold=0.7,
        max_layer=8,
    ):
        avg_latent = torch.zeros(self.batch_size, x.size(1),
                                 512).to(self.device)
        interp = torch.lerp(avg_latent, x, threshold)
        do_trunc = (torch.arange(x.size(1)) < max_layer).view(1, -1, 1).to(
            self.device)
        return torch.where(do_trunc, interp, x)

    def compute_clip_loss(
        self,
        img,
        text,
    ):
        img = ((img + 1) /2).clip(0,1)
        # img = self.clip_transform(img)
        img = self.clip_normalize(img)
        img = torch.nn.functional.upsample_bilinear(img, (224, 224))
        tokenized_text = clip.tokenize([text]).to(self.device)

        img_logits = self.clip_model.encode_image(img)
        text_logits = self.clip_model.encode_text(tokenized_text)

        # img_logits, _text_logits = self.clip_model(img, tokenized_text)

        loss = torch.cosine_similarity(img_logits, text_logits)

        return -10 * loss

    def generate_from_prompt(
        self,
        prompt: str,
        lr: float = 1e-2,
        img_save_freq: int = 1,
        num_generations: int = 200,
    ):
        # init_latents = self.normal_generator.sample(self.latent_shape).squeeze(-1).to(self.device)
        latents_init = torch.zeros(self.latent_shape).squeeze(-1).to(
            self.device)
        latents = torch.nn.Parameter(latents_init, requires_grad=True)

        optimizer = torch.optim.Adam(
            params=[latents],
            lr=lr,
            betas=(0.9, 0.999),
        )

        gen_img_list = []
        latents_list = []
        counter = 0
        for _step in range(num_generations):
            dlatents = latents.repeat(1, 18, 1)
            img = g_synthesis(dlatents)

            # NOTE: clip normalization did not seem to have much effect
            # img = self.clip_normalize(img)

            loss = self.compute_clip_loss(img, prompt)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            counter += 1

            if counter % img_save_freq == 0:
                img = tensor_to_pil_img(img)
                img.save(f"generations/{counter}.png")
                gen_img_list.append(img)

                print(f'Step {counter}')
                print(f'Loss {loss.data.cpu().numpy()[0]}')

                latents_list.append(latents.clone())

        return gen_img_list, latents_list

    def interpolate(
        latents_list,
        duration_list,
    ):
        gen_img_list = []
        fps = 25

        for idx, (latents,
                  duration) in enumerate(zip(latents_list, duration_list)):
            num_steps = int(duration * fps)
            latents1 = latents
            latents2 = latents_list[(idx + 1) % len(latents_list)]

            dlatents1 = latents1.repeat(1, 18, 1)
            dlatents2 = latents2.repeat(1, 18, 1)

            for step in range(num_steps):
                weight = math.sin(1.5708 * step / num_steps)**2
                dlatents = weight * dlatents2 + (1 - weight) * dlatents1

                img = g_synthesis(dlatents)
                img = tensor_to_pil_img(img)

                gen_img_list.append(img)

        return gen_img_list


if __name__ == "__main__":
    stylegan = StyleGAN()
    stylegan.generate_from_prompt("The image of a woman with purple hair")