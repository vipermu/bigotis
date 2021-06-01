import os
from typing import *

import imageio
import numpy as np
from flask import Flask, request, jsonify

from models.taming import taming_decoder
from models import dalle_decoder, aphantasia, stylegan

app = Flask(__name__)


def single_generation(
    prompt,
    model,
    num_iterations,
    resolution,
    out_dir,
    generate_img,
    generate_video,
):
    img_url = ''
    video_url = ''

    if model == 'dalle':
        gen_img_list = dalle_decoder.generate_from_prompt(
            prompt=prompt,
            lr=0.7,
            num_generations=num_iterations,
            img_save_freq=1,
        )

    elif model == 'aphantasia':
        gen_img_list, feat_list = aphantasia.generate_from_prompt(
            prompt=prompt,
            lr=0.9,
            num_generations=num_iterations,
            img_save_freq=1,
            resolution=resolution,
        )
    elif model == 'stylegan':
        gen_img_list = stylegan.generate_from_prompt(
            prompt=prompt,
            lr=1e-2,
            num_generations=num_iterations,
            img_save_freq=1,
        )
    elif model == 'taming':
        gen_img_list = taming_decoder.generate_from_prompt(
            prompt=prompt,
            lr=0.5,
            img_save_freq=1,
            num_generations=num_iterations,
            num_random_crops=20,
            img_batch=None,
        )

    else:
        response = jsonify(
            success=False,
            error="MODEL NOT RECOGNIZED",
        )
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
            img = np.array(pil_img)
            writer.append_data(img)

        writer.close()

        video_url = '/'.join(out_video_path.split('/')[1:])

    response = jsonify(
        success=True,
        imgUrl=img_url,
        videoUrl=video_url,
    )

    return response


def story_generation(
    prompt_list,
    duration_list,
    model,
    num_iterations,
    resolution,
    out_dir,
):
    interp_img_list = []
    interp_feat_list = []
    for prompt in prompt_list:
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
        else:
            response = jsonify(
                success=False,
                error="MODEL NOT RECOGNIZED",
            )
            return response

    if model == 'aphantasia':
        interp_result_img_list = aphantasia.interpolate(
            interp_feat_list,
            duration_list,
            resolution=resolution,
        )

    out_video_path = f"{out_dir}/interpolation.mp4"
    writer = imageio.get_writer(out_video_path, fps=25)

    for pil_img in interp_result_img_list:
        img = np.array(pil_img)
        writer.append_data(img)

    writer.close()

    video_url = '/'.join(out_video_path.split('/')[1:])

    response = jsonify(
        success=True,
        imgUrl='',
        videoUrl=video_url,
    )

    return response


@app.route(
    "/generate",
    methods=[
        "GET",
    ],
)
def generate():
    num_iterations = int(request.args.get('numIterations'))
    resolution = request.args.get('resolution')
    model = request.args.get('model')

    if request.args.get('storyGeneration') == 'true':
        prompt_list = request.args.get('promptArray').split(',')
        duration_list = [
            float(dur) for dur in request.args.get('durationArray').split(',')
        ]
        prompt_list = ['_'.join(prompt.split(' ')) for prompt in prompt_list]

        out_dir = f"public/generations/{'-'.join(prompt_list)}"
        os.makedirs(out_dir, exist_ok=True)

        response = story_generation(
            prompt_list,
            duration_list,
            model,
            num_iterations,
            resolution,
            out_dir,
        )
    else:
        prompt = request.args.get('prompt')
        generate_video = True if request.args.get(
            'videoGeneration') == 'true' else False
        generate_img = True if request.args.get(
            'imageGeneration') == 'true' else False
        out_dir = f"public/generations/{prompt}"
        os.makedirs(out_dir, exist_ok=True)

        response = single_generation(
            prompt,
            model,
            num_iterations,
            resolution,
            out_dir,
            generate_img,
            generate_video,
        )

    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
    )
