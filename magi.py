import openai
import os
import sys

MOD_FILE_PATH = "mod.txt"
openai.api_key = os.getenv('OPENAI_API_KEY')

SYSTEM_COLOR = "\033[91m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

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


def printSystemText(text):
	print(SYSTEM_COLOR + text + END_COLOR)	

	
def printMagiText(text):
	print(MAGI_COLOR + text + END_COLOR)

	
def userInput():
	prompt = input(USER_COLOR + "\n$ ")
	
	return prompt		


# Main logic

context = []

with open(MOD_FILE_PATH) as modFile:
	mod = modFile.read().strip()
	printSystemText("\nMod: " + mod)

printMagiText("\nMAGI: Greetings")

while True:
	prompt = userInput()
	response = send_prompt(mod, prompt, context)
	printMagiText("\nMAGI: " + response)	
	

