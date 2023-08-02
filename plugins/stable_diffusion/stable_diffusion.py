import torch
from diffusers import StableDiffusionPipeline
from diffusers import logging

STABLE_DIFFUSION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

IMAGE_SPECS = ", 8k, intrincate, highly detailed, realistic lighting, realistic textures, vibrant colors"

def generate_image(prompt, model):
	try:
		logging.set_verbosity_error()
		device = torch.device('cpu')

		pipe = StableDiffusionPipeline.from_pretrained(model, torch_dtype=torch.float32, safety_checker = None)
		pipe.to(device)

		with torch.no_grad():
			image = pipe(prompt + IMAGE_SPECS).images[0]

		return image

	except Exception as e:
		print(STABLE_DIFFUSION_ERROR + str(e)) 		
		return None


