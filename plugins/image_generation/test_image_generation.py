import image_generation

model = "stabilityai/stable-diffusion-3.5-large"
lora = ""
image_specs = "high quality, detailed"
negative_prompt = "low quality, blurry, bad anatomy, watermark"

prompt = "giant mecha"

width = 1024
height = 1024

image = image_generation.generate_image(prompt, negative_prompt, model, lora, image_specs, width, height)

image.save("image.png")

