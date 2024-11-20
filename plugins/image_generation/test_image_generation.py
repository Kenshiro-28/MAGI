import image_generation

model = "black-forest-labs/FLUX.1-dev"
lora = "0x000001/Anti-blur_Flux_Lora"

prompt = "giant mecha"
image_specs = "photograph"

width = 512
height = 512

image = image_generation.generate_image(prompt, model, lora, image_specs, width, height)

image.save("image.png")

