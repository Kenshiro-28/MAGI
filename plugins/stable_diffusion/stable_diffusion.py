import torch
from diffusers import DiffusionPipeline, KDPM2DiscreteScheduler
from diffusers import logging

STABLE_DIFFUSION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 768

INFERENCE_STEPS = 50

def dummy_checker(images, **kwargs):
    return images, False

def generate_image(prompt, model, image_specs, negative_prompt):
    try:
        logging.set_verbosity_error()
    
        pipe = DiffusionPipeline.from_pretrained(model, custom_pipeline = "lpw_stable_diffusion", safety_checker = dummy_checker)
        pipe.scheduler = KDPM2DiscreteScheduler.from_config(pipe.scheduler.config, use_karras_sigmas = True, algorithm_type="sde-dpmsolver++")

        prompt = image_specs + ", " + prompt

        image = pipe.text2img(prompt, negative_prompt = negative_prompt, width = IMAGE_WIDTH, height = IMAGE_HEIGHT, max_embeddings_multiples = 3, num_inference_steps = INFERENCE_STEPS).images[0]

        return image

    except Exception as e:
        print(STABLE_DIFFUSION_ERROR + str(e))         
        return None


