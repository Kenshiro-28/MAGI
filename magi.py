'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 11.05
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
DATA_TEXT = "DATA = "
MISSION_TEXT = "\n\nMISSION = "
TASK_LIST_SYSTEM_PROMPT = "Your task is to break down the user's prompt provided in the MISSION section into a list of specific and detailed tasks. Use the DATA section only if it provides useful information for the MISSION. Only output the task list, no titles, headers, or additional text. Ensure each task is actionable, detailed, and written in a clear, self-contained manner. Each task must be long enough to convey its purpose fully, but it must fit on a single paragraph. Write each task on its own paragraph."
ACTION_HELPER_TEXT = "Do this: "
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
PROGRESS_REPORT_TEXT = "\n\n----- Progress Report -----\n\n"
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\n««««« NORMAL MODE »»»»»"
MISSION_MODE_TEXT = "\n««««« MISSION MODE »»»»»"
NERV_MODE_TEXT    = "\n««««« NERV MODE »»»»»"
MAGI_MODE_TEXT    = "\n««««« MAGI MODE »»»»»\n\nThis is a fully autonomous mode.\n\nIt will run continuously until you manually stop the program by pressing Ctrl + C."
MAGI_ACTION_PROMPT = "Critically evaluate your previous response for accuracy, completeness, and clarity. Identify any gaps, inconsistencies, or areas where further detail could improve understanding. Ensure that your new response builds upon the previous answer by incorporating additional context, refining explanations, and correcting any oversights. Your goal is to produce an answer that is progressively more comprehensive and refined over each iteration."
SWITCH_AI_MODE_COMMAND = "M"
EXIT_COMMAND = "EXIT"


def sanitizeTask(task):
    # Remove digits, dots, dashes, spaces and "Task:" prefixes at the beginning of the task
    task = re.sub(r"^[0-9.\- ]*|^[Tt]ask[:]? *", '', task)
    
    return task
    

def createTaskList(mission, summary, header, ai_mode):
    context = []

    taskListText = core.send_prompt(TASK_LIST_SYSTEM_PROMPT, DATA_TEXT + summary + MISSION_TEXT + mission, context, hide_reasoning = True)
    
    plugin.printSystemText(header + taskListText + "\n", ai_mode)
    
    # Remove blank lines and create the task list
    taskList = [line for line in taskListText.splitlines() if line.strip()]

    return taskList
    

def runMagi(primeDirectives, action, context, ai_mode):
    plugin.runAction(primeDirectives, action, context, ai_mode)

    while True:
        plugin.runAction(primeDirectives, MAGI_ACTION_PROMPT, context, ai_mode)


def runNerv(primeDirectives, mission, context, ai_mode):
    global nerv_data

    if not nerv_data:
        nerv_data = core.load_mission_data(mission)
        plugin.printSystemText(MISSION_DATA_TEXT + nerv_data, ai_mode)
        agent.displayNervSquad(ai_mode)

    orders = agent.captain.issueOrders(DATA_TEXT + nerv_data + MISSION_TEXT + mission, ai_mode)
    
    team_response = agent.runSquadOrders(orders, ai_mode)

    nerv_data = core.update_summary(mission, nerv_data, team_response)
    
    plugin.printSystemText(PROGRESS_REPORT_TEXT + nerv_data + "\n", ai_mode)


def runMission(primeDirectives, mission, context, ai_mode):
    summary = core.load_mission_data(mission)

    if summary:
        plugin.printSystemText(MISSION_DATA_TEXT + summary, ai_mode)

    actionList = createTaskList(mission, summary, ACTIONS_TEXT, ai_mode)

    for action in actionList:
        action = sanitizeTask(action)
    
        plugin.printSystemText(ACTION_TAG + action, ai_mode)

        action = ACTION_HELPER_TEXT + action

        response = plugin.runAction(primeDirectives, action, context, ai_mode)
        
        summary = core.update_summary(mission, summary, response)
    
    plugin.printMagiText(SUMMARY_TEXT + summary, ai_mode)


def checkPrompt(primeDirectives, prompt, context, ai_mode):    
    if ai_mode == core.AiMode.MISSION:
        runMission(primeDirectives, prompt, context, ai_mode)
    elif ai_mode == core.AiMode.NERV:        
        runNerv(primeDirectives, prompt, context, ai_mode)
    elif ai_mode == core.AiMode.MAGI:
        runMagi(primeDirectives, prompt, context, ai_mode)
    else:
        plugin.runAction(primeDirectives, prompt, context, ai_mode)


def switchAiMode(ai_mode):
    if ai_mode == core.AiMode.NORMAL:
        ai_mode = core.AiMode.MISSION
        plugin.printSystemText(MISSION_MODE_TEXT, ai_mode)
    elif ai_mode == core.AiMode.MISSION:
        ai_mode = core.AiMode.NERV
        plugin.printSystemText(NERV_MODE_TEXT, ai_mode)
    elif ai_mode == core.AiMode.NERV:
        ai_mode = core.AiMode.MAGI
        plugin.printSystemText(MAGI_MODE_TEXT, ai_mode)
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

