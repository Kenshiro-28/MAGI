'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 2.04
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

import openai
import os
import sys
import copy
import time
from plugins import web

MODEL = "gpt-3.5-turbo"
CONTEXT_SIZE = 4 # Number of messages to remember
TEMPERATURE = 1
SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_FILE_PATH = "mission.txt"
MISSION_PROMPT = "Divide this mission in a list of independent tasks to be executed by you, one task per line, without subtasks. Write ONLY the list of tasks. MISSION: "
NEW_MISSION_TEXT = "\n\n----- Mission -----\n\n"
MISSION_MODE_ENABLED_TEXT = "\nMission mode enabled"
MISSION_MODE_DISABLED_TEXT = "\nMission mode disabled"
MODEL_TEXT = "\nModel: "
GENERATE_WEB_QUERY_TEXT = "Generate a query for google search to get information about this question, write only the query: "
BROWSE_INTERNET_QUERY_TEXT = "Tell me if you need updated information from the internet to do this task, write only YES or NO: "
WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
SUMMARIZE_TEXT = "\nRemove information from the above text that is not relevant to PROMPT. Please also remove any references to this website or other websites. Then rewrite it in a professional style. PROMPT = "
TASK_COMPLETED_TEXT = "Tell me if this task has been completed, write only YES or NO: "

MODEL_ERROR_TEXT = "\n[ERROR] An exception occurred while trying to get a response from the model: "
MODEL_ERROR_SLEEP_TIME = 5

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 500

GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

MISSION_COMMAND = "M"
EXIT_COMMAND = "EXIT"

openai.api_key = os.getenv('OPENAI_API_KEY')


def split_text_in_blocks(text):
	index = 0
	blockArray = []
	
	wordList = text.split()

	while index < len(wordList):
		limit = index + TEXT_BLOCK_WORDS
		block = " ".join(wordList[index:limit])
		blockArray.append(block)
		index += TEXT_BLOCK_WORDS

	return blockArray


def get_completion_from_messages(messages, model = MODEL, temperature = TEMPERATURE):
	try:
		response = openai.ChatCompletion.create(
		    model=model,
		    messages=messages,
		    temperature=temperature, # this is the degree of randomness of the model's output
		)

		return response.choices[0].message["content"]
		
	except Exception as e:
		printSystemText(MODEL_ERROR_TEXT + str(e), False) 
		time.sleep(MODEL_ERROR_SLEEP_TIME)				

		return get_completion_from_messages(messages, model = MODEL, temperature = TEMPERATURE)


def send_prompt(primeDirectives, prompt, context):
	command = primeDirectives + "\n" + prompt
	context.append({'role':'user', 'content':f"{command}"})

	response = get_completion_from_messages(context) 

	context.append({'role':'assistant', 'content':f"{response}"})

	# Check context size
	contextSize = len(context)
	
	while contextSize > CONTEXT_SIZE:
		context.pop(0)
		contextSize = len(context)		

	return response


def printSystemText(text, missionMode):
	print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)
	
	if missionMode == True:
		saveMissionData(text)	

	
def printMagiText(text, missionMode):
	print(END_COLOR + MAGI_COLOR + text + END_COLOR)
	
	if missionMode == True:
		saveMissionData(text)		


def saveMissionData(text):
	with open(MISSION_FILE_PATH, 'a') as missionFile:
		missionFile.write(text + "\n")

	
def userInput(missionMode):
	sys.stdin.flush()

	prompt = input(USER_COLOR + "\n$ ")
	
	if missionMode == True:
		saveMissionData(prompt)	
	
	return prompt		


def runMission(primeDirectives, prompt, context):
	mission = send_prompt(primeDirectives, MISSION_PROMPT + prompt, context)
	
	missionTitle = NEW_MISSION_TEXT + mission + "\n"
	
	printSystemText(missionTitle, True)
	
	# Remove blank lines
	mission = [line for line in mission.splitlines() if line.strip()]

	for task in mission:
		taskCompleted = False

		printSystemText("\n" + task, True)
		
		while taskCompleted == False:
			runPrompt(primeDirectives, task, context, True)		
			
			auxContext = copy.deepcopy(context)
						
			taskCompleted = isTaskCompleted(primeDirectives, task, auxContext)
		

def webSearch(primeDirectives, prompt, webContext, missionMode):
	summary = ""

	query = send_prompt(primeDirectives, GENERATE_WEB_QUERY_TEXT + prompt, webContext)

	# Remove double quotes
	query = query.replace('"', '')
	
	printSystemText(WEB_SEARCH_TEXT + query, missionMode)
		
	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		printSystemText("\n" + url, missionMode)	
		text = web.scrape(url)
		blockArray = split_text_in_blocks(text)

		# Summarize
		for block in blockArray:
			query = summary + block + SUMMARIZE_TEXT + prompt
			summary = send_prompt(primeDirectives, query, webContext) 

		if summary:			
			printSystemText("\n" + summary, missionMode)
			
	return summary
	

def isWebBrowsingRequired(primeDirectives, prompt, webContext):
	answer = False

	response = send_prompt(primeDirectives, BROWSE_INTERNET_QUERY_TEXT + prompt, webContext)
	
	# Remove dots and convert to uppercase
	response = response.replace(".", "").upper()
	
	if response == "YES":
		answer = True
		
	return answer


def isTaskCompleted(primeDirectives, task, context):
	answer = False

	response = send_prompt(primeDirectives, TASK_COMPLETED_TEXT + task, context)
	
	# Remove dots and convert to uppercase
	response = response.replace(".", "").upper()
	
	if response == "YES":
		answer = True
		
	return answer	
	
	
def runPrompt(primeDirectives, prompt, context, missionMode):	
	webContext = copy.deepcopy(context)

	newPrompt = prompt

	browseWeb = isWebBrowsingRequired(primeDirectives, prompt, webContext)
	
	while browseWeb == True:
		summary = webSearch(primeDirectives, newPrompt, webContext, missionMode)

		newPrompt = prompt + "\n" + summary
			
		browseWeb = isWebBrowsingRequired(primeDirectives, newPrompt, webContext)			

	# Send the prompt to the model	
	response = send_prompt(primeDirectives, newPrompt, context)

	printMagiText("\n" + response, missionMode)
	

def checkPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		runPrompt(primeDirectives, prompt, context, missionMode)


def switchMissionMode(missionMode):
	missionMode = not missionMode

	if missionMode == True:
		printSystemText("\nMission mode enabled", False)
	else:
		printSystemText("\nMission mode disabled", False)
		
	return missionMode


# Main logic
context = []
missionMode = False

printSystemText(MODEL_TEXT + MODEL, missionMode)

with open(PRIME_DIRECTIVES_FILE_PATH) as primeDirectivesFile:
	primeDirectives = primeDirectivesFile.read().strip()
	printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, missionMode)

printSystemText(SYSTEM_HINT_TEXT, missionMode)
		
# Main loop
while True:
	prompt = userInput(missionMode)

	if prompt == "":
		continue
	
	command = prompt.split()[0]
	
	if command.upper() == EXIT_COMMAND:
		break
	
	if command.upper() == MISSION_COMMAND:
		missionMode = switchMissionMode(missionMode)
	else:
		checkPrompt(primeDirectives, prompt, context, missionMode)
	
printSystemText("\n", missionMode)

