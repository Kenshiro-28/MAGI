import stable_diffusion

model = "digiplay/AbsoluteReality_v1.8.1"

prompt = "giant mecha"
image_specs = "8k, photo, hyperdetailed, realistic lighting, realistic textures, vibrant colors"
negative_prompt = "duplicate, mutilated, mutation, deformed, bad anatomy, bad proportions, gross proportions, malformed limbs, extra limbs, floating limbs, cloned face, disfigured, cross-eyed, squinting, missing arms, bad hands, extra fingers, fused fingers, missing legs, bad feet, extra toes, fused toes, watermark, text, signature"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

