'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 3.14
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

import core
import plugin
import re

SYSTEM_HINT_TEXT = "\n\nHint: to enable mission mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
GENERATE_TASK_LIST_TEXT = "\nWrite a task list. Write one task per line, no subtasks. Write ONLY the task list. MISSION = "
MISSION_SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
NEW_MISSION_TEXT = "\n\n----- Mission -----\n\n"
MISSION_MODE_ENABLED_TEXT = "\nMission mode enabled"
MISSION_MODE_DISABLED_TEXT = "\nMission mode disabled"
WEB_SEARCH_QUERY = "Create a one line search query for Google that would yield the most comprehensive and relevant results on the topic of: "
WEB_SUMMARY_TEXT = "\n\nWEB SUMMARY: "
TELEGRAM_MESSAGE_TEXT = "\n[TELEGRAM] "

MISSION_COMMAND = "M"
EXIT_COMMAND = "EXIT"


def runMission(primeDirectives, mission, context):
	summary = core.load_mission_data(mission)
	
	if summary:			
		printSystemText(MISSION_DATA_TEXT + summary, True)

	taskListText = core.send_prompt("", summary + GENERATE_TASK_LIST_TEXT + mission, context)
	
	printSystemText(NEW_MISSION_TEXT + taskListText + "\n", True)
	
	# Remove blank lines and create the task list
	taskList = [line for line in taskListText.splitlines() if line.strip()]

	for task in taskList:
		printSystemText("\n" + task, True)

		taskSummary = runTask(primeDirectives, task, mission, context)
		
		summary = core.update_summary(mission, context, summary, taskSummary)
	
	printMagiText(MISSION_SUMMARY_TEXT + summary, True)


def runTask(primeDirectives, task, mission, context):
	# Remove digits, dots, dashes and spaces at the beginning of the task
	task = re.sub(r"^[0-9.\- ]*", '', task)

	response = core.send_prompt(primeDirectives, task, context)

	# Search for updated information on the Internet
	if plugin.WEB_PLUGIN_ACTIVE:
		query = core.send_prompt("", WEB_SEARCH_QUERY + task, context) 
		webSummary = plugin.webSearch(query)
		summary = response + WEB_SUMMARY_TEXT + webSummary
	else:
		summary = response
	
	printMagiText("\n" + summary, True)
	
	return summary
	

def checkPrompt(primeDirectives, prompt, context, missionMode):	
	if missionMode:
		runMission(primeDirectives, prompt, context)
	else:
		response = core.send_prompt(primeDirectives, prompt, context)
		printMagiText("\n" + response, False)


def switchMissionMode(missionMode):
	missionMode = not missionMode

	if missionMode:
		printSystemText(MISSION_MODE_ENABLED_TEXT, False)
	else:
		printSystemText(MISSION_MODE_DISABLED_TEXT, False)
		
	return missionMode


def printSystemText(text, missionMode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		plugin.send_telegram_bot(text)
		
	core.print_system_text(text, missionMode)
	
	
def printMagiText(text, missionMode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		plugin.send_telegram_bot(text)
		
	core.print_magi_text(text, missionMode)
		

def userInput(missionMode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		prompt = plugin.receive_telegram_bot()
		
		if prompt:
			core.print_system_text(TELEGRAM_MESSAGE_TEXT + prompt, missionMode)		
	else:
		prompt = core.user_input(missionMode)
		
	return prompt		


# Main logic
if __name__ == "__main__":
	context = []
	missionMode = False

	primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

	if primeDirectives:
		printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, missionMode)

	printSystemText(SYSTEM_HINT_TEXT, missionMode)
			
	# Main loop
	while True:
		prompt = userInput(missionMode)

		if prompt == "":
			continue
			
		prompt_tokens = core.get_number_of_tokens(prompt)
		
		if prompt_tokens > core.MAX_INPUT_TOKENS:
			printSystemText(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens), False)
			continue
		
		command = prompt.split()[0]
		
		if command.upper() == EXIT_COMMAND:
			break
		
		if command.upper() == MISSION_COMMAND:
			missionMode = switchMissionMode(missionMode)
		else:
			checkPrompt(primeDirectives, prompt, context, missionMode)
		
	printSystemText("\n", missionMode)

