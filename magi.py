'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 12.01
Copyright   : GNU General Public License (GPLv3)
Description : AI system
=====================================================================================
'''

import core
import plugin
import agent
import re
from enum import Enum

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
MAGI_ACTION_PROMPT = """Review your previous response. Based on that review, choose one action:

1. IMPROVE: If the response needs correction, clarification, or more detail, formulate a command specifying the single most important improvement. Your entire output must be only the command itself, written in the second person.

2. EXPLORE: If the response is accurate and comprehensive, formulate a command to explore a relevant new direction, ask a follow-up question, or suggest a related task. Your entire output must be only the command itself, written in the second person."""
MAGI_ACTION_SYSTEM_PROMPT = "You are a logical AI assistant. Your task is to analyze the conversation history and the last response, then follow the user's instructions precisely."
SWITCH_AI_MODE_COMMAND = "M"
EXIT_COMMAND = "EXIT"


class AiMode(Enum):
    NORMAL  = 0
    MISSION = 1
    NERV    = 2
    MAGI    = 3


def sanitizeTask(task):
    # Remove digits, dots, dashes, spaces and "Task:" prefixes at the beginning of the task
    task = re.sub(r"^[0-9.\- ]*|^[Tt]ask[:]? *", '', task)
    
    return task
    

def createTaskList(mission, summary, header):
    context = []

    taskListText = core.send_prompt(TASK_LIST_SYSTEM_PROMPT, DATA_TEXT + summary + MISSION_TEXT + mission, context, hide_reasoning = True)
    
    plugin.printSystemText(header + taskListText + "\n")
    
    # Remove blank lines and create the task list
    taskList = [line for line in taskListText.splitlines() if line.strip()]

    return taskList


def runMagi(primeDirectives, action, context):
    while True:
        plugin.runAction(primeDirectives, action, context)
        aux_context = context[:]
        action = core.send_prompt(MAGI_ACTION_SYSTEM_PROMPT, MAGI_ACTION_PROMPT, aux_context, hide_reasoning = True)
        plugin.printSystemText(ACTION_TAG + action)


def runNerv(primeDirectives, mission, context):
    global nerv_data

    if not nerv_data:
        nerv_data = core.load_mission_data(mission)
        plugin.printSystemText(MISSION_DATA_TEXT + nerv_data)
        agent.displayNervSquad()

    orders = agent.captain.issueOrders(DATA_TEXT + nerv_data + MISSION_TEXT + mission)
    
    team_response = agent.runSquadOrders(orders)

    nerv_data = core.update_summary(mission, nerv_data, team_response)
    
    plugin.printSystemText(PROGRESS_REPORT_TEXT + nerv_data + "\n")


def runMission(primeDirectives, mission, context):
    summary = core.load_mission_data(mission)

    if summary:
        plugin.printSystemText(MISSION_DATA_TEXT + summary)

    actionList = createTaskList(mission, summary, ACTIONS_TEXT)

    for action in actionList:
        action = sanitizeTask(action)
    
        plugin.printSystemText(ACTION_TAG + action)

        action = ACTION_HELPER_TEXT + action

        response = plugin.runAction(primeDirectives, action, context)
        
        summary = core.update_summary(mission, summary, response)
    
    plugin.printMagiText(SUMMARY_TEXT + summary)


def checkPrompt(primeDirectives, prompt, context, ai_mode):    
    if ai_mode == AiMode.MISSION:
        runMission(primeDirectives, prompt, context)
    elif ai_mode == AiMode.NERV:        
        runNerv(primeDirectives, prompt, context)
    elif ai_mode == AiMode.MAGI:
        runMagi(primeDirectives, prompt, context)
    else:
        plugin.runAction(primeDirectives, prompt, context)


def switchAiMode(ai_mode):
    if ai_mode == AiMode.NORMAL:
        ai_mode = AiMode.MISSION
        plugin.printSystemText(MISSION_MODE_TEXT)
    elif ai_mode == AiMode.MISSION:
        ai_mode = AiMode.NERV
        plugin.printSystemText(NERV_MODE_TEXT)
    elif ai_mode == AiMode.NERV:
        ai_mode = AiMode.MAGI
        plugin.printSystemText(MAGI_MODE_TEXT)
    else:
        ai_mode = AiMode.NORMAL
        plugin.printSystemText(NORMAL_MODE_TEXT)        
        
    return ai_mode


# Main logic
if __name__ == "__main__":
    context = []
    nerv_data = ""
    ai_mode = AiMode.NORMAL

    primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

    if primeDirectives:
        plugin.printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives)

    plugin.printSystemText(SYSTEM_HINT_TEXT)
            
    # Main loop
    while True:
        prompt = plugin.userInput()

        if prompt == "" or prompt.isspace():
            continue

        prompt_tokens = core.get_number_of_tokens(prompt)

        if prompt_tokens > core.MAX_INPUT_TOKENS:
            plugin.printSystemText(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens))
            continue

        command = prompt.split()[0]

        if command.upper() == EXIT_COMMAND:
            break

        if command.upper() == SWITCH_AI_MODE_COMMAND:
            ai_mode = switchAiMode(ai_mode)
        else:
            checkPrompt(primeDirectives, prompt, context, ai_mode)
        
    plugin.printSystemText("\n")

