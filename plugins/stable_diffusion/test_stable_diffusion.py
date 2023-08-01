import stable_diffusion

model = "digiplay/DreamShaper_8"

prompt = "giant mecha"

image = stable_diffusion.generate_image(prompt, model)

image.save("image.png")

