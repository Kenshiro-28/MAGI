import openai
import os

MOD_FILE_PATH = "mod.txt"
MISSION_FILE_PATH = "mission.txt"
MISSION_COMMAND = "M"
TASK_DELIMITER = "."
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
	print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)	

	
def printMagiText(text):
	print(END_COLOR + MAGI_COLOR + text + END_COLOR)

	
def userInput():
	prompt = input(USER_COLOR + "\n$ ")
	
	return prompt		


def saveTask(task, taskArray):
	if task != "":
		taskArray.append(task.strip())
	

def executeMission(missionPrompt):

	taskArray = []
	task = ""

	for char in missionPrompt:

		if char == TASK_DELIMITER:
			saveTask(task, taskArray)
			task = ""
		else:
			task += char

	# Append the last task
	saveTask(task, taskArray)
	
	printSystemText("\n----- Mission -----\n")

	taskNumber = 1

	for task in taskArray:
	
		printSystemText("Task " + str(taskNumber) + ": " + task)
		taskNumber += 1
		

# Main logic
context = []

with open(MOD_FILE_PATH) as modFile:
	mod = modFile.read().strip()
	printSystemText("\nMod: " + mod)

printSystemText("\nHint: To execute a mission, type the letter 'm' and then the mission tasks. Tasks should be separated by a period, such as 'This is task 1. This is task 2.'")

# Main loop
while True:
	prompt = userInput()
	
	command = prompt.split()[0]
	
	if command.upper() == MISSION_COMMAND:
		missionPrompt = ' '.join(prompt.split()[1:])
		executeMission(missionPrompt)
	else:
		response = send_prompt(mod, prompt, context)
		printMagiText("\nMAGI: " + response)	
	

