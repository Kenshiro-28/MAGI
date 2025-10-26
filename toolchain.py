import json
from typing import Callable, Any
import inspect

TOOL_NOT_REGISTERED_ERROR = "[ERROR] Tool is not registered: "
TOOL_NON_CALLABLE_FUNCTION_ERROR = "[ERROR] Tool has non-callable 'function' field: "
TOOL_ADD_ERROR = "[ERROR] Error adding tool: "
TOOL_INVALID_PARAMETER_ERROR = "[ERROR] Invalid function parameter; tool functions cannot use *args or **kwargs: "
TOOL_DUPLICATE_ERROR = "[ERROR] Duplicate tool: "
TOOL_RUN_ERROR = "[ERROR] Error while running tool: "
TOOL_SIGNATURE_ERROR = "[ERROR] Function must accept 3 or 4 parameters: "
TOOL_PARAMETER_TYPE_ERROR = "[ERROR] Parameter {name} has incorrect type: expected {expected}, got {actual} in "

TOOLS: dict[str, dict] = {}


# Functions are expected to have 3 or 4 parameters (is_agent is optional)
# Function signature: (primeDirectives: str, action: str, context: list[str], is_agent: bool)
def _check_function(function: Callable[..., Any]):
    # Check function is callable
    if not callable(function):
        raise TypeError(TOOL_NON_CALLABLE_FUNCTION_ERROR)

    signature = inspect.signature(function)

    # Check arguments are not *args or **kwargs
    for param in signature.parameters.values():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            raise ValueError(TOOL_INVALID_PARAMETER_ERROR + str(function))

    # Get function parameters
    params = list(signature.parameters.values())
    num_params = len(params)

    # Check number of parameters
    if num_params not in (3, 4):
        raise ValueError(TOOL_SIGNATURE_ERROR + str(function))

    # Check parameter types
    expected_types = [str, str, list[str]]

    if num_params == 4:
        expected_types.append(bool)

    for i, param in enumerate(params):
        actual = param.annotation
        expected = expected_types[i]

        if actual != expected:
            raise TypeError(TOOL_PARAMETER_TYPE_ERROR.format(name = param.name, expected = expected, actual = actual) + str(function))


def _get_number_of_parameters(function: Callable[..., Any]):
    signature = inspect.signature(function)
    num_params = len(signature.parameters)

    return num_params


def add_tool(name: str, description: str, function: Callable[..., Any]) -> None:
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
    if not TOOLS:
        return ""

    tool_list = []

    for name, tool in TOOLS.items():
        description = tool.get("description", "No description provided.")
        tool_list.append({"name": name, "description": description})

    return json.dumps(tool_list, indent = 2)


def run_tool(name: str, primeDirectives: str, action: str, context: list[str], is_agent: bool) -> Any:
    tool = TOOLS.get(name)

    if not tool:
        raise KeyError(TOOL_NOT_REGISTERED_ERROR + name)

    function = tool["function"]

    try:
        num_params = _get_number_of_parameters(function)

        if num_params == 4:
            return function(primeDirectives, action, context, is_agent)
        elif num_params == 3:
            return function(primeDirectives, action, context)
        else:
            raise ValueError(TOOL_SIGNATURE_ERROR + str(function))

    except Exception as e:
        raise RuntimeError(TOOL_RUN_ERROR + name + "\n\n" + str(e)) from e

