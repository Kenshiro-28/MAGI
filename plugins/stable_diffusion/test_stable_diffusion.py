import stable_diffusion

model = "emilianJR/epiCRealism"

prompt = "giant mecha"
image_specs = "photo, hyperdetailed"
negative_prompt = "cross-eyed, disjoined, squinting, deformed, distorted, disfigured, text, signature, logo, low quality, worst quality, mutated hands and fingers, missing fingers, additional fingers"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

