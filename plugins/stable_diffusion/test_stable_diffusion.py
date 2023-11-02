import stable_diffusion

model = "digiplay/AbsoluteReality_v1.8.1"

prompt = "giant mecha"
image_specs = "8K UHD"
negative_prompt = "lowres"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

