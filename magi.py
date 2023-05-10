'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 2.00
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

import openai
import os
import copy
from plugins import web

MODEL = "gpt-3.5-turbo"
CONTEXT_SIZE = 10 # Number of messages to remember
TEMPERATURE = 1
SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. The mission data will be saved in mission.txt\n"
PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_FILE_PATH = "mission.txt"
MISSION_COMMAND = "M"
MISSION_PROMPT = "Divide this mission in a list of independent tasks to be executed by you, one task per line, without subtasks. Write ONLY the list of tasks. MISSION: "
NEW_MISSION_TEXT = "\n\n----- Mission -----\n\n"
MISSION_MODE_ENABLED_TEXT = "\nMission mode enabled"
MISSION_MODE_DISABLED_TEXT = "\nMission mode disabled"
MODEL_TEXT = "\nModel: "
GENERATE_WEB_QUERY_TEXT = "Generate a query for google search to get information about this question, write only the query: "
BROWSE_INTERNET_QUERY_TEXT = "Tell me if you would need updated information from internet to do this task, write only YES or NO: "
WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 5 # Number of web pages per search
SUMMARY_PROMPT_TEXT = "PROMT = "
SUMMARIZE_TEXT = "\nSummarize the text below, including only the information that is relevant to PROMPT.\n"
SUMMARY_MERGE_TEXT = "\nAdd the text above to the text below, and then summarize it.\n"

MODEL_ERROR = "\n[ERROR] An exception occurred while trying to get a response from the model: "

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 500

GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

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
		printSystemText(MODEL_ERROR + str(e), False) 		
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
		printSystemText("\n" + task, True)
		runPrompt(primeDirectives, task, context, True)		
		

def webSearch(primeDirectives, prompt, webContext, missionMode):
	summary = ""
	lastSummary = ""	

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

		for block in blockArray:
			query = SUMMARY_PROMPT_TEXT + prompt + SUMMARIZE_TEXT + block	
			summary = send_prompt(primeDirectives, query, webContext)

			# Merge the new summary with the old one
			query = lastSummary + SUMMARY_MERGE_TEXT + summary
			summary = send_prompt(primeDirectives, query, webContext) 

			lastSummary = summary

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
	
	command = prompt.split()[0]
	
	if command.upper() == MISSION_COMMAND:
		missionMode = switchMissionMode(missionMode)
	else:
		checkPrompt(primeDirectives, prompt, context, missionMode)
	
 
