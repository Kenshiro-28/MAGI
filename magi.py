'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 3.05
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
GENERATE_TASK_LIST_TEXT = "\nWrite a task list. Write one task per line, no subtasks. Write ONLY the task list. MISSION = "
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
UPDATED_DATA_TEXT = "\n\nUPDATED DATA: "
BASIC_SUMMARY_TEXT = "Summarize the following text: "
SUMMARIZE_TEXT = "\nSummarize the information from the above text that is relevant to this topic: "

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

TEXT_BLOCK_WORDS = 500

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
		return ""


def send_prompt(primeDirectives, prompt, context):
	if primeDirectives:
		primeDirectives += "\n"

	command = USER_TEXT + primeDirectives + prompt + ASSISTANT_TEXT

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


def runMission(primeDirectives, mission, context):
	missionCompleted = False

	summary = loadMissionData(mission)
	
	if summary:			
		printSystemText(MISSION_DATA_TEXT + summary, True)

	while not missionCompleted:
		taskListText = send_prompt("", summary + GENERATE_TASK_LIST_TEXT + mission, context)
		
		printSystemText(NEW_MISSION_TEXT + taskListText + "\n", True)
		
		# Remove blank lines and create the task list
		taskList = [line for line in taskListText.splitlines() if line.strip()]

		for task in taskList:
			printSystemText("\n" + task, True)

			taskSummary = runTask(primeDirectives, task, mission, context)
			
			summary = updateSummary(mission, context, summary, taskSummary)
		
		missionCompleted = isPromptCompleted(summary + MISSION_COMPLETED_TEXT + mission, context)
		
		if not missionCompleted:
			printMagiText(CONTINUE_MISSION_TEXT + summary, True)		


def webSearch(query):
	context = []
	summary	= ""

	printSystemText(WEB_SEARCH_TEXT + query, True)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		printSystemText("\n" + url, True)	
		text = web.scrape(url)
		blockArray = split_text_in_blocks(text)

		webSummary = summarizeBlockArray(query, blockArray)

		summary = updateSummary(query, context, summary, webSummary)

		if webSummary:			
			printSystemText("\n" + webSummary, True)
			
	return summary
	

def runTask(primeDirectives, task, mission, context):
	# Remove digits, dots, dashes and spaces at the beginning of the task
	task = re.sub(r"^[0-9.\- ]*", '', task)

	response = send_prompt(primeDirectives, task, context)

	# Search for updated information on the Internet
	query = basic_summary(mission, task)
	webSummary = webSearch(query)
	
	summary = response + UPDATED_DATA_TEXT + webSummary
	
	printMagiText("\n" + summary, True)
	
	return summary
	

def basic_summary(text1, text2):
	context = []	
	summary = send_prompt("", BASIC_SUMMARY_TEXT + text1 + "\n" + text2, context) 
	
	return summary


def summarize(topic, context, text):
	summary = send_prompt("", text + SUMMARIZE_TEXT + topic, context) 
	
	return summary
	

def updateSummary(topic, context, summary, text):
	if text:
		if summary:
			summary = summarize(topic, context, summary + "\n" + text)
		else:
			summary = text

	return summary


def summarizeBlockArray(topic, blockArray):
	context = []
	summary = ""

	# Summarize
	for block in blockArray:
		summary = updateSummary(topic, context, summary, block)

	return summary		


def loadMissionData(prompt):
	missionData = readTextFile(MISSION_DATA_FILE_PATH)
		
	blockArray = split_text_in_blocks(missionData)

	summary = summarizeBlockArray(prompt, blockArray)	
		
	return summary			

	
def isPromptCompleted(prompt, context):
	answer = False

	response = send_prompt("", prompt, context)

	if response:	
		response = response.split()[0].replace(".", "").replace(",", "").strip().upper()
	
	if response == "YES":
		answer = True
		
	return answer
	

def checkPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		response = send_prompt(primeDirectives, prompt, context)
		printMagiText("\n" + response, False)


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
	printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, False)

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

