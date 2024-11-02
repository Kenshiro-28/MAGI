import image_generation

model = "black-forest-labs/FLUX.1-dev"
lora = "0x000001/Anti-blur_Flux_Lora"

prompt = "giant mecha"
image_specs = "photograph"

image = image_generation.generate_image(prompt, model, lora, image_specs)

image.save("image.png")

