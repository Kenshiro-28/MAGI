import stable_diffusion

model = "emilianJR/epiCRealism"

prompt = "giant mecha"
image_specs = "photo"
negative_prompt = "duplicate, mutilated, extra fingers, mutated hands, mutation, deformed, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, poorly drawn face"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

