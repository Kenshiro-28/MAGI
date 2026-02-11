import image_generation

model = "SG161222/RealVisXL_V5.0"
lora = ""
image_type = "4K RAW photo"
image_specs = "50mm lens, f/8 aperture, high-end commercial photography, critical focus, tangible textures, richly detailed, volumetric lighting, cinematic color grading"
negative_prompt = "lowres, deformed, bad anatomy, bad proportions, gross proportions, jpeg artifacts, muddy textures, blurry, out of focus, soft focus, poorly drawn face, lifeless eyes, colored sclera"

prompt = "giant mecha"

width = 1024
height = 1024

image = image_generation.generate_image(prompt, negative_prompt, model, lora, image_type, image_specs, width, height)

image.save("image.png")

