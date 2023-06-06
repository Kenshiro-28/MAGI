'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 3.04
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

from llama_cpp import Llama
import os
import re
import sys
import copy
import time
from plugins import web

SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_LOG_FILE_PATH = "mission_log.txt"
MISSION_DATA_FILE_PATH = "mission_data.txt"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
GENERATE_MISSION_TEXT = "\nDivide this mission in a list of independent tasks, one task per line, without subtasks. Write ONLY the list of tasks. MISSION = "
MISSION_COMPLETED_TEXT = "\nTell me if the above text successfully completes the mission, write only YES or NO. MISSION = "
CONTINUE_MISSION_TEXT = "\n\nI will continue the mission until it is successfully completed.\n\n\n----- Summary -----\n\n"
NEW_MISSION_TEXT = "\n\n----- Mission -----\n\n"
MISSION_MODE_ENABLED_TEXT = "\nMission mode enabled"
MISSION_MODE_DISABLED_TEXT = "\nMission mode disabled"
MODEL_TEXT = "\n\nModel: "
USER_TEXT = "USER: " 
ASSISTANT_TEXT = " ASSISTANT: "
WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
SUMMARIZE_TEXT = "\nWrite the information from the text above that is relevant to: "

MODEL_ERROR_TEXT = "\n[ERROR] An exception occurred while trying to get a response from the model: "
MODEL_NOT_FOUND_ERROR = "\n[ERROR] Model not found.\n"

MAX_TOKENS = 2048
EXTRA_TOKEN_COUNT = 48
MAX_INPUT_TOKENS = MAX_TOKENS // 2 + EXTRA_TOKEN_COUNT
MAX_INPUT_TOKENS_ERROR = "[ERROR] Your input has more than " + str(MAX_INPUT_TOKENS) + " tokens: "

READ_TEXT_FILE_WARNING = "\n[WARNING] File not found: "

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 300

GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

MISSION_COMMAND = "M"
EXIT_COMMAND = "EXIT"


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


def get_number_of_tokens(text):
	tokenized_text = model.tokenize(text.encode('utf-8'))
	text_tokens = len(tokenized_text) + EXTRA_TOKEN_COUNT
	
	return text_tokens
	

def get_context_data(context):
	text = ' '.join(context)
	text_tokens = get_number_of_tokens(text)
	
	return text, text_tokens
	
	
def get_completion_from_messages(context):
	try:
		text, text_tokens = get_context_data(context)
		
		# Check context size
		while len(context) > 1 and text_tokens > MAX_INPUT_TOKENS:
			context.pop(0)
			text, text_tokens = get_context_data(context)

		response = model(text, max_tokens = MAX_TOKENS - text_tokens)

		return response['choices'][0]['text'].lstrip()
		
	except Exception as e:
		printSystemText(MODEL_ERROR_TEXT + str(e), False) 
		exit()


def send_prompt(primeDirectives, prompt, context):
	command = USER_TEXT + primeDirectives + "\n" + prompt + ASSISTANT_TEXT

	context.append(command)

	response = get_completion_from_messages(context) 

	context.append(response)

	return response


def printSystemText(text, missionMode):
	print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)
	
	if missionMode:
		saveMissionLog(text)	

	
def printMagiText(text, missionMode):
	print(END_COLOR + MAGI_COLOR + text + END_COLOR)
	
	if missionMode:
		saveMissionLog(text)		


def saveMissionLog(text):
	with open(MISSION_LOG_FILE_PATH, 'a') as missionFile:
		missionFile.write(text + "\n")

	
def userInput(missionMode):
	sys.stdin.flush()

	prompt = input(USER_COLOR + "\n$ ")
	
	if missionMode:
		saveMissionLog(prompt)	
	
	return prompt		


def runMission(primeDirectives, prompt, context):
	missionCompleted = False

	# Load mission data
	summary = loadMissionData(prompt)
	
	if summary:			
		printSystemText(MISSION_DATA_TEXT + summary, True)

	while not missionCompleted:
		mission = send_prompt("", summary + GENERATE_MISSION_TEXT + prompt, context)
		
		missionTitle = NEW_MISSION_TEXT + mission + "\n"
		
		printSystemText(missionTitle, True)
		
		# Remove blank lines
		mission = [line for line in mission.splitlines() if line.strip()]

		for task in mission:
			printSystemText("\n" + task, True)

			response = runPrompt(primeDirectives, task, context, True)	

			summary = summarize(prompt, context, summary + "\n" + response)	
		
		missionCompleted = isPromptCompleted(summary + MISSION_COMPLETED_TEXT + prompt, context)
		
		if not missionCompleted:
			printMagiText(CONTINUE_MISSION_TEXT + summary, True)		


def summarize(prompt, context, text):
	query = text + SUMMARIZE_TEXT + prompt
	summary = send_prompt("", query, context) 
	
	return summary	


def summarizeBlockArray(prompt, context, blockArray):
	summary = ""

	# Summarize
	for block in blockArray:
		summary = summarize(prompt, context, summary + block)

	return summary		


def loadMissionData(prompt):
	context = []

	missionData = readTextFile(MISSION_DATA_FILE_PATH)
		
	blockArray = split_text_in_blocks(missionData)

	summary = summarizeBlockArray(prompt, context, blockArray)	
		
	return summary			


def webSearch(prompt, context, missionMode):
	# Remove digits, dots, dashes and spaces at the beginning of the prompt
	query = re.sub(r"^[0-9.\- ]*", '', prompt)

	printSystemText(WEB_SEARCH_TEXT + query, missionMode)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		printSystemText("\n" + url, missionMode)	
		text = web.scrape(url)
		blockArray = split_text_in_blocks(text)

		summary = summarizeBlockArray(prompt, context, blockArray)

		if summary:			
			printSystemText("\n" + summary, missionMode)
	

def isPromptCompleted(prompt, context):
	answer = False

	response = send_prompt("", prompt, context)

	if response:	
		response = response.split()[0].replace(".", "").replace(",", "").strip().upper()
	
	if response == "YES":
		answer = True
		
	return answer
	

def runPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		webSearch(prompt, context, missionMode)

	# Send the prompt to the model	
	response = send_prompt(primeDirectives, prompt, context)

	printMagiText("\n" + response, missionMode)
	
	return response	
	

def checkPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		runPrompt(primeDirectives, prompt, context, missionMode)


def switchMissionMode(missionMode):
	missionMode = not missionMode

	if missionMode:
		printSystemText(MISSION_MODE_ENABLED_TEXT, False)
	else:
		printSystemText(MISSION_MODE_DISABLED_TEXT, False)
		
	return missionMode


def readTextFile(path):
	try:
		with open(path) as textFile:
			text = textFile.read().strip()
			return text	
	
	except FileNotFoundError:
		printSystemText(READ_TEXT_FILE_WARNING + str(path), False)
		return ""
	

def loadModel():
	model = None

	fileArray = os.listdir()

	# Filter for .bin files
	binFileArray = [f for f in fileArray if f.endswith('.bin')]

	if binFileArray:
		# Get the first .bin file
		modelFile = binFileArray[0]

		# Get the file name without the .bin extension
		modelName = os.path.splitext(modelFile)[0]
		
		print()
		
		# Load model		
		model = Llama(model_path = modelFile, n_ctx = MAX_TOKENS)
		model.verbose = False

		# Print model name		
		printSystemText(MODEL_TEXT + modelName, False)	
	else:
		printSystemText(MODEL_NOT_FOUND_ERROR, False)
		exit()		
		
	return model		


# Main logic
context = []
missionMode = False
model = loadModel()

primeDirectives = readTextFile(PRIME_DIRECTIVES_FILE_PATH)

if primeDirectives:
	printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, missionMode)

printSystemText(SYSTEM_HINT_TEXT, missionMode)
		
# Main loop
while True:
	prompt = userInput(missionMode)
	prompt_tokens = get_number_of_tokens(prompt)
	
	if prompt == "":
		continue
	
	if prompt_tokens > MAX_INPUT_TOKENS:
		printSystemText(MAX_INPUT_TOKENS_ERROR + str(prompt_tokens), False)
		continue
	
	command = prompt.split()[0]
	
	if command.upper() == EXIT_COMMAND:
		break
	
	if command.upper() == MISSION_COMMAND:
		missionMode = switchMissionMode(missionMode)
	else:
		checkPrompt(primeDirectives, prompt, context, missionMode)
	
printSystemText("\n", missionMode)

