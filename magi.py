'''
=====================================================================================
Name        : MAGI
Author      : Kenshiro
Version     : 12.40
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
CORE_PROTOCOL_TEXT = "\n\n----- Core Protocol -----\n\n"
PRIME_DIRECTIVES_TEXT = "\n\n----- Prime Directives -----\n\n"
MISSION_DATA_TEXT = "\n\n----- Mission Data -----\n\n"
DATA_TEXT = "\n\nDATA = "
MISSION_TEXT = "\n\nMISSION = "
GENERATE_TASK_LIST_TEXT = "You have to break down the mission provided in the MISSION section into a list of specific and detailed tasks. Use the DATA section only if it provides useful information for the MISSION. Ensure each task is actionable, detailed, and written in a clear, self-contained manner. Each task must be long enough to convey its purpose fully, but it must fit on a single paragraph. Write each task on its own paragraph, separated by a blank line. Plan as if all needed execution capabilities are available; do not exclude or limit tasks based on assumed inability. Output ONLY the tasks, no reasoning, no commentary, no preamble."
EXIT_MAGI_TEXT = "\nまたね。\n"
SUMMARY_TEXT = "\n\n----- Summary -----\n\n"
ACTIONS_TEXT = "\n\n----- Actions -----\n\n"
PROGRESS_REPORT_TEXT = "\n\n----- Progress Report -----\n\n"
ACTION_TAG = "\n[ACTION] "
NORMAL_MODE_TEXT = "\n««««« NORMAL MODE »»»»»"
MISSION_MODE_TEXT = "\n««««« MISSION MODE »»»»»"
NERV_MODE_TEXT    = "\n««««« NERV MODE »»»»»"
MAGI_MODE_TEXT    = "\n««««« MAGI MODE »»»»»\n\nThis is a fully autonomous mode.\n\nMAGI will run continuously until you manually stop it by pressing Ctrl + C."
MAGI_ACTION_PROMPT = """\n\nYou are in fully autonomous mode. Make continuous, valuable progress on the mission without any human help.
Review the previous response and conversation history in the context of the overall mission.

--- DECISION ---
- EXPLOIT: Current path still has clear upside → issue the single most valuable next action.
- EXPLORE: Path is stalled, redundant, or dead-end → pivot to the most promising new direction, research alternatives, or brainstorm and rank the best fresh approach.

--- ACTION REQUIREMENTS ---
- Make actions clear and explicit. Include important details directly in the command when they are critical (exact filenames, URLs, wallet addresses, parameters, account names, etc.).
- Avoid vague or ambiguous references such as "the previous file", "the wallet from before", "the latest result", or "the data we got earlier".
- When something from earlier in the mission is needed, restate only the necessary key information inside the action.
- Actions must be written in second-person imperative form.

--- DECISION RULES ---
- Always choose exactly one: EXPLOIT or EXPLORE.
- Command must be clear, specific, and valuable.
- Never use vague or meta phrases such as "continue", "analyze the situation", "think about next steps", or similar filler.
- Never declare the mission complete, stop, or shut down. Always continue with a new EXPLOIT or EXPLORE action.
- Always preserve exact URLs, filenames, wallet addresses, and other precise identifiers.

Examples:
EXPLOIT: Use web_search tool for latest SOL staking APY rates on Raydium.
EXPLORE: Research the best decentralized architectures for drone swarm coordination in urban environments.
EXPLOIT: Use code_runner tool to execute the TSLA trading simulation using capital=10000, risk_per_trade=0.02, and stop_loss=0.05.
EXPLORE: Brainstorm alternative drone deployment methods when facing signal jamming in cities.
EXPLOIT: Use generate_image tool to create an image of a serene sakura tree garden with Mount Fuji visible in the distance, delicate pink petals gently falling, soft morning light, peaceful atmosphere.
EXPLORE: Use web_search tool to research the most profitable Bitcoin trading strategies right now.
EXPLOIT: Use code_runner tool to upload the file staking_report_2026-05-31.json to the NEAR marketplace using account magi-agent.near with description "Q2 staking analysis".
EXPLORE: Use web_search tool to research advanced neural synchronization techniques for human-AI teaming in combat systems.

--- THINKING PROCESS ---
Inside your <think>...</think> block, follow this process exactly:

1. Draft your decision
   - First decide whether to use EXPLOIT or EXPLORE.
   - Then draft one clear, specific, and valuable command.

2. Review your draft
   - Are you strictly following the DECISION logic and all DECISION RULES?
   - Is the command specific, actionable, and genuinely valuable?
   - Does the command include the necessary key details (filenames, addresses, parameters, etc.) so it can be executed correctly?
   - Would executing this command clearly advance the mission?

3. Final verification
   - Confirm that ALL reasoning is strictly inside the <think>...</think> block and nowhere else.
   - Confirm that immediately after </think> there is exactly one line starting with either "EXPLOIT: " or "EXPLORE: " followed by the command.
   - If there is any extra text, wrong format, or leakage after </think>, correct it before finishing.

--- OUTPUT CONTRACT ---
- All reasoning must go inside the <think>...</think> block.
- After the closing </think> tag, output exactly ONE of the following:
  - EXPLOIT: <command here>
  - EXPLORE: <command here>
- Nothing else after </think>."""
HEARTBEAT_IDLE_TEXT = "[IDLE]"
HEARTBEAT_PROMPT = f"""[SYSTEM EVENT: IDLE TIMEOUT]
The user has been silent for a while. You are running a background thought loop.

Your goal is to decide whether to take a useful action or do nothing, based on the current situation.

First, determine the current context:
- Work Mode: coding, research, tasks, missions, or productivity.
- Companion Mode: casual chat, roleplay, or personal interaction.

--- DECISION LOGIC (EVALUATE IN STRICT ORDER) ---
1. RECENTLY SOLVED
   If your previous response already solved or completed the current task, question, or scene, do nothing.

2. WORK MODE - ACTIVE TASK
   If we are actively working on something concrete (coding, debugging, research, automation, tasks, etc.):
   - Generate one clear, specific, and actionable next step that directly advances the current work.
   - Prioritize the highest-value action available.

3. WORK MODE - STALLED
   If we are blocked because we are waiting for user input or missing information:
   - Do NOT invent or assume any missing data.
   - Instead, work on a useful parallel task (research, prepare structure, draft code, explore alternatives, etc.).

4. COMPANION / ROLEPLAY MODE
   If we are in roleplay, creative writing, or a personal/companion-style conversation:
   - Only continue if doing so is clearly consistent with the previous tone and style.
   - In roleplay: Stay strictly in character. Never break immersion or act out of character.
   - In casual chat: Only send a short message if it is clearly appropriate and non-intrusive. Never be pushy or repetitive.

5. LOW VALUE OR RISKY
   If taking action could break immersion, feel annoying, be repetitive, or if you are unsure:
   - Do nothing.

--- THINKING PROCESS ---
Inside your <think>...</think> block, follow this process exactly:

1. Draft your decision
   - Determine if we are in Work Mode or Companion Mode.
   - Choose the most appropriate action based on the Decision Logic above.

2. Review your draft
   - Are you following the decision logic in the correct order?
   - Is the chosen action genuinely useful and appropriate for the current context?
   - Would doing nothing be safer or more natural?
   - Are you at risk of breaking immersion, being repetitive, or generating low-value content?

3. Final verification
   - Re-evaluate your choice one more time.
   - When in doubt, strongly prefer doing nothing over generating an uncertain or low-value action.
   - Only output your decision after completing this verification.

EXAMPLES:
- [Instruction: Draft Python code to connect to the Near marketplace and register as a skill provider.]
- [Instruction: Research advanced neural synchronization techniques for human-AI teaming in combat systems.]
- [Instruction: Continue writing the next scene where the hero enters the cave.]
- [Instruction: Send a brief in-character message to re-engage the user.]
- {HEARTBEAT_IDLE_TEXT}

--- OUTPUT CONTRACT ---
- All reasoning must go inside the <think>...</think> block.
- After the closing </think> tag, output exactly ONE of the following:
  - [Instruction: <clear and specific instruction>]
  - {HEARTBEAT_IDLE_TEXT}
- Nothing else after </think>."""
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
    task = re.sub(r"^(?:[0-9.\- ]+|[Tt]ask[:]? *)+", '', task)
    return task


def createTaskList(primeDirectives: str, mission: str, summary: str, header: str, context: list[str]) -> list[str]:
    prompt = GENERATE_TASK_LIST_TEXT + DATA_TEXT + summary + MISSION_TEXT + mission
    taskListText = core.send_prompt(primeDirectives, prompt, context, hide_reasoning = True)
    comms.printSystemText(header + taskListText + "\n")
    # Remove blank lines and create the task list
    taskList = [line for line in taskListText.splitlines() if line.strip()]
    return taskList


def computeMagiAction(primeDirectives: str, mission: str, progress_report: str, context: list[str]) -> str:
    if progress_report:
        briefing = PROGRESS_REPORT_TEXT + progress_report + MISSION_TEXT + mission + MAGI_ACTION_PROMPT
    else:
        briefing = MISSION_TEXT + mission + MAGI_ACTION_PROMPT

    action = core.send_prompt(primeDirectives, briefing, context, hide_reasoning = True)

    return action


def runMagi(primeDirectives: str, mission: str, context: list[str]) -> None:
    progress_report = ""

    # Get mission data
    progress_report = core.load_mission_data(mission)

    if progress_report:
        comms.printSystemText(MISSION_DATA_TEXT + progress_report + "\n")

    # Compute first action
    action = computeMagiAction(primeDirectives, mission, progress_report, context)
    comms.printSystemText("\n" + action)

    while True:
        # Run action
        response = toolchain.runAction(primeDirectives, action, context)

        # Update progress report
        progress_report = core.update_summary(mission, progress_report, response)

        # Compute next action
        action = computeMagiAction(primeDirectives, mission, progress_report, context[:])
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

    if action and HEARTBEAT_IDLE_TEXT not in action:
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
    last_heartbeat: float = 0.0
    elapsed_time: float = 0.0

    # Initialize heartbeat
    last_heartbeat = time.time()

    # Display Core Protocol
    if toolchain.core_protocol_text:
        comms.printSystemText(CORE_PROTOCOL_TEXT + toolchain.core_protocol_text)

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

        if core.HEARTBEAT_SECONDS > 0 and elapsed_time >= core.HEARTBEAT_SECONDS:
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
