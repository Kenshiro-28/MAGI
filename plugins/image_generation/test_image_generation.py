import image_generation

model = "black-forest-labs/FLUX.1-dev"

prompt = "giant mecha"
image_specs = "UHD"

image = image_generation.generate_image(prompt, model, image_specs)

image.save("image.png")

