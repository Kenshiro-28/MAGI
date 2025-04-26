from llama_cpp import Llama
import os
import sys
import time
import re
import datetime

SYSTEM_VERSION_TEXT = "\n\nSystem: v12.01"

SYSTEM_TEXT = "<|im_start|>system\n"
USER_TEXT = "<|im_start|>user\n"
ASSISTANT_TEXT = "<|im_start|>assistant\n"
EOS = "\n<|im_end|>\n"

TEMPERATURE = 0.6

THINK_TEXT = "<think>\n"

SUMMARIZE_SYSTEM_PROMPT = """You are an expert assistant specialized in text summarization. Your task is to generate a concise and accurate summary of the provided text, focusing strictly on the topic specified at the end of the user prompt.

When the provided text includes new information following an earlier summary, integrate the relevant details from the new information, while ensuring all key information relevant to the topic from the earlier text is carried forward and included. Ensure the final summary is comprehensive and accurately reflects all relevant points gathered so far.

Output only the final, unified summary text."""

SUMMARIZE_TEXT = "\n\nSummarize the information from the above text that is relevant to this topic: "

PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
MISSION_LOG_FILE_PATH = "mission_log.txt"
MISSION_DATA_FILE_PATH = "mission_data.txt"
CONFIG_FILE_PATH = "config.cfg"

MODEL_TEXT = "\nModel: "
MODEL_ERROR_TEXT = "\n[WARNING] An exception occurred while trying to get a response from the model: "
MODEL_NOT_FOUND_ERROR = "\n[ERROR] Model not found.\n"
MODEL_LOAD_ERROR = "\n[ERROR] Error loading model: "

CONTEXT_SIZE = 0
MAX_INPUT_TOKENS = 0
MAX_INPUT_TOKENS_ERROR = "\n[ERROR] You have entered too many tokens: "
MAX_RESPONSE_SIZE = 16384
MIN_CONTEXT_SIZE = MAX_RESPONSE_SIZE * 2
CONTEXT_SIZE_KEY = "CONTEXT_SIZE"
CONTEXT_SIZE_NOT_FOUND_TEXT = "Context size not found.\n"
CONTEXT_SIZE_INVALID_TEXT = "Invalid context size.\n"

DISPLAY_EXTENDED_REASONING = True
DISPLAY_EXTENDED_REASONING_KEY = "DISPLAY_EXTENDED_REASONING"

READ_TEXT_FILE_WARNING = "\n[WARNING] File not found: "

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 4000

CONFIG_ERROR = "\n[ERROR] Configuration error: "

MAGI_TEXT_SLEEP_TIME = 0.045 # Sleep seconds per char

THINK_PATTERN = re.compile(r'(<think>.*?</think>\n)|(<think>.*?</think>)', flags=re.DOTALL)

LOG_ENABLED = False
ENABLE_LOG_KEY = "ENABLE_LOG"

model = None
config = None


def split_text_in_blocks(text):
    index = 0
    blockArray = []
    
    wordList = text.split()

    while index < len(wordList):
        limit = index + TEXT_BLOCK_WORDS
        block = " ".join(wordList[index:limit])
        blockArray.append(block)
        index += TEXT_BLOCK_WORDS

    return blockArray


def get_number_of_tokens(text):
    tokenized_text = model.tokenize(text.encode('utf-8'))
    text_tokens = len(tokenized_text)
    
    return text_tokens
    

def get_context_data(context):
    text = ''.join(context)
    text_tokens = get_number_of_tokens(text)
    
    return text, text_tokens
    
    
def get_completion_from_messages(context):
    try:
        text, text_tokens = get_context_data(context)
        
        # Check context size
        while len(context) > 3 and text_tokens > MAX_INPUT_TOKENS:
            context.pop(1)
            context.pop(1)
            text, text_tokens = get_context_data(context)

        max_tokens = min(CONTEXT_SIZE - text_tokens, MAX_RESPONSE_SIZE)

        response = model(text, max_tokens = max_tokens, temperature = TEMPERATURE)

        return response['choices'][0]['text'].strip()
        
    except Exception as e:
        print_system_text(MODEL_ERROR_TEXT + str(e)) 
        return ""


def remove_reasoning(response):
    # Remove complete <think>...</think> blocks
    response = THINK_PATTERN.sub('', response)

    # Clean up any stray <think> or </think> tags
    response = response.replace('<think>', '').replace('</think>', '')

    return response.strip()


def send_prompt(primeDirectives, prompt, context, hide_reasoning = False):
    primeDirectives = SYSTEM_TEXT + primeDirectives + EOS

    if context:
        context[0] = primeDirectives
    else:
        context.append(primeDirectives)

    command = USER_TEXT + prompt + EOS + ASSISTANT_TEXT

    # Append THINK_TEXT to trigger extended reasoning
    context.append(command + THINK_TEXT)

    full_response = THINK_TEXT + get_completion_from_messages(context)

    # Remove THINK_TEXT from the command prompt
    context[-1] = command

    response = remove_reasoning(full_response)

    context.append(response + EOS)

    if DISPLAY_EXTENDED_REASONING and not hide_reasoning:
        return full_response
    else:
        return response


def print_system_text(text):
    print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)
    
    if LOG_ENABLED:
        save_mission_log(text)    


def print_magi_text(text):
    print(END_COLOR + MAGI_COLOR, end='')
    
    for char in text:
        print(char, end='', flush=True)
        time.sleep(MAGI_TEXT_SLEEP_TIME)
        
    print(END_COLOR)
    
    if LOG_ENABLED:
        save_mission_log(text)    


def save_mission_log(text):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Use regex to insert timestamp after any leading newlines
    log_entry = re.sub(r'^(\n*)', r'\1[{}] '.format(timestamp), text)
    
    with open(MISSION_LOG_FILE_PATH, 'a') as missionFile:
        missionFile.write(log_entry + "\n")


def user_input():
    sys.stdin.flush()

    prompt = input(USER_COLOR + "\n$ ")
    
    if LOG_ENABLED:
        save_mission_log("\n" + prompt)    
    
    return prompt


def summarize(topic, text):
    context = []

    summary = send_prompt(SUMMARIZE_SYSTEM_PROMPT, text + SUMMARIZE_TEXT + topic, context, hide_reasoning = True)

    return summary


def update_summary(topic, summary, text):
    if text:
        if summary:
            summary = summarize(topic, summary + "\n" + text)
        else:
            summary = text

    return summary


def summarize_block_array(topic, blockArray):
    summary = ""

    # Summarize
    for block in blockArray:
        summary = update_summary(topic, summary, block)

    return summary        


def load_mission_data(prompt):
    missionData = read_text_file(MISSION_DATA_FILE_PATH)
    
    if len(missionData.split()) > TEXT_BLOCK_WORDS:
        blockArray = split_text_in_blocks(missionData)
        summary = summarize_block_array(prompt, blockArray)    
    else:
        summary = missionData    
        
    return summary            


def read_text_file(path):
    try:
        with open(path) as textFile:
            text = textFile.read().strip()
            return text    
    
    except FileNotFoundError:
        print_system_text(READ_TEXT_FILE_WARNING + str(path))
        return ""
    

def load_model(startup = True):
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
        model = Llama(model_path = modelFile, n_ctx = CONTEXT_SIZE)

        model.verbose = False
        
        if startup:
            print_system_text(SYSTEM_VERSION_TEXT)
            print_system_text(MODEL_TEXT + modelName)        

    except Exception as e:
        print_system_text(MODEL_LOAD_ERROR + str(e))
        exit()


def unload_model():
    global model

    if model is not None:
        model.close()
        model = None


def load_config():
    global config
    config = {}

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


def configure_model():
    global CONTEXT_SIZE
    global MAX_INPUT_TOKENS
    global LOG_ENABLED
    global DISPLAY_EXTENDED_REASONING

    try:
        # Set context size
        context_size = config.get(CONTEXT_SIZE_KEY, '')

        if not context_size:
            print_system_text(CONFIG_ERROR + CONTEXT_SIZE_NOT_FOUND_TEXT)
            exit()

        CONTEXT_SIZE = int(context_size)

        if CONTEXT_SIZE < MIN_CONTEXT_SIZE:
            raise ValueError

        MAX_INPUT_TOKENS = CONTEXT_SIZE - MAX_RESPONSE_SIZE
        
        # Set logging configuration
        LOG_ENABLED = config.get(ENABLE_LOG_KEY, "NO").upper() == "YES"

        # Set extended reasoning configuration
        DISPLAY_EXTENDED_REASONING = config.get(DISPLAY_EXTENDED_REASONING_KEY, "YES").upper() == "YES"

    except ValueError:
        print_system_text(CONFIG_ERROR + CONTEXT_SIZE_INVALID_TEXT)
        exit()


# Initialize
load_config()
configure_model()
load_model()

