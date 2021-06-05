import os
import base64
from io import BytesIO
from typing import *

from flask import Flask, request, jsonify
from rq import Queue
from rq.job import Job
from PIL import Image

from worker import conn
from server_utils import single_generation, story_generation

app = Flask(__name__)
app.app_context().push()

q = Queue(connection=conn)


def base64_to_PIL(base64_encoding: str):
    return Image.open(BytesIO(base64.b64decode(base64_encoding)))


def PIL_to_base64(img):
    buffer = BytesIO()
    # img = remove_background(img)
    img.save(buffer, format='PNG')
    buffer.seek(0)
    data_uri = base64.b64encode(buffer.read()).decode('ascii')

    return data_uri


@app.route("/results/<job_key>", methods=['GET'])
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)

    print(job.is_finished)
    if job.is_finished:
        response = job.result
        response['finished'] = "yup"
    else:
        response = {
            "finished": "Not yet bro!",
            "status": 202,
        }

    json_response = jsonify(response)
    json_response.headers.add('Access-Control-Allow-Origin', '*')

    return json_response


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
    job_id = -1

    if request.args.get('storyGeneration') == 'true':
        prompt_list = request.args.get('promptArray').split(',')
        duration_list = [
            float(dur) for dur in request.args.get('durationArray').split(',')
        ]
        prompt_list = ['_'.join(prompt.split(' ')) for prompt in prompt_list]

        out_dir = f"public/generations/{'-'.join(prompt_list)}"
        os.makedirs(out_dir, exist_ok=True)

        args = (
            prompt_list,
            duration_list,
            model,
            num_iterations,
            resolution,
            out_dir,
        )

        job = q.enqueue_call(
            func=story_generation,
            args=args,
            result_ttl=5000,
        )
        job_id = job.get_id()
        print(f"JOB ID: {job_id}")

    else:
        img_base64_array = request.args.get('imgArray')
        if img_base64_array is not None:
            img_base64_list = [
                f"data:{img}" for img in img_base64_array.split('data:')[1::]
            ]
            img_list = [
                base64_to_PIL(img.split('base64')[1])
                for img in img_base64_list
            ]

        prompt = request.args.get('prompt')
        generate_video = True if request.args.get(
            'videoGeneration') == 'true' else False
        generate_img = True if request.args.get(
            'imageGeneration') == 'true' else False
        out_dir = f"public/generations/{prompt}"
        os.makedirs(out_dir, exist_ok=True)

        args = (
            prompt,
            img_list,
            model,
            num_iterations,
            resolution,
            out_dir,
            generate_img,
            generate_video,
        )

        # single_generation(*args)

        job = q.enqueue_call(
            func=single_generation,
            args=args,
            result_ttl=5000,
        )
        job_id = job.get_id()
        print(f"JOB ID: {job_id}")

    response = jsonify(
        success=True,
        jobId=job_id,
    )

    response.headers.add('Access-Control-Allow-Origin', '*')

    return response


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
    )
