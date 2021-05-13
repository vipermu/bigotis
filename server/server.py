import os
from typing import *

import imageio
import numpy as np
from flask import Flask, request, jsonify

from models.dalle_decoder import generate_from_prompt

app = Flask(__name__)


@app.route(
    "/generate",
    methods=[
        "GET",
    ],
)
def generate():
    prompt = request.args.get('prompt')
    model = request.args.get('model')
    generate_video = True if request.args.get('videoGeneration')=='true' else False
    generate_img = True if request.args.get('imageGeneration')=='true' else False

    img_url = ''
    video_url = ''
    
    out_dir = f"public/generations/{prompt}"

    if model == 'dalle':
        gen_img_list = generate_from_prompt(
            prompt=prompt,
            lr=0.9,
            num_generations=10,
            img_save_freq=1,
        )

    elif model == 'aphantasia':
        pass

    else:
        response = jsonify(
            success=False,
            error="MODEL NOT RECOGNIZED",
        )
        return response


    if generate_img:
        os.makedirs(out_dir, exist_ok=True)
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

    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


if __name__ == "__main__":
    app.run(port=8000, )
