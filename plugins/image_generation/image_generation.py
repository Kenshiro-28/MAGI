import gc
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from diffusers.utils import logging

IMAGE_GENERATION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

INFERENCE_STEPS = 40
RECOMMENDED_VRAM = 24 * (1024 ** 3) 
MIN_VRAM = 12 * (1024 ** 3)
GUIDANCE_SCALE = 5.0
ALGORITHM_TYPE = "dpmsolver++"  # DPM++ 2M Karras


def _load_pipeline(model: str, lora: str):
    pipe = None

    # GPU MODE (If available)
    if torch.cuda.is_available():
        total_vram = torch.cuda.get_device_properties(0).total_memory
        
        # Check total VRAM
        if total_vram >= RECOMMENDED_VRAM:
            pipe = StableDiffusionXLPipeline.from_pretrained(model, torch_dtype=torch.float16)
            pipe.enable_model_cpu_offload()
        elif total_vram >= MIN_VRAM:
            pipe = StableDiffusionXLPipeline.from_pretrained(model, torch_dtype=torch.float16)
            pipe.enable_model_cpu_offload()
            pipe.enable_vae_tiling()
        else:
            # Fallback for weak GPUs -> CPU
            pipe = _load_cpu_pipeline(model)
            
    # CPU MODE
    else:
        pipe = _load_cpu_pipeline(model)

    # Apply Lora if needed
    if lora:
        print(f"Loading LoRA weights: {lora}...")
        pipe.load_lora_weights(lora)

    # Set scheduler
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config,
        algorithm_type=ALGORITHM_TYPE,
        use_karras_sigmas=True
    )

    return pipe


def _load_cpu_pipeline(model: str):
    print(f"Loading {model} (SDXL) in High-Quality CPU Mode (Float32)...")
    
    # Load SDXL Pipeline with strict 32-bit precision
    pipe = StableDiffusionXLPipeline.from_pretrained(
        model,
        torch_dtype=torch.float32,
        variant=None, 
        use_safetensors=True
    )

    # Force strict 32-bit casting
    pipe.to(dtype=torch.float32)
    pipe.to("cpu")

    # ENABLE TILING (Mandatory for SDXL on CPU)
    pipe.enable_vae_tiling()
    
    # Memory Optimization
    pipe.enable_attention_slicing()

    return pipe


def generate_image(
    prompt: str,
    negative_prompt: str,
    model: str,
    lora: str,
    image_type: str,
    image_specs: str,
    width: int,
    height: int
):
    pipe: StableDiffusionXLPipeline = None
    image = None

    try:
        logging.set_verbosity_error()

        # Load pipeline
        pipe = _load_pipeline(model, lora)

        # Add image type (i.e. "4K RAW photo")
        if image_type:
            prompt = image_type + ", " + prompt

        # Add image specs (i.e. "50mm lens, ...")
        if image_specs:
            prompt = prompt.removesuffix('.') + ", " + image_specs

        # Print positive and negative prompts
        print("\n" + "=" * 50)
        print("[POSITIVE PROMPT]")
        print(prompt)
        print("-" * 50)
        print("[NEGATIVE PROMPT]")
        print(negative_prompt)
        print("=" * 50 + "\n")

        # Generate image
        print(f"Generating SDXL image (Steps: {INFERENCE_STEPS}, CFG: {GUIDANCE_SCALE})...")
        image = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            guidance_scale=GUIDANCE_SCALE,
            num_inference_steps=INFERENCE_STEPS
        ).images[0]

        return image

    except Exception as e:
        print(IMAGE_GENERATION_ERROR + str(e))
        return None

    finally:
        # Cleanup
        if pipe is not None:
            del pipe

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        gc.collect()
