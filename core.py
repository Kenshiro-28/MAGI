import os
import sys
import time
import re
import datetime
import select
from llama_cpp import Llama
from collections.abc import Iterator

SYSTEM_VERSION_TEXT = "\nSystem: v12.29"

SYSTEM_TEXT = "<|im_start|>system\n"
USER_TEXT = "<|im_start|>user\n"
ASSISTANT_TEXT = "<|im_start|>assistant\n"
EOS = "\n<|im_end|>\n"

SUMMARIZE_SYSTEM_PROMPT = "You are a summarizer. Summarize ONLY the information relevant to the TOPIC at the end. If the TOPIC includes output rules or a required format, follow it exactly. Do NOT invent facts, numbers, dates, names, or attribution. Preserve names/numbers/dates exactly. Prefer clear, self-contained bullet points OR clear sentences (choose whichever fits the TOPIC). Include enough context in each point/sentence to be understandable on its own (avoid vague pronouns when possible). Do not over-compress: keep key qualifiers, quantities, and constraints that affect meaning. Avoid preamble unless TOPIC asks; if you add one, keep it to a single short line. If the input contains PREVIOUS_SUMMARY and NEW_TEXT, keep relevant facts from PREVIOUS_SUMMARY and integrate relevant new facts from NEW_TEXT."

SUMMARIZE_TEXT = "\n\nTOPIC:\n"
PREVIOUS_SUMMARY = "PREVIOUS_SUMMARY:\n"
NEW_TEXT = "\n\nNEW_TEXT:\n"

PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
MISSION_LOG_FILE_PATH = "mission_log.txt"
MISSION_DATA_FILE_PATH = "mission_data.txt"
CONFIG_FILE_PATH = "config.cfg"

MODEL_TEXT = "\nModel: "
MODEL_RESPONSE_ERROR = "\n[ERROR] An exception occurred while trying to get a response from the model: "
MODEL_RESPONSE_FORMAT_ERROR = "\n[ERROR] Response format error."
MODEL_NOT_FOUND_ERROR = "\n[ERROR] Model not found.\n"
MODEL_LOAD_ERROR = "\n[ERROR] Error loading model: "

TEMPERATURE = 0.0
TEMPERATURE_KEY = "TEMPERATURE"
TEMPERATURE_NOT_FOUND_TEXT = "Temperature not found.\n"
TEMPERATURE_INVALID_TEXT = "Invalid temperature.\n"

CONTEXT_SIZE = 0
MAX_INPUT_TOKENS = 0
MIN_CONTEXT_SIZE = 32768
MIN_RESPONSE_SIZE = 16384
MAX_RESPONSE_SIZE = 32768
CONTEXT_SIZE_KEY = "CONTEXT_SIZE"
CONTEXT_SIZE_NOT_FOUND_TEXT = "Context size not found.\n"
CONTEXT_SIZE_INVALID_TEXT = "Invalid context size.\n"
MAX_INPUT_TOKENS_WARNING = "\n[WARNING] You have exceeded optimal input tokens: "

DISPLAY_EXTENDED_REASONING = True
DISPLAY_EXTENDED_REASONING_KEY = "DISPLAY_EXTENDED_REASONING"

READ_TEXT_FILE_WARNING = "\n[WARNING] File not found: "

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 3000

CONFIG_ERROR = "\n[ERROR] Configuration error: "

CONSOLE_INPUT_TIMEOUT = 0.1  # Seconds
CONSOLE_OUTPUT_SPEED = 0.045  # Seconds per char

THINK_START = "<think>"
THINK_END = "</think>"
THINK_PATTERN = re.compile(
    rf'({re.escape(THINK_START)}.*?{re.escape(THINK_END)}\n?)',
    flags=re.DOTALL
)


LOG_ENABLED = False
ENABLE_LOG_KEY = "ENABLE_LOG"

model: Llama = None
config: dict[str, str] = {}


def split_text_in_blocks(text: str) -> list[str]:
    index = 0
    blockArray = []

    wordList = text.split()

    while index < len(wordList):
        limit = index + TEXT_BLOCK_WORDS
        block = " ".join(wordList[index:limit])
        blockArray.append(block)
        index += TEXT_BLOCK_WORDS

    return blockArray


def get_number_of_tokens(text: str) -> int:
    tokenized_text = model.tokenize(text.encode('utf-8'))
    text_tokens = len(tokenized_text)

    return text_tokens


def get_context_data(context: list[str]) -> tuple[str, int]:
    text = ''.join(context)
    text_tokens = get_number_of_tokens(text)

    return text, text_tokens


def get_completion_from_messages(context: list[str]) -> str:
    try:
        # Get context data
        text, text_tokens = get_context_data(context)

        # Check context size
        while len(context) > 3 and text_tokens > MAX_INPUT_TOKENS:
            context.pop(1)
            context.pop(1)
            text, text_tokens = get_context_data(context)

        # Catch oversized initial prompt
        if text_tokens > MAX_INPUT_TOKENS:
            print_system_text(MAX_INPUT_TOKENS_WARNING + str(text_tokens))

        # Compute response token limit
        max_tokens = min(CONTEXT_SIZE - text_tokens, MAX_RESPONSE_SIZE)

        # Get model response
        response = model(text, max_tokens = max_tokens, temperature = TEMPERATURE, stream = False)

        # Check response format
        if isinstance(response, Iterator):
            raise ValueError(MODEL_RESPONSE_FORMAT_ERROR)

        return response['choices'][0]['text'].strip()

    except Exception as e:
        error = MODEL_RESPONSE_ERROR + str(e)
        print_system_text(error)
        exit()


def remove_reasoning(response: str) -> str:
    # Remove complete <think>...</think> blocks
    response = THINK_PATTERN.sub('', response)

    # Clean up any stray <think> or </think> tags
    response = response.replace(THINK_START, '').replace(THINK_END, '')

    return response.strip()


def send_prompt(primeDirectives: str, prompt: str, context: list[str], hide_reasoning: bool = False) -> str:
    # Sanitize input
    primeDirectives = primeDirectives.strip()
    prompt = prompt.strip()

    # Format Prime Directives
    primeDirectives = SYSTEM_TEXT + primeDirectives + EOS

    # Set Prime Directives in context
    if context:
        context[0] = primeDirectives
    else:
        context.append(primeDirectives)

    # Format prompt
    command = USER_TEXT + prompt + EOS + ASSISTANT_TEXT

    # Append prompt to context
    context.append(command)

    # Process the updated context
    full_response = get_completion_from_messages(context)

    # Remove extended reasoning from response
    response = remove_reasoning(full_response)

    # Add response to context
    context.append(response + EOS)

    # Return the full response if required
    if DISPLAY_EXTENDED_REASONING and not hide_reasoning:
        return full_response
    else:
        return response


def print_system_text(text: str) -> None:
    print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)

    if LOG_ENABLED:
        save_mission_log(text)


def print_magi_text(text: str) -> None:
    print(END_COLOR + MAGI_COLOR, end='')

    for char in text:
        print(char, end='', flush=True)
        time.sleep(CONSOLE_OUTPUT_SPEED)

    print(END_COLOR)

    if LOG_ENABLED:
        save_mission_log(text)


def save_mission_log(text: str) -> None:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Use regex to insert timestamp after any leading newlines
    log_entry = re.sub(r'^(\n*)', r'\1[{}] '.format(timestamp), text)

    with open(MISSION_LOG_FILE_PATH, 'a') as missionFile:
        missionFile.write(log_entry + "\n")


def user_input() -> str:
    """
    Non-blocking read. Returns the input string ONLY if the user has pressed Enter.
    Otherwise returns an empty string.
    """
    text: str = ""

    # Ensure any previous stdout (like the prompt cursor) is visible
    sys.stdout.flush()

    # Check if stdin has data waiting
    ready, _, _ = select.select([sys.stdin], [], [], CONSOLE_INPUT_TIMEOUT)

    if ready:
        try:
            text = sys.stdin.readline().strip()

            if LOG_ENABLED:
                save_mission_log("\n" + text)

        except Exception:
            return ""

    return text


def summarize(topic: str, text: str) -> str:
    context: list[str] = []

    summary = send_prompt(SUMMARIZE_SYSTEM_PROMPT, text + SUMMARIZE_TEXT + topic, context, hide_reasoning = True)

    return summary


def update_summary(topic: str, summary: str, text: str) -> str:
    if not text:
        return summary

    if not summary:
        return text

    merged = PREVIOUS_SUMMARY + summary + NEW_TEXT + text

    return summarize(topic, merged)


def summarize_block_array(topic: str, blockArray: list[str]) -> str:
    summary = ""

    # Summarize
    for block in blockArray:
        summary = update_summary(topic, summary, block)

    return summary


def binary_question(primeDirectives: str, question: str, context: list[str]) -> bool:
    aux_context = context[:]

    response = send_prompt(primeDirectives, question, aux_context, hide_reasoning = True)

    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Clean the last line
    last_line = last_line.upper().replace(".", "").replace("'", "").replace("\"", "").strip()

    # Check answer
    if "YES" in last_line:
        return True
    else:
        return False


def load_mission_data(prompt: str) -> str:
    missionData = read_text_file(MISSION_DATA_FILE_PATH)

    if len(missionData.split()) > TEXT_BLOCK_WORDS:
        blockArray = split_text_in_blocks(missionData)
        summary = summarize_block_array(prompt, blockArray)
    else:
        summary = missionData

    return summary


def read_text_file(path: str) -> str:
    try:
        with open(path) as textFile:
            text = textFile.read().strip()
            return text

    except FileNotFoundError:
        print_system_text(READ_TEXT_FILE_WARNING + str(path))
        return ""


def load_model(startup: bool = True) -> None:
    global model
    model = None

    try:
        fileArray = sorted(os.listdir())

        # Filter for model files
        modelFileArray = [f for f in fileArray if f.endswith('.gguf')]

        if not modelFileArray:
            print_system_text(MODEL_NOT_FOUND_ERROR)
            exit()

        # Get the first model file
        modelFile = modelFileArray[0]

        # Get the file name without the .gguf extension
        modelName = os.path.splitext(modelFile)[0]

        print()

        # Load model
        model = Llama(
            model_path = modelFile,
            n_ctx = CONTEXT_SIZE,
            n_gpu_layers = -1,
            verbose = False
        )

        if startup:
            print_system_text(SYSTEM_VERSION_TEXT)
            print_system_text(MODEL_TEXT + modelName)

            # Print config
            config_info = (
                f"\nContext: {CONTEXT_SIZE:,} tokens\n"
                f"\nTemperature: {TEMPERATURE}"
            )

            print_system_text(config_info)

    except Exception as e:
        print_system_text(MODEL_LOAD_ERROR + str(e))
        exit()


def unload_model() -> None:
    global model

    if model is not None:
        model.close()
        model = None


def load_config() -> None:
    global config

    try:
        with open(CONFIG_FILE_PATH, 'r') as file:
            for line in file:
                # Remove any leading/trailing white spaces
                line = line.strip()

                # Skip invalid lines
                if not line or line.startswith('#') or line.count('=') == 0:
                    continue

                # Split each line into a key-value pair
                key, value = line.split('=', 1)

                # Remove any leading/trailing white spaces from key and value
                key = key.strip()
                value = value.strip()

                # Add to dictionary
                config[key] = value

    except Exception as e:
        print_system_text(CONFIG_ERROR + str(e) + "\n")


def configure_model() -> None:
    global TEMPERATURE
    global CONTEXT_SIZE
    global MAX_INPUT_TOKENS
    global LOG_ENABLED
    global DISPLAY_EXTENDED_REASONING

    # Set model temperature
    temperature = config.get(TEMPERATURE_KEY, '')

    if not temperature:
        print_system_text(CONFIG_ERROR + TEMPERATURE_NOT_FOUND_TEXT)
        exit()

    try:
        TEMPERATURE = float(temperature)

    except ValueError:
        print_system_text(CONFIG_ERROR + TEMPERATURE_INVALID_TEXT)
        exit()

    # Set context size
    context_size = config.get(CONTEXT_SIZE_KEY, '')

    if not context_size:
        print_system_text(CONFIG_ERROR + CONTEXT_SIZE_NOT_FOUND_TEXT)
        exit()

    try:
        CONTEXT_SIZE = int(context_size)

    except ValueError:
        print_system_text(CONFIG_ERROR + CONTEXT_SIZE_INVALID_TEXT)
        exit()

    # Check minimum context size
    if CONTEXT_SIZE < MIN_CONTEXT_SIZE:
        print_system_text(CONFIG_ERROR + CONTEXT_SIZE_INVALID_TEXT)
        exit()

    # Set max input tokens
    MAX_INPUT_TOKENS = CONTEXT_SIZE - MIN_RESPONSE_SIZE

    # Set logging configuration
    LOG_ENABLED = config.get(ENABLE_LOG_KEY, "NO").upper() == "YES"

    # Set extended reasoning configuration
    DISPLAY_EXTENDED_REASONING = config.get(DISPLAY_EXTENDED_REASONING_KEY, "YES").upper() == "YES"


# Initialize
load_config()
configure_model()
load_model()
