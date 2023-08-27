import stable_diffusion

model = "digiplay/AbsoluteReality_v1.8.1"

prompt = "giant mecha"
image_specs = "8k, photo, hyperdetailed, dramatic lighting, realistic textures, vibrant colors"
negative_prompt = "duplicate, mutilated, mutation, deformed, bad anatomy, bad proportions, gross proportions, unnatural body, unnatural pose, malformed limbs, extra limbs, floating limbs, cloned face, disfigured, robot eyes, asymmetrical eyes, deformed iris, deformed pupils, cross-eyed, squinting, missing arms, bad hands, extra fingers, fused fingers, missing legs, bad feet, extra toes, fused toes, jpeg artifacts, watermark, text, signature"

image = stable_diffusion.generate_image(prompt, model, image_specs, negative_prompt)

image.save("image.png")

