import openai
import os

MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.7
SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. The mission data will be saved in mission.txt\n"
PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_FILE_PATH = "mission.txt"
MISSION_COMMAND = "M"
MISSION_PROMPT = "Divide this mission in a list of independent tasks to be executed by you, one task per line, without subtasks. Write ONLY the list of tasks. MISSION: "
NEW_MISSION_TEXT = "\n----- Mission -----\n\n"

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

openai.api_key = os.getenv('OPENAI_API_KEY')

def get_completion_from_messages(messages, model = MODEL, temperature = TEMPERATURE):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )

    return response.choices[0].message["content"]


def send_prompt(primeDirectives, prompt, context):
	command = primeDirectives + prompt
	context.append({'role':'user', 'content':f"{command}"})

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
	

def runMission(primeDirectives, prompt, context):
	mission = send_prompt(primeDirectives, MISSION_PROMPT + prompt, context)
	
	missionTitle = NEW_MISSION_TEXT + mission
	
	printSystemText(missionTitle)
	saveMissionData(missionTitle)
	
	# Start new context
	context = []
	
	# Remember user prompt
	context.append({'role':'user', 'content':f"{prompt}"})	

	# Remove blank lines
	mission = '\n'.join(line for line in mission.splitlines() if line.strip())	

	for task in mission.split('\n'):
		systemText = "\n" + task 
		printSystemText(systemText)
		response = send_prompt(primeDirectives, task, context)		
		magiText = "\n" + response
		printMagiText(magiText)
		saveMissionData(systemText + "\n" + magiText)
		
	
def runPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		response = send_prompt(primeDirectives, prompt, context)
		printMagiText("\n" + response)	


def switchMissionMode(missionMode):
	missionMode = not missionMode

	if missionMode == True:
		printSystemText("\nMission mode enabled")
	else:
		printSystemText("\nMission mode disabled")
		
	return missionMode


def saveMissionData(text):
    with open(MISSION_FILE_PATH, 'a') as missionFile:
        missionFile.write(text + "\n")

# Main logic
context = []
missionMode = False

with open(PRIME_DIRECTIVES_FILE_PATH) as primeDirectivesFile:
	primeDirectives = primeDirectivesFile.read().strip()
	printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives)

printSystemText(SYSTEM_HINT_TEXT)

# Main loop
while True:
	prompt = userInput()
	
	command = prompt.split()[0]
	
	if command.upper() == MISSION_COMMAND:
		missionMode = switchMissionMode(missionMode)
	else:
		runPrompt(primeDirectives, prompt, context, missionMode)
	
 
