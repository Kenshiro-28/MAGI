import gc
import torch
from diffusers import StableDiffusion3Pipeline, logging

IMAGE_GENERATION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

INFERENCE_STEPS = 30
RECOMMENDED_VRAM = 16 * (1024 ** 3)  # 16GB
MIN_VRAM = 8 * (1024 ** 3)  # 8GB
GUIDANCE_SCALE = 3.5
MAX_SEQUENCE_LENGTH = 256


def _load_pipeline(model: str, lora: str):
    if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= RECOMMENDED_VRAM:
        # Best quality
        pipe = StableDiffusion3Pipeline.from_pretrained(model, torch_dtype = torch.bfloat16)
        pipe.enable_model_cpu_offload()
    elif torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= MIN_VRAM:
        # For lower VRAM, use float16 and more aggressive optimizations
        pipe = StableDiffusion3Pipeline.from_pretrained(model, torch_dtype = torch.float16)
        pipe.enable_model_cpu_offload()
        pipe.enable_attention_slicing()
    else:
        # Force CPU mode for low VRAM or no CUDA
        pipe = StableDiffusion3Pipeline.from_pretrained(model, torch_dtype = torch.float32)
        pipe.to("cpu")

    if lora:
        pipe.load_lora_weights(lora)

    return pipe


def generate_image(
    prompt: str,
    negative_prompt: str,
    model: str,
    lora: str,
    image_specs: str,
    width: int,
    height: int
):
    pipe: StableDiffusion3Pipeline = None
    image = None

    try:
        logging.set_verbosity_error()

        # Load pipeline
        pipe = _load_pipeline(model, lora)

        # Add image specs
        if image_specs:
            prompt = image_specs + ". " + prompt

        # Generate image
        image = pipe(
            prompt = prompt,
            negative_prompt = negative_prompt,
            width = width,
            height = height,
            guidance_scale = GUIDANCE_SCALE,
            num_inference_steps = INFERENCE_STEPS,
            max_sequence_length = MAX_SEQUENCE_LENGTH,
        ).images[0]

        return image

    except Exception as e:
        print(IMAGE_GENERATION_ERROR + str(e))
        return None

    finally:
        # Cleanup
        pipe = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        gc.collect()


