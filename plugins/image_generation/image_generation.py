from __future__ import annotations
import gc
import re
from pathlib import Path
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from diffusers.utils import logging
from huggingface_hub import list_repo_files, hf_hub_download
from typing import Any, Optional


IMAGE_GENERATION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

INFERENCE_STEPS = 40
RECOMMENDED_VRAM = 16 * (1024 ** 3)
GUIDANCE_SCALE = 5.0
ALGORITHM_TYPE = "dpmsolver++"  # DPM++ 2M Karras
LORA_SCALE = 0.8
MAX_IMAGE_PIXELS = 2048 ** 2
LOCAL_MODEL_PATH = Path(__file__).resolve().with_name("model.safetensors")


def _validate_dimensions(width: int, height: int):
    """Round dimensions to multiples of 8 and report adjustments."""
    # Check minimum dimensions.
    if width < 8 or height < 8:
        raise ValueError("SDXL image dimensions must be at least 8x8 pixels")

    # Round to multiples of 8.
    orig_w, orig_h = width, height
    width = (width // 8) * 8
    height = (height // 8) * 8

    # Check total pixels.
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError(
            f"Image resolution exceeds the maximum of {MAX_IMAGE_PIXELS:,} pixels"
        )

    # Report dimension adjustments.
    if width != orig_w or height != orig_h:
        print(f"[NOTE] Adjusted dimensions {orig_w}x{orig_h} → {width}x{height} (SDXL VAE requirement)")

    return width, height


def _is_safetensors_file(files: list[str]) -> bool:
    """Check for a root-level Safetensors file."""
    return any(
        f.endswith(".safetensors") and "/" not in f
        for f in files
    )


def _has_component_safetensors(
    files: list[str],
    variant: Optional[str] = None
) -> bool:
    """Check for the expected SDXL Diffusers Safetensors component files."""
    components = {"unet", "vae", "text_encoder", "text_encoder_2"}
    found: set[str] = set()

    for file in files:
        if "/" not in file or not file.endswith(".safetensors"):
            continue

        component, filename = file.split("/", 1)

        if component not in components:
            continue

        base = (
            "diffusion_pytorch_model"
            if component in {"unet", "vae"}
            else "model"
        )
        prefix = f"{base}.{variant}" if variant else base

        if filename == f"{prefix}.safetensors" or (
            filename.startswith(f"{prefix}-")
            and filename.endswith(".safetensors")
        ):
            found.add(component)

    return found == components


def _select_safetensors_file(
    files: list[str],
    torch_dtype: torch.dtype
) -> str:
    root_files = [
        f for f in files
        if f.endswith(".safetensors") and "/" not in f
    ]

    if not root_files:
        raise ValueError("No root .safetensors checkpoint found")

    # A repository with one checkpoint is unambiguous.
    if len(root_files) == 1:
        return root_files[0]

    precision = "fp16" if torch_dtype == torch.float16 else "fp32"
    matches = [
        f for f in root_files
        if precision in f.lower()
    ]

    if len(matches) == 1:
        return matches[0]

    # Prefer an untagged checkpoint when no unique precision match exists.
    precision_tags = (
        "fp16",
        "fp32",
        "bf16",
        "fp8",
        "float16",
        "float32"
    )
    generic = [
        f for f in root_files
        if not any(tag in f.lower() for tag in precision_tags)
    ]

    if len(generic) == 1:
        return generic[0]

    raise ValueError(
        f"Could not uniquely select a {precision} checkpoint. "
        f"Available checkpoints: {root_files}"
    )


def _load_pipeline(model: str, torch_dtype: torch.dtype):
    if LOCAL_MODEL_PATH.is_file():
        print(f"Loading base pipeline: {LOCAL_MODEL_PATH}")
        print(f" → Detected local single-file Safetensors checkpoint (overrides configured model: {model})")
        return StableDiffusionXLPipeline.from_single_file(
            str(LOCAL_MODEL_PATH),
            dtype=torch_dtype,
            add_watermarker=False
        )

    print(f"Loading base pipeline: {model}")
    files = list_repo_files(model)

    if (
        "model_index.json" in files
        and torch_dtype == torch.float16
        and _has_component_safetensors(files, variant="fp16")
    ):
        print(" → Detected Diffusers FP16 Safetensors format")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model,
            variant="fp16",
            dtype=torch_dtype,
            use_safetensors=True,
            add_watermarker=False
        )

    elif "model_index.json" in files and _has_component_safetensors(files):
        print(" → Detected Diffusers Safetensors format")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model,
            dtype=torch_dtype,
            use_safetensors=True,
            add_watermarker=False
        )

    elif _is_safetensors_file(files):
        print(" → Detected single-file Safetensors checkpoint")

        safetensors_file = _select_safetensors_file(files, torch_dtype)

        local_path = hf_hub_download(
            repo_id=model,
            filename=safetensors_file
        )

        pipe = StableDiffusionXLPipeline.from_single_file(
            local_path,
            config=model if "model_index.json" in files else None,
            dtype=torch_dtype,
            add_watermarker=False
        )

    elif "model_index.json" in files:
        print(" → Detected standard Diffusers format (Safetensors unavailable)")
        pipe = StableDiffusionXLPipeline.from_pretrained(
            model,
            dtype=torch_dtype,
            add_watermarker=False
        )

    else:
        raise ValueError(
            f"Could not detect a supported SDXL model format in {model}"
        )

    return pipe


def _load_cpu_pipeline(model: str):
    selected_model = LOCAL_MODEL_PATH if LOCAL_MODEL_PATH.is_file() else model
    print(f"Loading {selected_model} (SDXL) in High-Quality CPU Mode (Float32)...")
    pipe = _load_pipeline(model, torch.float32)
    pipe.to("cpu")

    return pipe


def _load_gpu_pipeline(model: str, lora: Optional[str] = None):
    cuda_available = torch.cuda.is_available()

    if cuda_available:
        pipe = _load_pipeline(model, torch.float16)
    else:
        pipe = _load_cpu_pipeline(model)

    # Apply LoRA before device placement or CPU offloading
    if lora:
        print(f"Loading LoRA weights: {lora}...")
        pipe.load_lora_weights(lora, adapter_name="default")
        pipe.set_adapters(["default"], adapter_weights=[LORA_SCALE])

    # Select execution mode using available VRAM
    if cuda_available:
        gpu_id = torch.cuda.current_device()
        free_vram, _ = torch.cuda.mem_get_info(device=gpu_id)

        if free_vram >= RECOMMENDED_VRAM:
            pipe.to(f"cuda:{gpu_id}")
        else:
            pipe.enable_model_cpu_offload(gpu_id=gpu_id)

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
    lora: Optional[str],
    image_type: str,
    image_specs: str,
    width: int,
    height: int
):
    pipe: Optional[Any] = None
    image = None

    try:
        logging.set_verbosity_error()

        # Check image dimensions
        width, height = _validate_dimensions(width, height)

        # Load pipeline
        pipe = _load_gpu_pipeline(model, lora)

        # Add image type (i.e. "RAW photo")
        if image_type:
            prompt = image_type + ", " + prompt

        # Add image specs after removing trailing periods
        if image_specs:
            prompt = re.sub(r"(?:\s*\.)+\s*$", "", prompt) + ", " + image_specs

        # Remove repeated commas
        prompt = re.sub(r"\s*,(?:\s*,)+\s*", ", ", prompt)

        # Remove a trailing comma at the very end
        prompt = re.sub(r",\s*$", "", prompt)

        # Collapse runs of multiple spaces
        prompt = re.sub(r" {2,}", " ", prompt)

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

        gc.collect()

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

