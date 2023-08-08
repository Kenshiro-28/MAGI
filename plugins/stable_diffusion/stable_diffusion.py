import torch
from diffusers import DiffusionPipeline
from diffusers import logging

STABLE_DIFFUSION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 768

def dummy_checker(images, **kwargs):
	return images, False

def generate_image(prompt, model, image_specs, negative_prompt):
	try:
		logging.set_verbosity_error()
	
		device = torch.device('cpu')

		pipe = DiffusionPipeline.from_pretrained(model, custom_pipeline = "lpw_stable_diffusion", torch_dtype = torch.float32, safety_checker = dummy_checker)
		pipe = pipe.to(device)

		prompt += ", " + image_specs

		image = pipe.text2img(prompt, negative_prompt = negative_prompt, width = IMAGE_WIDTH, height = IMAGE_HEIGHT, max_embeddings_multiples = 3).images[0]

		return image

	except Exception as e:
		print(STABLE_DIFFUSION_ERROR + str(e)) 		
		return None


