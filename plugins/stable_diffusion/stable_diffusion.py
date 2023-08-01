import torch
from diffusers import StableDiffusionPipeline
from diffusers import logging

IMAGE_SPECS = ", 8k, intrincate, highly detailed, realistic lighting, realistic textures, vibrant colors"

def generate_image(prompt, model):
	logging.set_verbosity_error()
	device = torch.device('cpu')

	pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float32, safety_checker = None)
	pipe.to(device)

	with torch.no_grad():
		image = pipe(prompt + IMAGE_SPECS).images[0]

	return image


