import imageio
from typing import *

import numpy as np
import torch

from models.taming.taming_decoder import TamingDecoder
from models.stylegan import StyleGAN
from models import aphantasia
# from models import dalle_decoder


def single_generation(
    prompt,
    img_list,
    model,
    num_iterations,
    resolution,
    out_dir,
    generate_img,
    generate_video,
):
    img_url = ''
    video_url = ''

    if model == 'aphantasia':
        gen_img_list, feat_list = aphantasia.generate_from_prompt(
            prompt=prompt,
            lr=0.9,
            num_generations=num_iterations,
            img_save_freq=1,
            resolution=resolution,
        )
    # elif model == 'dalle':
    #     gen_img_list = dalle_decoder.generate_from_prompt(
    #         prompt=prompt,
    #         lr=0.7,
    #         num_generations=num_iterations,
    #         img_save_freq=1,
    #     )
    elif model == 'stylegan':
        stylegan = StyleGAN()
        gen_img_list, _feat_list = stylegan.generate_from_prompt(
            prompt=prompt,
            lr=3e-2,
            num_generations=num_iterations,
            img_save_freq=1,
        )
    elif model == 'taming':
        taming_decoder = TamingDecoder()

        if img_list is not None:
            img_processed_list = [
                taming_decoder.vqgan_preprocess(img) for img in img_list
            ]
            img_batch = torch.cat(img_processed_list)
        else:
            img_batch = None

        if img_batch is not None:
            lr = 0.3
        else:
            lr = 0.5

        gen_img_list, _feat_list = taming_decoder.generate_from_prompt(
            prompt=prompt,
            lr=lr,
            img_save_freq=1,
            num_generations=num_iterations,
            num_random_crops=20,
            img_batch=img_batch,
        )

    else:
        response = {
            "success": False,
            "error": "MODEL NOT RECOGNIZED",
        }
        return response

    if generate_img:
        out_img_path = f"{out_dir}/img.png"

        generated_img = gen_img_list[-1]
        generated_img.save(out_img_path)

        img_url = '/'.join(out_img_path.split('/')[1:])

    if generate_video:
        out_video_path = f"{out_dir}/video.mp4"
        writer = imageio.get_writer(out_video_path, fps=5)

        for pil_img in gen_img_list:
            img = np.array(pil_img, dtype=np.uint8)
            writer.append_data(img)

        writer.close()

        video_url = '/'.join(out_video_path.split('/')[1:])

    response = {
        'success': True,
        'imgUrl': img_url,
        'videoUrl': video_url,
    }

    return response


def story_generation(
    prompt_list,
    img_list,
    duration_list,
    model,
    num_iterations,
    resolution,
    out_dir,
):
    interp_img_list = []
    interp_feat_list = []
    for idx, prompt in enumerate(prompt_list):
        print(f"USING {model}")
        if model == 'aphantasia':
            gen_img_list, feat_list = aphantasia.generate_from_prompt(
                prompt=prompt,
                lr=0.8,
                num_generations=num_iterations,
                img_save_freq=1,
                resolution=resolution,
            )
            interp_img_list.append(gen_img_list[-1])
            interp_feat_list.append(feat_list[-1])

        elif model == 'taming':
            taming_decoder = TamingDecoder()
            if img_list is not None:
                img_sublist = [img_list[idx]]
                img_processed_list = [
                    taming_decoder.vqgan_preprocess(img) for img in img_sublist
                ]
                img_batch = torch.cat(img_processed_list)
            else:
                img_batch = None
            
            if img_batch is not None:
                lr = 0.3
            else:
                lr = 0.5
            
            gen_img_list, feat_list = taming_decoder.generate_from_prompt(
                prompt=prompt,
                lr=lr,
                img_save_freq=1,
                num_generations=num_iterations,
                num_random_crops=20,
                img_batch=img_batch,
            )

            interp_img_list.append(gen_img_list[-1])
            interp_feat_list.append(feat_list[-1])

        elif model == 'stylegan':
            stylegan = StyleGAN()
            gen_img_list, feat_list = stylegan.generate_from_prompt(
                prompt=prompt,
                lr=6e-3,
                num_generations=num_iterations,
                img_save_freq=1,
            )
            interp_img_list.append(gen_img_list[-1])
            interp_feat_list.append(feat_list[-1])

        else:
            response = {
                "success": False,
                "error": "MODEL NOT RECOGNIZED",
            }
            return response

    if model == 'aphantasia':
        interp_result_img_list = aphantasia.interpolate(
            interp_feat_list,
            duration_list,
            resolution=resolution,
        )

    elif model == 'taming':
        taming_decoder = TamingDecoder()
        interp_result_img_list = taming_decoder.interpolate(
            interp_feat_list,
            duration_list,
        )

    elif model == 'stylegan':
        stylegan = StyleGAN()
        interp_result_img_list = stylegan.interpolate(
            interp_feat_list,
            duration_list,
        )

    out_video_path = f"{out_dir}/interpolation.mp4"
    
    writer = imageio.get_writer(out_video_path, fps=25)

    for pil_img in interp_result_img_list:
        img = np.array(pil_img, dtype=np.uint8)
        writer.append_data(img)

    writer.close()
    
    video_url = '/'.join(out_video_path.split('/')[1:])

    response = {
        "success": True,
        "imgUrl": '',
        "videoUrl": video_url,
    }

    return response