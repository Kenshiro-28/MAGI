'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 3.06
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

import core
import re
from plugins import web

SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
GENERATE_TASK_LIST_TEXT = "\nWrite a task list. Write one task per line, no subtasks. Write ONLY the task list. MISSION = "
MISSION_COMPLETED_TEXT = "\nTell me if the above text successfully completes the mission, write only YES or NO. MISSION = "
CONTINUE_MISSION_TEXT = "\n\nI will continue the mission until it is successfully completed.\n\n\n----- Summary -----\n\n"
NEW_MISSION_TEXT = "\n\n----- Mission -----\n\n"
MISSION_MODE_ENABLED_TEXT = "\nMission mode enabled"
MISSION_MODE_DISABLED_TEXT = "\nMission mode disabled"

WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
UPDATED_DATA_TEXT = "\n\nUPDATED DATA: "

GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

MISSION_COMMAND = "M"
EXIT_COMMAND = "EXIT"


def runMission(primeDirectives, mission, context):
	missionCompleted = False

	summary = core.load_mission_data(mission)
	
	if summary:			
		core.print_system_text(MISSION_DATA_TEXT + summary, True)

	while not missionCompleted:
		taskListText = core.send_prompt("", summary + GENERATE_TASK_LIST_TEXT + mission, context)
		
		core.print_system_text(NEW_MISSION_TEXT + taskListText + "\n", True)
		
		# Remove blank lines and create the task list
		taskList = [line for line in taskListText.splitlines() if line.strip()]

		for task in taskList:
			core.print_system_text("\n" + task, True)

			taskSummary = runTask(primeDirectives, task, mission, context)
			
			summary = core.update_summary(mission, context, summary, taskSummary)
		
		missionCompleted = core.is_prompt_completed(summary + MISSION_COMPLETED_TEXT + mission, context)
		
		if not missionCompleted:
			core.print_magi_text(CONTINUE_MISSION_TEXT + summary, True)		


def webSearch(query):
	context = []
	summary	= ""

	core.print_system_text(WEB_SEARCH_TEXT + query, True)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		core.print_system_text("\n" + url, True)	
		text = web.scrape(url)
		blockArray = core.split_text_in_blocks(text)

		webSummary = core.summarize_block_array(query, blockArray)

		summary = core.update_summary(query, context, summary, webSummary)

		if webSummary:			
			core.print_system_text("\n" + webSummary, True)
			
	return summary
	

def runTask(primeDirectives, task, mission, context):
	# Remove digits, dots, dashes and spaces at the beginning of the task
	task = re.sub(r"^[0-9.\- ]*", '', task)

	response = core.send_prompt(primeDirectives, task, context)

	# Search for updated information on the Internet
	query = core.basic_summary(mission, task)
	webSummary = webSearch(query)
	
	summary = response + UPDATED_DATA_TEXT + webSummary
	
	core.print_magi_text("\n" + summary, True)
	
	return summary
	

def checkPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		response = core.send_prompt(primeDirectives, prompt, context)
		core.print_magi_text("\n" + response, False)


def switchMissionMode(missionMode):
	missionMode = not missionMode

	if missionMode:
		core.print_system_text(MISSION_MODE_ENABLED_TEXT, False)
	else:
		core.print_system_text(MISSION_MODE_DISABLED_TEXT, False)
		
	return missionMode


# Main logic
if __name__ == "__main__":
	context = []
	missionMode = False

	primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

	if primeDirectives:
		core.print_system_text(PRIME_DIRECTIVES_TEXT + primeDirectives, False)

	core.print_system_text(SYSTEM_HINT_TEXT, missionMode)
			
	# Main loop
	while True:
		prompt = core.user_input(missionMode)
		prompt_tokens = core.get_number_of_tokens(prompt)
		
		if prompt == "":
			continue
		
		if prompt_tokens > core.MAX_INPUT_TOKENS:
			core.print_system_text(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens), False)
			continue
		
		command = prompt.split()[0]
		
		if command.upper() == EXIT_COMMAND:
			break
		
		if command.upper() == MISSION_COMMAND:
			missionMode = switchMissionMode(missionMode)
		else:
			checkPrompt(primeDirectives, prompt, context, missionMode)
		
	core.print_system_text("\n", missionMode)

