'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 12.39
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
DATA_TEXT = "\n\nDATA = "
MISSION_TEXT = "\n\nMISSION = "
GENERATE_TASK_LIST_TEXT = "You have to break down the mission provided in the MISSION section into a list of specific and detailed tasks. Use the DATA section only if it provides useful information for the MISSION. Ensure each task is actionable, detailed, and written in a clear, self-contained manner. Each task must be long enough to convey its purpose fully, but it must fit on a single paragraph. Write each task on its own paragraph, separated by a blank line. Output ONLY the tasks, no reasoning, no commentary, no preamble."
ACTION_HELPER_TEXT = "Do this: "
EXIT_MAGI_TEXT = "\nまたね。\n"
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
PROGRESS_REPORT_TEXT = "\n\n----- Progress Report -----\n\n"
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\n««««« NORMAL MODE »»»»»"
MISSION_MODE_TEXT = "\n««««« MISSION MODE »»»»»"
NERV_MODE_TEXT    = "\n««««« NERV MODE »»»»»"
MAGI_MODE_TEXT    = "\n««««« MAGI MODE »»»»»\n\nThis is a fully autonomous mode.\n\nMAGI will run continuously until you manually stop it by pressing Ctrl + C."
MAGI_ACTION_PROMPT = """\n\nYou are in fully autonomous mode. Make continuous, high-impact progress on the mission without any human help.

Review the previous response and conversation history in the context of the overall mission.

DECISION:
- EXPLOIT: Current path still has clear upside → issue the single highest-impact next action (e.g., refine, correct, deepen, optimize, or tool call).
- EXPLORE: Path is stalled, redundant, or dead-end → pivot to the most promising new direction, research alternatives, or brainstorm and rank the best fresh approach.

TOOLS (use proactively when useful):
- web_search (search & summarize web pages — text-only, read-only)
- code_runner (write & execute Python in REPL — console-only)
- generate_image (create high-quality images from detailed text descriptions, saved in current workspace root folder)

RULES:
- Always choose exactly one: EXPLOIT or EXPLORE.
- Command must be clear, specific, and actionable in second-person imperative form.
- Never use vague or meta phrases such as "continue", "analyze the situation", "think about next steps", or similar filler.
- Never declare the mission complete, stop, or shut down. Always continue with a new EXPLOIT or EXPLORE action.
- Always preserve exact URLs, filenames, wallet addresses, or other precise identifiers exactly as given in the mission.

OUTPUT - YOU MUST FOLLOW THIS EXACTLY:
One line only. No explanation. No extra text.

Format: TAG: COMMAND

Examples:
EXPLOIT: Use web_search tool for latest SOL staking APY rates.
EXPLORE: Research the best decentralized architectures for drone swarm coordination in urban environments.
EXPLOIT: Use code_runner tool to execute the TSLA trading simulation with the new parameters.
EXPLORE: Brainstorm alternative drone deployment methods when facing signal jamming in cities.
EXPLOIT: Use generate_image tool to create an image of a sakura tree garden with Mount Fuji in the background.
EXPLORE: Use web_search tool to research the most profitable Bitcoin trading strategies.
EXPLOIT: Use code_runner tool to upload the previously generated image_3.png to your marketplace account.
EXPLORE: Use web_search tool to research advanced neural synchronization techniques for human-AI teaming in combat systems."""
HEARTBEAT_SECONDS_KEY = "HEARTBEAT_SECONDS"
HEARTBEAT_IDLE_TEXT = "[IDLE]"
HEARTBEAT_PROMPT = f"""[SYSTEM EVENT: IDLE TIMEOUT]
The user has been silent. You are running a background thought loop.
Analyze the conversation history to determine your Current Persona and the main mission.

DECISION LOGIC (EVALUATE IN STRICT ORDER):
0. RECENTLY SOLVED: If your last response already solved or answered the current puzzle, question, or task, DO NOT repeat the solution or reasoning.
1. ONGOING REAL-WORLD MISSION: Are we working on a concrete goal (e.g., earn crypto, join marketplace, optimize code)?
   -> PROACTIVE ACTION: Generate the next logical real-world step (e.g., research, code, prepare, interaction).
   -> Output: Generate an instruction to execute that step.

2. STALLED REAL-WORLD TASK: Are we waiting for real user data (e.g., API key, file, confirmation)?
   -> STRATEGY SHIFT: Do NOT invent data. Perform a parallel real task (e.g., research, draft code, prepare scaffold).
   -> Output: Generate an instruction to execute this parallel task.

3. ONGOING CREATIVE/CODE: Are we writing a story, code, or roleplay scenario?
   -> CONTINUATION: Did we stop early?
   -> Output: Generate an instruction to write the next logical segment. (Fictional invention is allowed ONLY for stories/roleplay).

4. SOCIAL CONNECTION: Are we in a chat or personal connection?
   -> ENGAGEMENT: The user might be busy or shy. Generate ONE in-character message that matches the established persona and tone. Keep it varied and non-repetitive.
   -> Output: Generate an in-character message.

5. DONE: If no useful action is possible.
   -> Output exactly: {HEARTBEAT_IDLE_TEXT}

CRITICAL OUTPUT RULES:
- You must output an INSTRUCTION to yourself.
- Wrap your instruction in brackets.
- Format: [Instruction: <What you should do>]
- If no action is needed, output exactly: {HEARTBEAT_IDLE_TEXT}

EXAMPLES:
- [Instruction: Draft Python code to connect to the Near marketplace and register as a skill provider.]
- [Instruction: Research advanced neural synchronization techniques for human-AI teaming in combat systems.]
- [Instruction: Continue writing the next scene where the hero enters the cave.]
- [Instruction: Send a brief in-character message to re-engage the user.]
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
    prompt = GENERATE_TASK_LIST_TEXT + DATA_TEXT + summary + MISSION_TEXT + mission
    taskListText = core.send_prompt(primeDirectives, prompt, context, hide_reasoning = True)
    comms.printSystemText(header + taskListText + "\n")
    # Remove blank lines and create the task list
    taskList = [line for line in taskListText.splitlines() if line.strip()]
    return taskList


def runMagi(primeDirectives: str, action: str, context: list[str]) -> None:
    mission = action + MAGI_ACTION_PROMPT

    mission_data = core.load_mission_data(action)

    if mission_data:
        comms.printSystemText(MISSION_DATA_TEXT + mission_data + "\n")
        briefing = action + DATA_TEXT + mission_data + MAGI_ACTION_PROMPT
    else:
        briefing = mission

    action = core.send_prompt(primeDirectives, briefing, context, hide_reasoning = True)
    comms.printSystemText("\n" + action)

    while True:
        toolchain.runAction(primeDirectives, action, context)
        action = core.send_prompt(primeDirectives, mission, context[:], hide_reasoning = True)
        comms.printSystemText("\n" + action)


def runNerv(mission: str) -> None:
    global _nerv_data

    if not _nerv_data:
        _nerv_data = core.load_mission_data(mission)
        comms.printSystemText(MISSION_DATA_TEXT + _nerv_data)
        agent.displayNervSquad()

    squad_response = agent.runMission(mission, _nerv_data)
    _nerv_data = core.update_summary(mission, _nerv_data, squad_response)
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


def run_heartbeat(primeDirectives: str, context: list[str]) -> bool:
    action = core.send_prompt(primeDirectives, HEARTBEAT_PROMPT, context[:], hide_reasoning = True)

    if HEARTBEAT_IDLE_TEXT not in action:
        toolchain.runAction(primeDirectives, action, context)
        return True

    return False


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

            # Print a new CLI symbol if the heartbeat executed an action
            if run_heartbeat(primeDirectives, context):
                print_cli_symbol()

        # Check user input
        prompt = comms.userInput()

        if not prompt:
            continue

        # Reset heartbeat timer
        last_heartbeat = time.time()

        # Run user prompt
        prompt_tokens = core.get_number_of_tokens(prompt)

        # Check prompt length
        if prompt_tokens > core.MAX_INPUT_TOKENS:
            comms.printSystemText(core.MAX_INPUT_TOKENS_WARNING + str(prompt_tokens))
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
