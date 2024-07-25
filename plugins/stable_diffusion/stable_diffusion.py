import torch
from diffusers import DiffusionPipeline, KDPM2DiscreteScheduler
from diffusers import logging

STABLE_DIFFUSION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 768

INFERENCE_STEPS = 50

MIN_VRAM = 4 * 1024 * 1024 * 1024  # 4GB in bytes


def dummy_checker(images, **kwargs):
    return images, False


def generate_image(prompt, model, image_specs, negative_prompt):
    try:
        logging.set_verbosity_error()
        
        # Check if CUDA is available and there is enough VRAM
        if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= MIN_VRAM:
            device = "cuda"
        else:
            device = "cpu"
        
        pipe = DiffusionPipeline.from_pretrained(model, custom_pipeline = "lpw_stable_diffusion", safety_checker = dummy_checker)
        pipe = pipe.to(device)
        pipe.scheduler = KDPM2DiscreteScheduler.from_config(pipe.scheduler.config, use_karras_sigmas = True, algorithm_type="sde-dpmsolver++")
        
        prompt = image_specs + ", " + prompt
        
        image = pipe.text2img(prompt, negative_prompt = negative_prompt, width = IMAGE_WIDTH, height = IMAGE_HEIGHT, max_embeddings_multiples = 3, num_inference_steps = INFERENCE_STEPS).images[0]

        return image

    except Exception as e:
        print(STABLE_DIFFUSION_ERROR + str(e))         
        return None


