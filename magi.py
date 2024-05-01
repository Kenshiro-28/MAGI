'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 10.19
Copyright   : GNU General Public License (GPLv3)
Description : Advanced Chatbot
=====================================================================================
'''

import core
import plugin
import agent
import re

SYSTEM_HINT_TEXT = "\n\nHint: to switch AI mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
GENERATE_TASK_LIST_TEXT = "\nBreak down the following mission into a flat list of tasks, with each task described in a single line. Don't write titles or headings. MISSION = "
ACTION_HELPER_TEXT = "Do this: "
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
PROGRESS_REPORT_TEXT = "\n\n----- Progress Report -----\n\n"
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\nNormal mode enabled"
MISSION_MODE_TEXT = "\nMission mode enabled"
NERV_MODE_TEXT = "\nNERV mode enabled"

SWITCH_AI_MODE_COMMAND = "M"
EXIT_COMMAND = "EXIT"


def sanitizeTask(task):
	# Remove digits, dots, dashes, spaces and "Task:" prefixes at the beginning of the task
	task = re.sub(r"^[0-9.\- ]*|^[Tt]ask[:]? *", '', task)
	
	return task
	

def createTaskList(mission, summary, context, header, ai_mode):
	taskListText = core.send_prompt("", summary + GENERATE_TASK_LIST_TEXT + mission, context)
	
	plugin.printSystemText(header + taskListText + "\n", ai_mode)
	
	# Remove blank lines and create the task list
	taskList = [line for line in taskListText.splitlines() if line.strip()]

	return taskList
	

def runNerv(primeDirectives, mission, context, ai_mode):
	global nerv_data

	if not nerv_data:
		nerv_data = core.load_mission_data(mission)
		plugin.printSystemText(MISSION_DATA_TEXT + nerv_data, ai_mode)
		agent.displayNervSquad(ai_mode)

	orders = agent.captain.issueOrders("\nDATA = " + nerv_data + "\nMISSION = " + mission, ai_mode)
	
	team_response = agent.runSquadOrders(orders, ai_mode)

	nerv_data = core.update_summary(mission, context, nerv_data, team_response)
	
	plugin.printSystemText(PROGRESS_REPORT_TEXT + nerv_data + "\n", ai_mode)


def runMission(primeDirectives, mission, context, ai_mode):
	summary = ""

	if ai_mode == core.AiMode.MISSION:	
		summary = core.load_mission_data(mission)
	
		if summary:			
			plugin.printSystemText(MISSION_DATA_TEXT + summary, ai_mode)

	actionList = createTaskList(mission, summary, context, ACTIONS_TEXT, ai_mode)

	for action in actionList:
		action = sanitizeTask(action)
	
		plugin.printSystemText(ACTION_TAG + action, ai_mode)

		action = ACTION_HELPER_TEXT + action

		actionSummary = plugin.runAction(primeDirectives, action, context, ai_mode)
		
		summary = core.update_summary(mission, context, summary, actionSummary)
	
	plugin.printMagiText(SUMMARY_TEXT + summary, ai_mode)
	
	return summary	


def checkPrompt(primeDirectives, prompt, context, ai_mode):	
	if ai_mode == core.AiMode.MISSION:
		runMission(primeDirectives, prompt, context, ai_mode)
	elif ai_mode == core.AiMode.NERV:		
		runNerv(primeDirectives, prompt, context, ai_mode)
	else:
		plugin.runAction(primeDirectives, prompt, context, ai_mode)


def switchAiMode(ai_mode):
	if ai_mode == core.AiMode.NORMAL:
		ai_mode = core.AiMode.MISSION
		plugin.printSystemText(MISSION_MODE_TEXT, ai_mode)
	elif ai_mode == core.AiMode.MISSION:
		ai_mode = core.AiMode.NERV
		plugin.printSystemText(NERV_MODE_TEXT, ai_mode)
	else:
		ai_mode = core.AiMode.NORMAL
		plugin.printSystemText(NORMAL_MODE_TEXT, ai_mode)		
		
	return ai_mode


# Main logic
if __name__ == "__main__":
	context = []
	nerv_data = ""
	ai_mode = core.AiMode.NORMAL

	primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

	if primeDirectives:
		plugin.printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives, ai_mode)

	plugin.printSystemText(SYSTEM_HINT_TEXT, ai_mode)
			
	# Main loop
	while True:
		prompt = plugin.userInput(ai_mode)

		if prompt == "" or prompt.isspace():
			continue
			
		prompt_tokens = core.get_number_of_tokens(prompt)
		
		if prompt_tokens > core.MAX_INPUT_TOKENS:
			plugin.printSystemText(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens), ai_mode)
			continue
		
		command = prompt.split()[0]
		
		if command.upper() == EXIT_COMMAND:
			break
		
		if command.upper() == SWITCH_AI_MODE_COMMAND:
			ai_mode = switchAiMode(ai_mode)
		else:
			checkPrompt(primeDirectives, prompt, context, ai_mode)
		
	plugin.printSystemText("\n", ai_mode)

