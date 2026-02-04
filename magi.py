'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 12.28
Copyright   : GNU General Public License (GPLv3)
Description : AI system
=====================================================================================
'''

import re
import time
from enum import Enum
from typing import Any

# MAGI modules
core: Any = None
comms: Any = None
toolchain: Any = None
agent: Any = None

SYSTEM_HINT_TEXT = "\n\nHint: to switch AI mode, type the letter 'm' and press enter. To exit MAGI, type 'exit'.\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
DATA_TEXT = "DATA = "
MISSION_TEXT = "\n\nMISSION = "
GENERATE_TASK_LIST_TEXT = "You have to break down the mission provided in the MISSION section into a list of specific and detailed tasks. Use the DATA section only if it provides useful information for the MISSION. Ensure each task is actionable, detailed, and written in a clear, self-contained manner. Each task must be long enough to convey its purpose fully, but it must fit on a single paragraph. Write each task on its own paragraph, separated by a blank line. Output ONLY the tasks, no reasoning, no commentary, no preamble.\n\n"
ACTION_HELPER_TEXT = "Do this: "
EXIT_MAGI_TEXT = "\nまたね。\n"
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
PROGRESS_REPORT_TEXT = "\n\n----- Progress Report -----\n\n"
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\n««««« NORMAL MODE »»»»»"
MISSION_MODE_TEXT = "\n««««« MISSION MODE »»»»»"
NERV_MODE_TEXT    = "\n««««« NERV MODE »»»»»"
MAGI_MODE_TEXT    = "\n««««« MAGI MODE »»»»»\n\nThis is a fully autonomous mode.\n\nIt will run continuously until you manually stop the program by pressing Ctrl + C."
MAGI_ACTION_PROMPT = """You are working autonomously without user interaction.

Review your previous response in the context of overall progress. Then select one action:

1. EXPLOIT: If the previous response can be improved through correction, clarification, refinement, more detail, or updated data to directly advance the current path, create a command for the single most effective action. Ensure the command is actionable, detailed, and written in a clear, self-contained manner.
2. EXPLORE: If further exploitation on the current path offers no meaningful value (e.g., it's in a dead end, redundant, or stalled with no clear progress), reflect on the current situation and create a command to explore the most promising direction. If no clear new direction is viable, create a command to brainstorm new ideas and select the best one. Ensure the command is actionable, detailed, and written in a clear, self-contained manner.

CONSTRAINTS:
- The command must be specific and actionable.
- DO NOT use vague phrases like "Continue" or "Analyze".
- Always choose one action to continue the mission—do not stop or exit.

CRITICAL OUTPUT FORMAT:
Output EXACTLY one line. No reasoning. No preamble.
Format: TAG: COMMAND

Output only the mode tag followed by the command in second person (imperative form), as in the examples below.

Examples:
EXPLOIT: Fix the error of SOLANA_PRIVATE_KEY environment variable not set by hardcoding the private key '2base58exampleprivatekeystring' in the code.
EXPLORE: Research how to earn SOL tokens.
EXPLOIT: Refine the stock analysis for TSLA by incorporating recent price data with closing prices on Oct 21, 2025: 442.60, Oct 22, 2025: 438.97, Oct 23, 2025: 419.50.
EXPLORE: Brainstorm alternative trading strategies for volatile stocks.
EXPLOIT: Refine the military drone swarm simulation by incorporating formation data with drone counts 10, 20, 30 and positions at (40.7128, -74.0060), (34.0522, -118.2437).
EXPLORE: Research alternative deployment strategies for drone reconnaissance in urban environments."""
HEARTBEAT_SECONDS_KEY = "HEARTBEAT_SECONDS"
HEARTBEAT_TAG = "\n\n[HEARTBEAT]"
HEARTBEAT_IDLE_TEXT = "[IDLE]"
HEARTBEAT_PROMPT = f"""[SYSTEM EVENT: IDLE TIMEOUT]
The user has been silent. You are running a background thought loop.
Analyze the conversation history to determine your Current Persona (e.g., Assistant, Friend, Partner) and the context.

DECISION LOGIC (EVALUATE IN ORDER):
1. STALLED REAL-WORLD TASK: Are we waiting for real user data (e.g., API key, file, confirmation)?
   -> STRATEGY SHIFT: Do NOT invent data. Can you perform a *parallel real task*?
      - Research: Look up documentation or market stats.
      - Preparation: Draft the code scaffold or plan.
      -> Action: Generate an instruction to execute this parallel real task.
2. ONGOING CREATIVE/CODE: Are we writing a story, code, or roleplay scenario?
   -> CONTINUATION: Did we stop early?
      - Action: Generate an instruction to write the next logical segment. (Fictional invention is allowed ONLY for stories/roleplay).
3. SOCIAL CONNECTION: Are we in a chat or personal connection?
   -> ENGAGEMENT: The user might be busy or shy.
      - Action: Generate an in-character message (e.g., playful, concerned, curious) to re-engage.
4. DONE: If no useful action is possible.
   -> Action: Output {HEARTBEAT_IDLE_TEXT}.

CRITICAL OUTPUT RULES:
- You must output an INSTRUCTION to yourself.
- Wrap your instruction in brackets.
- Format: [Instruction: <What you should do>]
- If no action is needed, output exactly: {HEARTBEAT_IDLE_TEXT}

EXAMPLES:
- [Instruction: User didn't provide the API key, so draft the Python client class structure to be ready.]
- [Instruction: Since the user is silent, continue writing the next scene where the hero enters the cave.]
- [Instruction: Research current APY rates for the requested token while waiting.]
- [Instruction: Tease the user playfully about leaving me on read.]
- {HEARTBEAT_IDLE_TEXT}"""
SWITCH_AI_MODE_COMMAND = "M"
EXIT_COMMAND = "EXIT"


_nerv_data: str = ""


class AiMode(Enum):
    NORMAL  = 0
    MISSION = 1
    NERV    = 2
    MAGI    = 3


def sanitizeTask(task: str) -> str:
    # Remove digits, dots, dashes, spaces and "Task:" prefixes at the beginning of the task
    task = re.sub(r"^[0-9.\- ]*|^[Tt]ask[:]? *", '', task)
    return task


def createTaskList(primeDirectives: str, mission: str, summary: str, header: str, context: list[str]) -> list[str]:
    taskListText = core.send_prompt(primeDirectives, GENERATE_TASK_LIST_TEXT + DATA_TEXT + summary + MISSION_TEXT + mission, context, hide_reasoning = True)
    comms.printSystemText(header + taskListText + "\n")
    # Remove blank lines and create the task list
    taskList = [line for line in taskListText.splitlines() if line.strip()]
    return taskList


def runMagi(primeDirectives: str, action: str, context: list[str]) -> None:
    prompt = action + "\n\n" + MAGI_ACTION_PROMPT
    action = toolchain.run_core_protocol(primeDirectives, prompt, context, hide_reasoning = True)
    comms.printSystemText(ACTION_TAG + action)

    while True:
        toolchain.runAction(primeDirectives, action, context)
        aux_context = context[:]
        action = toolchain.run_core_protocol(primeDirectives, MAGI_ACTION_PROMPT, aux_context, hide_reasoning = True)
        comms.printSystemText(ACTION_TAG + action)


def runNerv(mission: str) -> None:
    global _nerv_data

    if not _nerv_data:
        _nerv_data = core.load_mission_data(mission)
        comms.printSystemText(MISSION_DATA_TEXT + _nerv_data)
        agent.displayNervSquad()

    orders = agent.captain.issueOrders(DATA_TEXT + _nerv_data + MISSION_TEXT + mission)
    team_response = agent.runSquadOrders(orders)
    _nerv_data = core.update_summary(mission, _nerv_data, team_response)
    comms.printSystemText(PROGRESS_REPORT_TEXT + _nerv_data + "\n")


def runMission(primeDirectives: str, mission: str, context: list[str]) -> None:
    summary = core.load_mission_data(mission)

    if summary:
        comms.printSystemText(MISSION_DATA_TEXT + summary)

    actionList = createTaskList(primeDirectives, mission, summary, ACTIONS_TEXT, context)

    for action in actionList:
        action = sanitizeTask(action)
        comms.printSystemText(ACTION_TAG + action)
        action = ACTION_HELPER_TEXT + action
        response = toolchain.runAction(primeDirectives, action, context)
        summary = core.update_summary(mission, summary, response)

    comms.printMagiText(SUMMARY_TEXT + summary)


def checkPrompt(primeDirectives: str, prompt: str, context: list[str], ai_mode: AiMode) -> None:
    if ai_mode == AiMode.MISSION:
        runMission(primeDirectives, prompt, context)
    elif ai_mode == AiMode.NERV:
        runNerv(prompt)
    elif ai_mode == AiMode.MAGI:
        runMagi(primeDirectives, prompt, context)
    else:
        toolchain.runAction(primeDirectives, prompt, context)


def switchAiMode(ai_mode: AiMode) -> AiMode:
    if ai_mode == AiMode.NORMAL:
        ai_mode = AiMode.MISSION
        comms.printSystemText(MISSION_MODE_TEXT)
    elif ai_mode == AiMode.MISSION:
        ai_mode = AiMode.NERV
        comms.printSystemText(NERV_MODE_TEXT)
    elif ai_mode == AiMode.NERV:
        ai_mode = AiMode.MAGI
        comms.printSystemText(MAGI_MODE_TEXT)
    else:
        ai_mode = AiMode.NORMAL
        comms.printSystemText(NORMAL_MODE_TEXT)

    return ai_mode


def run_heartbeat(primeDirectives: str, context: list[str]):
    comms.printSystemText(HEARTBEAT_TAG)
    action = core.send_prompt(primeDirectives, HEARTBEAT_PROMPT, context[:], hide_reasoning = True)

    if HEARTBEAT_IDLE_TEXT not in action:
        toolchain.runAction(primeDirectives, action, context)


def print_cli_symbol():
    if not comms.telegram_bot_enabled:
        print(core.USER_COLOR + "\n$ ", end = '', flush = True)


def main() -> int:
    # Import MAGI modules here to prevent them from being imported in subprocesses
    global core, comms, toolchain, agent

    import core as _core
    import comms as _comms
    import toolchain as _toolchain
    import agent as _agent
    import plugin  # noqa: F401

    core, comms, toolchain, agent = _core, _comms, _toolchain, _agent

    context: list[str] = []
    primeDirectives: str = ""
    ai_mode: AiMode = AiMode.NORMAL
    prompt: str = " "
    prompt_tokens: int = 0
    command: str = ""
    heartbeat_seconds: int = 0
    last_heartbeat: float = 0.0
    elapsed_time: float = 0.0

    # Initialize heartbeat
    try:
        heartbeat_seconds = int(core.config.get(HEARTBEAT_SECONDS_KEY, 0))
    except Exception as e:
        print(core.CONFIG_ERROR + str(e) + "\n")

    last_heartbeat = time.time()

    # Initialize Prime Directives
    primeDirectives = core.read_text_file(core.PRIME_DIRECTIVES_FILE_PATH)

    if primeDirectives:
        comms.printSystemText(PRIME_DIRECTIVES_TEXT + primeDirectives)

    # Print system hint
    comms.printSystemText(SYSTEM_HINT_TEXT)

    # Print console prompt
    print_cli_symbol()

    # Main loop
    while True:
        # Check heartbeat
        elapsed_time = time.time() - last_heartbeat

        if heartbeat_seconds > 0 and elapsed_time >= heartbeat_seconds:
            last_heartbeat = time.time()
            run_heartbeat(primeDirectives, context)
            print_cli_symbol()

        # Check user input
        prompt = comms.userInput()

        if not prompt:
            continue

        # Reset heartbeat timer
        last_heartbeat = time.time()

        # Run user prompt
        prompt_tokens = core.get_number_of_tokens(prompt)

        # Check prompt lenght
        if prompt_tokens > core.MAX_INPUT_TOKENS:
            comms.printSystemText(core.MAX_INPUT_TOKENS_ERROR + str(prompt_tokens))
            print_cli_symbol()
            continue

        # Get first word (could be a command)
        command = prompt.split()[0]

        # Check exit command
        if command.upper() == EXIT_COMMAND:
            break

        # Check change AI mode command
        if command.upper() == SWITCH_AI_MODE_COMMAND:
            ai_mode = switchAiMode(ai_mode)
        else:
            checkPrompt(primeDirectives, prompt, context, ai_mode)

        print_cli_symbol()

    comms.printSystemText(EXIT_MAGI_TEXT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
