import json
from typing import Callable
import inspect
import comms
import core

TOOL_SELECTION_SYSTEM_PROMPT = "You are an AI assistant focused on tool selection. Reason step-by-step as instructed in the user prompt."
CORE_PROTOCOL_FILE_PATH = "core_protocol.txt"
TASK_SECTION_TEXT = "\n---\nTASK: "
AVAILABLE_TOOLS_TEXT = "\n---\nAVAILABLE TOOLS: "
CONTINUE_TEXT = "continue"
TOOL_SELECTION_TEXT = f"""\n---\nTOOL SELECTION: Review the task description above, the provided conversation history, and the list of available tools. Follow these steps:

Step 1: Determine if any tool is necessary to complete or advance the task, considering information gaps, requirements, enhancements from history, or if the task can be resolved with existing knowledge.

Step 2: If a tool is needed, select the single best match by comparing the task to each tool's description. Evaluate based on:
   - Relevance: Direct alignment with the task's core needs.
   - Specificity: Prefer tools that precisely address the gap over general ones.
   - Tie-breaker: If multiple seem equally suitable, prefer the first listed tool.
   Only choose from the listed tools—do not invent new ones. Select only one tool per evaluation; chaining happens automatically if needed.

Step 3: If no tool is suitable, none is required, or the task can proceed without one, select '{CONTINUE_TEXT}'.

Reason step-by-step based on these steps. Then, on the final line, output ONLY the exact tool name (no additional text) or '{CONTINUE_TEXT}' to proceed without a tool."""  # noqa: S608
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


def _sanitize_tool_name(response: str) -> str:
    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Clean the last line
    tool = last_line.replace(".", "").replace("'", "").replace("\"", "").lower().strip()

    return tool


def run_core_protocol(primeDirectives: str, action: str, context: list[str], hide_reasoning: bool = False) -> str:
    response = core.send_prompt(primeDirectives, CORE_PROTOCOL + action, context, hide_reasoning)

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

    tool_use = 0

    # Use tools
    while tool_use < TOOL_USE_LIMIT:
        available_tools = print_tools()

        if available_tools == EMPTY_JSON_TEXT:
            break

        # Select tool
        prompt = TASK_SECTION_TEXT + extended_action + AVAILABLE_TOOLS_TEXT + available_tools + TOOL_SELECTION_TEXT
        tool = core.send_prompt(TOOL_SELECTION_SYSTEM_PROMPT, prompt, context, hide_reasoning = True)
        tool = _sanitize_tool_name(tool)

        if tool == CONTINUE_TEXT:
            break

        try:
            tool_use += 1
            extended_action = run_tool(tool, primeDirectives, extended_action, context, is_agent)

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

    return response


# INITIALIZE

# Core Protocol
core_protocol_text = core.read_text_file(CORE_PROTOCOL_FILE_PATH)

if core_protocol_text:
    CORE_PROTOCOL = core_protocol_text + TASK_SECTION_TEXT
else:
    CORE_PROTOCOL = ""


