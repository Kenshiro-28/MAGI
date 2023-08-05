import stable_diffusion

model = "digiplay/DreamShaper_8"

prompt = "giant mecha"
image_specs = "8k, intrincate, highly detailed, realistic lighting, realistic textures, vibrant colors"
negative_prompt = "BadDream, (UnrealisticDream:1.3)"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

