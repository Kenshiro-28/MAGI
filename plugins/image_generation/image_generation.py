import torch
from diffusers import FluxPipeline
from diffusers import logging

IMAGE_GENERATION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

INFERENCE_STEPS = 50

MIN_VRAM = 8 * 1024 * 1024 * 1024  # 8GB in bytes

GUIDANCE_SCALE = 3.5


def generate_image(prompt, model, lora, image_specs, width, height):
    try:
        logging.set_verbosity_error()

        # Check if CUDA is available and there is enough VRAM
        if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= MIN_VRAM:
            pipe = FluxPipeline.from_pretrained(model, torch_dtype = torch.bfloat16)
            pipe.enable_model_cpu_offload()
        else:
            pipe = FluxPipeline.from_pretrained(model)
            pipe.to("cpu")

        if (lora):
            pipe.load_lora_weights(lora)

        if image_specs:
            prompt = image_specs + ", " + prompt
        
        image = pipe(prompt, width = width, height = height, guidance_scale = GUIDANCE_SCALE, num_inference_steps = INFERENCE_STEPS, max_sequence_length = 512).images[0]

        return image

    except Exception as e:
        print(IMAGE_GENERATION_ERROR + str(e))
        return None


