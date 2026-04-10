import image_generation

model = "stabilityai/stable-diffusion-xl-base-1.0"
lora = "ostris/face-helper-sdxl-lora"
image_type = "4K RAW photo, high-end commercial photography"
image_specs = "50mm lens, f/8 aperture, critical focus, tangible textures, richly detailed, volumetric lighting, cinematic color grading"
negative_prompt = "lowres, blurry, out of focus, soft focus, jpeg artifacts, muddy textures, deformed, disfigured, bad proportions, bad anatomy, bad face, missing limbs, bad hands"

prompt = "giant mecha"

width = 1024
height = 1024

image = image_generation.generate_image(prompt, negative_prompt, model, lora, image_type, image_specs, width, height)

image.save("image.png")

