import torch
from diffusers import DiffusionPipeline
from diffusers import logging

STABLE_DIFFUSION_ERROR = "\n[ERROR] An exception occurred while trying to generate an image: "

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512
IMAGE_SPECS = ", 8k, intrincate, highly detailed, realistic lighting, realistic textures, vibrant colors"
NEGATIVE_PROMPT = "worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck"

def dummy_checker(images, **kwargs):
	return images, False

def generate_image(prompt, model):
	try:
		logging.set_verbosity_error()
	
		device = torch.device('cpu')

		pipe = DiffusionPipeline.from_pretrained(model, custom_pipeline = "lpw_stable_diffusion", torch_dtype = torch.float32, safety_checker = dummy_checker)
		pipe = pipe.to(device)

		prompt += IMAGE_SPECS

		image = pipe.text2img(prompt, negative_prompt = NEGATIVE_PROMPT, width = IMAGE_WIDTH, height = IMAGE_HEIGHT, max_embeddings_multiples = 3).images[0]

		return image

	except Exception as e:
		print(STABLE_DIFFUSION_ERROR + str(e)) 		
		return None


