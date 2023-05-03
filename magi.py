import openai
import os
import sys

MOD_FILE_PATH = "mod.txt"
openai.api_key = os.getenv('OPENAI_API_KEY')


def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):

    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )

    return response.choices[0].message["content"]


def send_prompt(mod, prompt, context):

	modPrompt = mod + prompt
	context.append({'role':'user', 'content':f"{modPrompt}"})
#	print(f"{modPrompt}")

	response = get_completion_from_messages(context) 

	context.append({'role':'assistant', 'content':f"{response}"})

	return response


# Main logic
context = []

with open(MOD_FILE_PATH) as modFile:
	mod = modFile.read().strip()
	print(mod)

while True:
	prompt = input("$ ")
	response = send_prompt(mod, prompt, context)
	print(response)	
	

