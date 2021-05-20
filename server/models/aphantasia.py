import os
import argparse
from typing import *

import numpy as np
import torch
import torchvision
import torchvision.transforms.functional as TF
import torch.nn.functional as F
import clip
from imageio import imsave
from PIL import Image

model_list = ['ViT-B/32', 'RN50', 'RN50x4', 'RN101']

img_norm = torchvision.transforms.Normalize(
    (0.48145466, 0.4578275, 0.40821073),
    (0.26862954, 0.26130258, 0.27577711),
)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--input_text',
        default=None,
        help='input text',
    )
    parser.add_argument(
        '--micro_text',
        default=None,
        help='input text for small details',
    )
    parser.add_argument(
        '--substract_text',
        default=None,
        help='input text to subtract',
    )

    parser.add_argument(
        '--out_dir',
        default='_out',
    )
    parser.add_argument(
        '--size',
        default='3000-3000',
        help='Output resolution',
    )
    parser.add_argument(
        '--save_freq',
        default=1,
        type=int,
        help='Saving step',
    )
    parser.add_argument(
        '--save_pt',
        action='store_true',
        help='Save FFT snapshots for further use',
    )
    parser.add_argument(
        '--batch_size',
        default=1,
        type=int,
        help='Batch size generation',
    )

    # training
    parser.add_argument(
        '--model',
        default='ViT-B/32',
        choices=model_list,
        help='Select CLIP model to use',
    )
    parser.add_argument(
        '--num_steps',
        default=400,
        type=int,
        help='Total iterations',
    )
    parser.add_argument(
        '--num_crops',
        default=200,
        type=int,
        help='Samples to evaluate',
    )
    parser.add_argument(
        '--lrate',
        default=1.5,
        type=float,
        help='Learning rate',
    )
    parser.add_argument(
        '--prog',
        action='store_true',
        help='Enable progressive lrate growth (up to double a.lrate)',
    )

    # tweaks
    parser.add_argument(
        '--contrast',
        default=1.,
        type=float,
    )
    parser.add_argument(
        '--colors',
        default=1.,
        type=float,
    )
    parser.add_argument(
        '--decay',
        default=1,
        type=float,
    )
    parser.add_argument(
        '--noise',
        default=0,
        type=float,
        help='Add noise to suppress accumulation',
    )  # < 0.05 ?
    parser.add_argument(
        '--sync',
        default=0,
        type=float,
        help='Sync output to input image',
    )
    parser.add_argument(
        '--invert',
        action='store_true',
        help='Invert criteria',
    )
    args = parser.parse_args()

    if args.size is not None:
        args.size = [int(s) for s in args.size.split('-')][::-1]

    if len(args.size) == 1:
        args.size = args.size * 2

    args.modsize = 288 if args.model == 'RN50x4' else 224

    return args


# From https://github.com/tensorflow/lucid/blob/master/lucid/optvis/param/spatial.py
def rfft2d_freqs(height, width):
    """Computes 2D spectrum frequencies."""
    y_freqs = np.fft.fftfreq(height)[:, None]
    # when we have an odd input dimension we need to keep one additional frequency and later cut off 1 pixel
    width_even_idx = (width + 1) // 2 if width % 2 == 1 else width // 2 + 1

    x_freqs = np.fft.fftfreq(width)[:width_even_idx]

    return np.sqrt(x_freqs * x_freqs + y_freqs * y_freqs)


def get_fft_img(
    spectrum_size: Union[List[int], Tuple[int]],
    std: float = 0.01,
    return_img_freqs=False,
):
    """
    """
    batch_size, num_channels, height, width = spectrum_size

    #NOTE: generate all possible freqs for the input image size
    img_freqs = rfft2d_freqs(height, width)

    #NOTE: 2 for imaginary and real components
    spectrum_shape = [
        batch_size,
        num_channels,
        *img_freqs.shape,
        2,
    ]

    fft_img = (torch.randn(*spectrum_shape) * std)

    if return_img_freqs:
        return fft_img, img_freqs
    else:
        return fft_img


def get_scale_from_img_freqs(
    img_freqs,
    decay_power,
):
    height, width = img_freqs.shape
    clamped_img_freqs = np.maximum(img_freqs, 1.0 / max(width, height))

    scale = 1.0 / clamped_img_freqs**decay_power
    scale *= np.sqrt(width * height)
    scale = torch.tensor(scale).float()[None, None, ..., None]

    return scale


def fft_to_rgb(
    fft_img,
    scale,
    img_size,
    shift=None,
    contrast=1.,
    decorrelate=True,
    device="cuda",
):
    num_channels = 3
    im = 2

    scaled_fft_img = scale * fft_img
    if shift is not None:
        scaled_fft_img += scale * shift

    image = torch.irfft(
        scaled_fft_img,
        im,
        normalized=True,
        signal_sizes=img_size,
    )
    image = image * contrast / image.std()  # keep contrast, empirical

    if decorrelate:
        colors = 1
        color_correlation_svd_sqrt = np.asarray([
            [0.26, 0.09, 0.02],
            [0.27, 0.00, -0.05],
            [0.27, -0.09, 0.03],
        ]).astype("float32")
        color_correlation_svd_sqrt /= np.asarray([
            colors,
            1.,
            1.,
        ])  # saturate, empirical

        max_norm_svd_sqrt = np.max(
            np.linalg.norm(color_correlation_svd_sqrt, axis=0))

        color_correlation_normalized = color_correlation_svd_sqrt / max_norm_svd_sqrt

        image_permute = image.permute(0, 2, 3, 1)
        image_permute = torch.matmul(
            image_permute,
            torch.tensor(color_correlation_normalized.T).to(device))

        image = image_permute.permute(0, 3, 1, 2)

    image = torch.sigmoid(image)

    return image


def checkout(
    img,
    fname=None,
):
    img = np.transpose(np.array(img)[:, :, :], (1, 2, 0))
    if fname is not None:
        img = np.clip(img * 255, 0, 255).astype(np.uint8)
        imsave(fname, img)


def get_stacked_random_crops(img, num_random_crops=64):
    crop_trans = torchvision.transforms.RandomCrop(img.shape[2:4])
    img = crop_trans(img)
    img_size = [img.shape[2], img.shape[3]]

    crop_list = []
    for _ in range(num_random_crops):
        crop_size_y = int(img_size[0] * torch.zeros(1, ).uniform_(.2, .8))
        crop_size_x = int(img_size[1] * torch.zeros(1, ).uniform_(.2, .8))

        y_offset = torch.randint(0, img_size[0] - crop_size_y, ())
        x_offset = torch.randint(0, img_size[1] - crop_size_x, ())

        crop = img[:, :, y_offset:y_offset + crop_size_y,
                   x_offset:x_offset + crop_size_x]

        crop = torch.nn.functional.upsample_bilinear(crop, (224, 224))
        # crop = torch.nn.functional.interpolate(
        #     crop,
        #     (224, 224),
        #     mode='bilinear',
        # )

        crop_list.append(crop)

    img = torch.cat(crop_list, axis=0)

    return img


def random_crop(
    img,
    num_crops,
    crop_size=224,
    normalize=True,
):
    def map(x, a, b):
        return x * (b - a) + a

    rnd_size = torch.rand(num_crops)
    rnd_offx = torch.clip(torch.randn(num_crops) * 0.2 + 0.5, 0., 1.)
    rnd_offy = torch.clip(torch.randn(num_crops) * 0.2 + 0.5, 0., 1.)

    img_size = img.shape[2:]
    min_img_size = min(img_size)

    sliced = []
    cuts = []
    for c in range(num_crops):
        current_crop_size = map(rnd_size[c], crop_size, min_img_size).int()

        offsetx = map(rnd_offx[c], 0, img_size[1] - current_crop_size).int()
        offsety = map(rnd_offy[c], 0, img_size[0] - current_crop_size).int()
        cut = img[:, :, offsety:offsety + current_crop_size,
                  offsetx:offsetx + current_crop_size]
        cut = F.interpolate(
            cut,
            (crop_size, crop_size),
            mode='bicubic',
            align_corners=False,
        )  # bilinear

        if normalize is not None:
            cut = img_norm(cut)

        cuts.append(cut)

    return torch.cat(cuts, axis=0)


def generate_from_prompt(
    prompt: str,
    lr: float = 3e-1,
    img_save_freq: int = 1,
    num_generations: int = 200,
    num_random_crops: int = 20,
    resolution: str = "1024-1024",
):
    args = get_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"

    args.input_text = prompt
    args.lrate = lr
    args.save_freq = img_save_freq
    args.num_steps = num_generations
    args.num_random_crops = num_random_crops

    if resolution is not None:
        args.size = tuple([int(res) for res in resolution.split("-")])

    gen_img_list = []

    clip_model, _ = clip.load(args.model)
    print(f"Using model {args.model}")

    input_text = args.input_text
    print(f"Generating from '{input_text}'")

    tokenized_text = clip.tokenize([input_text]).to(device).detach().clone()
    text_logits = clip_model.encode_text(tokenized_text)

    num_channels = 3
    spectrum_size = [args.batch_size, num_channels, *args.size]
    fft_img, img_freqs = get_fft_img(
        spectrum_size,
        std=0.01,
        return_img_freqs=True,
    )

    fft_img = fft_img.to(device)
    fft_img.requires_grad = True

    scale = get_scale_from_img_freqs(
        img_freqs=img_freqs,
        decay_power=args.decay,
    )

    scale = scale.to(device)

    shift = None
    if args.noise > 0:
        img_size = img_freqs.shape
        noise_size = (1, 1, *img_size, 1)
        shift = self.noise * torch.randn(noise_size, ).to(self.device)

    # optimizer = torch.optim.Adam(
    #     [fft_img],
    #     args.lrate,
    # )
    optimizer = torch.optim.SGD(
        [fft_img],
        args.lrate,
    )

    for step in range(args.num_steps):
        loss = 0

        initial_img = fft_to_rgb(
            fft_img=fft_img,
            scale=scale,
            img_size=args.size,
            shift=shift,
            contrast=1.0,
            decorrelate=True,
            device=device,
        )

        # crop_img_out = random_crop(
        #     initial_img,
        #     num_crops,
        #     crop_size,
        #     normalize=True,
        # )
        crop_img_out = get_stacked_random_crops(
            initial_img,
            num_random_crops,
        )
        img_logits = clip_model.encode_image(crop_img_out).to(device)
        tokenized_text = clip.tokenize([input_text]).to(device)
        text_logits = clip_model.encode_text(tokenized_text)

        loss += -10 * torch.cosine_similarity(
            text_logits,
            img_logits,
            dim=-1,
        ).mean()

        print(loss)

        # torch.cuda.empty_cache()

        # if self.prog is True:
        #     lr_cur = lr + (step / self.steps) * (init_lr - lr)
        #     for g in self.optimizer.param_groups:
        #         g['lr'] = lr_cur

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if step % args.save_freq == 0:
            print("Saving generation...")
            with torch.no_grad():
                img = fft_to_rgb(
                    fft_img=fft_img,
                    scale=scale,
                    img_size=args.size,
                    shift=shift,
                    contrast=1.0,
                    decorrelate=True,
                    device=device,
                )
                img = img.detach().cpu().numpy()[0]
                img = np.transpose(np.array(img)[:, :, :], (1, 2, 0))
                img = np.clip(img * 255, 0, 255).astype(np.uint8)
                pil_img = Image.fromarray(img)
                gen_img_list.append(pil_img)

    return gen_img_list


if __name__ == '__main__':
    prompt = "The image of a skull surrounded by fire. A skull in fire. The image of a skull. A white skull"
    lr = 0.8
    img_save_freq = 5
    num_generations = 400
    num_random_crops = 100
    resolution = "512-2048"

    gen_img_list = generate_from_prompt(
        prompt=prompt,
        lr=lr,
        img_save_freq=img_save_freq,
        num_generations=num_generations,
        num_random_crops=num_random_crops,
        resolution=resolution,
    )

    out_dir = os.path.join("public", "generations", prompt)
    os.makedirs(out_dir, exist_ok=True)

    for idx, gen_img in enumerate(gen_img_list):
        gen_img.save(os.path.join(out_dir, f"img_{idx}.png"))
