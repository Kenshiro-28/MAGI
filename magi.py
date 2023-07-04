'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 3.16
Copyright   : GNU General Public License (GPLv3)
Description : Autonomous agent 
=====================================================================================
'''

import core
import plugin
import re

SYSTEM_HINT_TEXT = "\n\nHint: to switch AI mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
GENERATE_TASK_LIST_TEXT = "\nWrite a task list. Write one task per line, no subtasks. Write ONLY the task list. MISSION = "
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
STRATEGY_TEXT = "\n\n----- Strategy -----\n\n"
MISSION_TAG = "\n[MISSION] "
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\nNormal mode enabled"
MISSION_MODE_TEXT = "\nMission mode enabled"
NERV_MODE_TEXT = "\nNERV mode enabled\n\n[WARNING] this mode runs continuously"
WEB_SEARCH_QUERY = "Create a one line search query for Google that would yield the most comprehensive and relevant results on the topic of: "
WEB_SUMMARY_TEXT = "\n\nWEB SUMMARY: "
TELEGRAM_MESSAGE_TEXT = "\n[TELEGRAM] "

SWITCH_AI_MODE_COMMAND = "M"
EXIT_COMMAND = "EXIT"


def sanitizeTask(task):
	# Remove digits, dots, dashes and spaces at the beginning of the task
	task = re.sub(r"^[0-9.\- ]*", '', task)
	
	return task
	

def createTaskList(mission, summary, context, header, ai_mode):
	taskListText = core.send_prompt("", summary + GENERATE_TASK_LIST_TEXT + mission, context)
	
	printSystemText(header + taskListText + "\n", ai_mode)
	
	# Remove blank lines and create the task list
	taskList = [line for line in taskListText.splitlines() if line.strip()]

	return taskList
	

def runNerv(primeDirectives, goal, context, ai_mode):
	summary = core.load_mission_data(goal)
	
	if summary:			
		printSystemText(MISSION_DATA_TEXT + summary, ai_mode)

	while True:
		missionList = createTaskList(goal, summary, context, STRATEGY_TEXT, ai_mode)

		for mission in missionList:
			mission = sanitizeTask(mission)
		
			printSystemText(MISSION_TAG + mission, ai_mode)

			missionSummary = runMission(primeDirectives, mission, context, ai_mode)
			
			summary = core.update_summary(goal, context, summary, missionSummary)
		
		printMagiText(SUMMARY_TEXT + summary, ai_mode)
	

def runMission(primeDirectives, mission, context, ai_mode):
	summary = ""

	if ai_mode == core.AiMode.MISSION:	
		summary = core.load_mission_data(mission)
	
		if summary:			
			printSystemText(MISSION_DATA_TEXT + summary, ai_mode)

	taskList = createTaskList(mission, summary, context, ACTIONS_TEXT, ai_mode)

	for task in taskList:
		task = sanitizeTask(task)
	
		printSystemText(ACTION_TAG + task, ai_mode)

		taskSummary = runTask(primeDirectives, task, mission, context, ai_mode)
		
		summary = core.update_summary(mission, context, summary, taskSummary)
	
	printMagiText(SUMMARY_TEXT + summary, ai_mode)


def runTask(primeDirectives, task, mission, context, ai_mode):
	response = core.send_prompt(primeDirectives, task, context)

	# Search for updated information on the Internet
	if plugin.WEB_PLUGIN_ACTIVE:
		query = core.send_prompt("", WEB_SEARCH_QUERY + task, context) 
		webSummary = plugin.webSearch(query)
		summary = response + WEB_SUMMARY_TEXT + webSummary
	else:
		summary = response
	
	printMagiText("\n" + summary, ai_mode)
	
	return summary
	

def checkPrompt(primeDirectives, prompt, context, ai_mode):	
	if ai_mode == core.AiMode.MISSION:
		runMission(primeDirectives, prompt, context, ai_mode)
	elif ai_mode == core.AiMode.NERV:		
		runNerv(primeDirectives, prompt, context, ai_mode)
	else:
		response = core.send_prompt(primeDirectives, prompt, context)
		printMagiText("\n" + response, ai_mode)


def switchAiMode(ai_mode):
	if ai_mode == core.AiMode.NORMAL:
		ai_mode = core.AiMode.MISSION
		printSystemText(MISSION_MODE_TEXT, ai_mode)
	elif ai_mode == core.AiMode.MISSION:
		ai_mode = core.AiMode.NERV
		printSystemText(NERV_MODE_TEXT, ai_mode)
	else:
		ai_mode = core.AiMode.NORMAL
		printSystemText(NORMAL_MODE_TEXT, ai_mode)		
		
	return ai_mode


def printSystemText(text, ai_mode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		plugin.send_telegram_bot(text)
		
	core.print_system_text(text, ai_mode)
	
	
def printMagiText(text, ai_mode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		plugin.send_telegram_bot(text)
		
	core.print_magi_text(text, ai_mode)
		

def userInput(ai_mode):
	if plugin.TELEGRAM_PLUGIN_ACTIVE:
		prompt = plugin.receive_telegram_bot()
		
		if prompt:
			core.print_system_text(TELEGRAM_MESSAGE_TEXT + prompt, ai_mode)		
	else:
		prompt = core.user_input(ai_mode)
		
	return prompt		


# Main logic
if __name__ == "__main__":
	context = []
	ai_mode = core.AiMode.NORMAL

	primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

	if primeDirectives:
		printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, ai_mode)

	printSystemText(SYSTEM_HINT_TEXT, ai_mode)
			
	# Main loop
	while True:
		prompt = userInput(ai_mode)

		if prompt == "" or prompt.isspace():
			continue
			
		prompt_tokens = core.get_number_of_tokens(prompt)
		
		if prompt_tokens > core.MAX_INPUT_TOKENS:
			printSystemText(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens), ai_mode)
			continue
		
		command = prompt.split()[0]
		
		if command.upper() == EXIT_COMMAND:
			break
		
		if command.upper() == SWITCH_AI_MODE_COMMAND:
			ai_mode = switchAiMode(ai_mode)
		else:
			checkPrompt(primeDirectives, prompt, context, ai_mode)
		
	printSystemText("\n", ai_mode)

