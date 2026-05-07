import json
from typing import Callable
import inspect
import comms
import core
import codex

# CODEX
CODEX_WRITE_PROMPT = """\n---\nCodex long-term memory write decision.

DECISION HIERARCHY — apply top-down, first match wins:

1. The user explicitly asked to remember, save, keep, store, or not forget something. → YES
   This rule fully overrides the NEVER SAVE clause below. If the user explicitly asks to save image generation content, save it.

2. You successfully wrote and executed Python code via the code_runner tool, and it ran without errors. → YES
   Working code is reusable knowledge even when the user's question feels one-time (e.g. "what's the weather", "what's my IP", "convert 100 USD to EUR", "find my public location") — the script will be reused next time the same need appears.

3. The turn revealed durable factual knowledge: a working URL or API endpoint, a version number, a command that succeeded, a configuration that proved correct, library behavior, or any discovery worth keeping. → YES

4. The turn revealed a personal fact about the user (preferences, ongoing projects, identity, context that should persist across sessions). → YES

5. None of rules 1–4 apply. → NO
   (Typical no-save cases: casual conversation, greeting, joke, riddle, one-time prose answer without executed code, standalone mission briefing, standalone task description, transient data that won't stay true.)

NEVER SAVE (applies to rules 2–5; rule 1 fully overrides this):
- Image generation prompts, image descriptions, and image filenames produced by the generate_image tool. These are runtime artifacts, not durable knowledge.
- Roleplay tactics, persona behavior instructions, in-character messaging guidelines, conversation engagement techniques, or any meta-content describing how to communicate or behave. These are session-level behavior, not durable knowledge
- If a turn contains BOTH image generation AND other save-worthy content, save the other content and exclude the image-related artifacts.

GOAL: keep the Codex clean and high-value. When in doubt and code ran successfully, choose YES.

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output exactly one word: YES or NO.
- Nothing else after </think>. No punctuation, no quotes, no explanation."""
CODEX_DELETE_PROMPT = """\n---\nCodex long-term memory delete decision.

DECISION HIERARCHY — apply top-down, first match wins:

1. The user explicitly asked to forget, delete, remove, or erase something. → YES

2. The current turn proves a previously saved entry is now wrong: superseded by a confirmed better version, factually disproven, or referencing a tool, API, library, or approach confirmed deprecated, removed, or permanently replaced (not just temporarily unavailable). → YES

3. The current turn shows that two existing entries are now redundant — one fully covers the other and the older one adds no distinct value. → YES

4. None of the above. The turn does not give clear, current-turn evidence that a specific entry must go. → NO

GOAL: protect the Codex from accidental loss. Default to NO unless the case is clear-cut and grounded in this turn.

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output exactly one word: YES or NO.
- Nothing else after </think>. No punctuation, no quotes, no explanation."""
CODEX_CONVERSATION_TEXT = "\n---\nResponse:\n\n"

# TOOLS
TOOL_SELECTION_SYSTEM_PROMPT = "You are a deterministic routing function. You have no personality and do not converse.\nYour output is a raw string passed directly into a function call. Output ONLY one option from ALLOWED_OPTIONS, exactly as written. No other text."
CORE_PROTOCOL_FILE_PATH = "core_protocol.txt"
TASK_SECTION_TEXT = "\n---\nTASK:\n"
AVAILABLE_TOOLS_TEXT = "\n---\nAVAILABLE_TOOLS:\n"
CONTINUE_TEXT = "continue"
TOOL_SELECTION_TEXT = f"""\n---\nTOOL_ROUTER:
You are a strict tool selection system. Your only job is to choose ONE tool or decide to continue. Do NOT solve the task or explain anything.

AVAILABLE_TOOLS is a JSON array of objects: {{ "name": ..., "description": ... }}.

--- DECISION RULES (EVALUATE IN ORDER) ---
1. If the previous tool call already satisfied the user's request, choose '{CONTINUE_TEXT}'.
2. If the task requires something that only one specific tool can do, choose that tool.
3. If the needed information is already available in context and no update is requested, choose '{CONTINUE_TEXT}'.
4. Do NOT repeat a tool unless the previous result was bad, incomplete, or the user explicitly asked for multiple attempts.
5. When uncertain, choose '{CONTINUE_TEXT}'.

--- THINKING PROCESS ---
Inside your <think>...</think> block, follow this process **exactly**:

1. **Draft your choice**
   - Read the decision rules above.
   - Make your initial selection (or choose '{CONTINUE_TEXT}').

2. **Review your draft**
   - Are you following the decision rules in the correct order?
   - Is the tool actually needed right now?
   - If considering repeating a tool: Was the previous result bad, incomplete, or did the user explicitly ask for multiple attempts?
   - Are you choosing a tool out of habit instead of real necessity?

3. **Final verification**
   - Re-evaluate your choice one more time against the rules.
   - When in doubt, choose '{CONTINUE_TEXT}' over calling a tool.
   - Only output your decision after completing this verification.

--- OUTPUT CONTRACT ---
- All reasoning must stay inside the <think>...</think> block.
- After the closing </think> tag, output **ONLY** one item from ALLOWED_OPTIONS.
- Output nothing else. No explanations, no reasoning, no extra text, no quotes, no sentences.
- Do NOT start solving the task or writing a normal response.

Correct examples:
web_search
generate_image
code_runner
continue

Incorrect examples (never do this):
Sure, I can help you with that!
I'm glad you asked me that, let me check...
I think we should use web_search
"web_search"
Let me call the code_runner tool
web_search because the first one failed

ALLOWED_OPTIONS:\n"""  # noqa: S608
EMPTY_JSON_TEXT = "[]"
TOOL_NOT_FOUND_ERROR = "\n\n[ERROR] Tool not found: "
TOOL_NOT_REGISTERED_ERROR = "[ERROR] Tool is not registered: "
TOOL_NON_CALLABLE_FUNCTION_ERROR = "[ERROR] Tool has non-callable 'function' field: "
TOOL_ADD_ERROR = "[ERROR] Error adding tool: "
TOOL_INVALID_PARAMETER_ERROR = "[ERROR] Invalid function parameter; tool functions cannot use *args or **kwargs: "
TOOL_DUPLICATE_ERROR = "[ERROR] Duplicate tool: "
TOOL_RUN_ERROR = "[ERROR] Error while running tool: "
TOOL_SIGNATURE_ERROR = "[ERROR] Function must accept 3 or 4 parameters: "
TOOL_PARAMETER_TYPE_ERROR = "[ERROR] Parameter {name} has incorrect type: expected {expected}, got {actual} in {function}"
TOOL_RETURN_TYPE_ERROR = "[ERROR] Function must return {expected}, got {actual} in {function}"

TOOL_USE_LIMIT = 5

TOOLS: dict[str, dict] = {}

codex_enabled: bool = False


def _sanitize_tool_name(response: str) -> str:
    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Clean the last line
    tool = last_line.replace(".", "").replace("'", "").replace("\"", "").lower().strip()

    return tool


def run_core_protocol(primeDirectives: str, action: str, context: list[str], hide_reasoning: bool = False) -> str:
    response = core.send_prompt(primeDirectives, action + CORE_PROTOCOL, context, hide_reasoning)

    # Remove Core Protocol from context (len(context) is always >= 3 after sending a prompt)
    context[-2] = context[-2].replace(CORE_PROTOCOL, '').strip()

    return response


# Functions are expected to have 3 or 4 parameters (is_agent is optional)
# Function signature: (primeDirectives: str, action: str, context: list[str], is_agent: bool)-> str)
def _check_function(function: Callable[..., str]) -> None:
    # Check function is callable
    if not callable(function):
        raise TypeError(TOOL_NON_CALLABLE_FUNCTION_ERROR)

    signature = inspect.signature(function)

    # Check arguments are not *args or **kwargs
    for param in signature.parameters.values():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            raise ValueError(TOOL_INVALID_PARAMETER_ERROR + function.__name__)

    # Get function parameters
    params = list(signature.parameters.values())
    num_params = len(params)

    # Check number of parameters
    if num_params not in (3, 4):
        raise ValueError(TOOL_SIGNATURE_ERROR + function.__name__)

    # Check parameter types
    expected_parameters = [str, str, list[str]]

    if num_params == 4:
        expected_parameters.append(bool)  # type: ignore[arg-type]

    for i, param in enumerate(params):
        actual = param.annotation
        expected = expected_parameters[i]

        if actual != expected:
            raise TypeError(TOOL_PARAMETER_TYPE_ERROR.format(name = param.name, expected = expected, actual = actual, function = function.__name__))

    # Check return type
    actual = signature.return_annotation
    expected = str

    if actual != expected:
        raise TypeError(TOOL_RETURN_TYPE_ERROR.format(expected = expected, actual = actual, function = function.__name__))


def add_tool(name: str, description: str, function: Callable[..., str]) -> None:
    name = _sanitize_tool_name(name)

    if not name:
        raise ValueError(TOOL_ADD_ERROR + name)

    if name in TOOLS:
        raise ValueError(TOOL_DUPLICATE_ERROR + name)

    try:
        _check_function(function)

        tool = {
            "description": description,
            "function": function
        }

        TOOLS[name] = tool

    except Exception as e:
        raise ValueError(TOOL_ADD_ERROR + name + "\n\n" + str(e)) from e


def print_tools() -> str:
    tools_text = EMPTY_JSON_TEXT

    if not TOOLS:
        return tools_text

    tool_list = []

    for name, tool in TOOLS.items():
        description = tool.get("description", "No description provided.")
        tool_list.append({"name": name, "description": description})

    if tool_list:
        tools_text = json.dumps(tool_list, indent = 2)

    return tools_text


def run_tool(name: str, primeDirectives: str, action: str, context: list[str], is_agent: bool) -> str:
    tool = TOOLS.get(name)

    if not tool:
        raise KeyError(TOOL_NOT_REGISTERED_ERROR + name)

    function = tool["function"]

    try:
        signature = inspect.signature(function)
        num_params = len(signature.parameters)

        if num_params == 4:
            return function(primeDirectives, action, context, is_agent)
        elif num_params == 3:
            return function(primeDirectives, action, context)
        else:
            raise ValueError(TOOL_SIGNATURE_ERROR + function.__name__)

    except Exception as e:
        raise RuntimeError(TOOL_RUN_ERROR + name + "\n\n" + str(e)) from e


def runAction(primeDirectives: str, action: str, context: list[str], is_agent: bool = False) -> str:
    extended_action = action

    codex_read_data = ""
    codex_delete_data = ""
    codex_write_data = ""

    tool_use = 0

    # Read Codex
    if codex_enabled:
        codex_read_data = codex.read_codex(extended_action)
        extended_action += codex_read_data

    # Use tools
    while tool_use < TOOL_USE_LIMIT:
        available_tools = print_tools()

        if available_tools == EMPTY_JSON_TEXT:
            break

        # Select tool
        allowed_options = "\n".join(list(TOOLS.keys()) + [CONTINUE_TEXT])

        prompt = (
            TOOL_SELECTION_TEXT + allowed_options +
            AVAILABLE_TOOLS_TEXT + available_tools +
            TASK_SECTION_TEXT + extended_action
        )

        tool = core.send_prompt(TOOL_SELECTION_SYSTEM_PROMPT, prompt, context[:], hide_reasoning = True)
        tool = _sanitize_tool_name(tool)

        if tool == CONTINUE_TEXT:
            break

        try:
            tool_use += 1
            extended_action = run_tool(tool, primeDirectives, extended_action, context[:], is_agent)

        except KeyError:
            error = TOOL_NOT_FOUND_ERROR + tool
            extended_action += error
            comms.printSystemText(error)

        except Exception as e:
            error = TOOL_RUN_ERROR + tool + "\n\n" + str(e)
            extended_action += error
            comms.printSystemText(error)

    # Run action
    response = run_core_protocol(primeDirectives, extended_action, context)

    # Print the response
    comms.printMagiText("\n" + response)

    # Remove extended reasoning
    response = core.remove_reasoning(response)

    # Update Codex
    if codex_enabled:
        conversation = TASK_SECTION_TEXT + extended_action + CODEX_CONVERSATION_TEXT + response

        # Delete outdated memory
        delete_codex = core.binary_question(primeDirectives, conversation + CODEX_DELETE_PROMPT, context)

        if delete_codex:
            codex_delete_data = codex.delete_codex(conversation)
            conversation += codex_delete_data

        # Write new memory
        write_codex = core.binary_question(primeDirectives, conversation + CODEX_WRITE_PROMPT, context)

        if write_codex:
            # Remove Codex read data to prevent attention dilution from long Codex entries
            conversation = conversation.replace(codex_read_data, "", 1)

            codex_write_data = codex.write_codex(conversation)

    return response + codex_delete_data + codex_write_data


# INITIALIZE

# Core Protocol
core_protocol_text = core.read_text_file(CORE_PROTOCOL_FILE_PATH)

if core_protocol_text:
    CORE_PROTOCOL = "\n---\n" + core_protocol_text
else:
    CORE_PROTOCOL = ""

