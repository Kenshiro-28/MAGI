import gc
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from diffusers.utils import logging
from huggingface_hub import list_repo_files, hf_hub_download

IMAGE_GENERATION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

INFERENCE_STEPS = 40
RECOMMENDED_VRAM = 24 * (1024 ** 3) 
GUIDANCE_SCALE = 5.0
ALGORITHM_TYPE = "dpmsolver++"  # DPM++ 2M Karras
LORA_SCALE = 0.8


def _get_repo_files(repo_id: str):
    try:
        return list_repo_files(repo_id)

    except Exception:
        return []


def _validate_dimensions(width: int, height: int):
    """SDXL requires multiples of 8. Auto-adjust + warn if changed."""
    orig_w, orig_h = width, height
    width = (width // 8) * 8
    height = (height // 8) * 8

    if width != orig_w or height != orig_h:
        print(f"[NOTE] Adjusted dimensions {orig_w}x{orig_h} → {width}x{height} (SDXL VAE requirement)")

    return width, height


def _is_safetensors_file(files: list) -> bool:
    """Auto-detect single-file checkpoints vs full Diffusers format"""
    try:
        has_safetensors = any(f.endswith('.safetensors') and '/' not in f for f in files)
        return has_safetensors

    except Exception:
        return False


def _load_pipeline(model: str, torch_dtype: torch.dtype):
    print(f"Loading base pipeline: {model}")
    files = _get_repo_files(model)

    if _is_safetensors_file(files):
        print(" → Detected single-file checkpoint")
        safetensors_file = next((f for f in files if f.endswith('.safetensors') and '/' not in f), None)
        if not safetensors_file:
            raise ValueError(f"No root .safetensors file found in {model}")

        # Robust download (avoids URL parsing bugs)
        local_path = hf_hub_download(
            repo_id=model,
            filename=safetensors_file,
            token=True
        )
        pipe = StableDiffusionXLPipeline.from_single_file(
            local_path,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            safety_checker=None,
            feature_extractor=None,
            requires_safety_checker=False
        )
        pipe.safety_checker = None
        pipe.feature_extractor = None
    else:
        print(" → Detected standard Diffusers format")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model,
            torch_dtype=torch_dtype,
            use_safetensors=True,
            variant=None,
            load_safety_checker=False,
            token=True
        )

    return pipe


def _load_cpu_pipeline(model: str):
    print(f"Loading {model} (SDXL) in High-Quality CPU Mode (Float32)...")
    pipe = _load_pipeline(model, torch.float32)
    pipe.to("cpu")
    pipe.to(dtype=torch.float32)
    pipe.vae.enable_tiling()
    pipe.vae.enable_slicing()
    pipe.enable_attention_slicing()

    return pipe


def _load_gpu_pipeline(model: str, lora: str = None):
    if torch.cuda.is_available():
        total_vram = torch.cuda.get_device_properties(0).total_memory
        pipe = _load_pipeline(model, torch.float16)

        # Check total VRAM
        if total_vram >= RECOMMENDED_VRAM:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
            pipe.vae.enable_tiling()
            pipe.vae.enable_slicing()
    else:
        pipe = _load_cpu_pipeline(model)

    # Apply LoRA if needed
    if lora:
        print(f"Loading LoRA weights: {lora}...")
        pipe.load_lora_weights(lora, adapter_name="default")
        pipe.set_adapters(["default"], adapter_weights=[LORA_SCALE])

    # Set scheduler
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config,
        algorithm_type=ALGORITHM_TYPE,
        use_karras_sigmas=True
    )

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

        # Check image dimensions
        width, height = _validate_dimensions(width, height)

        # Load pipeline
        pipe = _load_gpu_pipeline(model, lora)

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
