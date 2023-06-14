from llama_cpp import Llama
import os
import sys

USER_TEXT = "USER: " 
ASSISTANT_TEXT = " ASSISTANT: "

BASIC_SUMMARY_TEXT = "Summarize the following text: "
SUMMARIZE_TEXT = "\nSummarize the information from the above text that is relevant to this topic: "

PRIME_DIRECTIVES_FILE_PATH = "prime_directives.txt"
MISSION_LOG_FILE_PATH = "mission_log.txt"
MISSION_DATA_FILE_PATH = "mission_data.txt"

MODEL_TEXT = "\n\nModel: "
MODEL_ERROR_TEXT = "\n[ERROR] An exception occurred while trying to get a response from the model: "
MODEL_NOT_FOUND_ERROR = "\n[ERROR] Model not found.\n"

MAX_TOKENS = 2048
EXTRA_TOKEN_COUNT = 48
MAX_INPUT_TOKENS = MAX_TOKENS // 2 + EXTRA_TOKEN_COUNT
MAX_INPUT_TOKENS_ERROR = "[ERROR] Your input has more than " + str(MAX_INPUT_TOKENS) + " tokens: "

READ_TEXT_FILE_WARNING = "\n[WARNING] File not found: "

SYSTEM_COLOR = "\033[32m"
MAGI_COLOR = "\033[99m"
USER_COLOR = "\033[93m"
END_COLOR = "\x1b[0m"

TEXT_BLOCK_WORDS = 400


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
	text_tokens = len(tokenized_text) + EXTRA_TOKEN_COUNT
	
	return text_tokens
	

def get_context_data(context):
	text = ' '.join(context)
	text_tokens = get_number_of_tokens(text)
	
	return text, text_tokens
	
	
def get_completion_from_messages(context):
	try:
		text, text_tokens = get_context_data(context)
		
		# Check context size
		while len(context) > 1 and text_tokens > MAX_INPUT_TOKENS:
			context.pop(0)
			text, text_tokens = get_context_data(context)

		response = model(text, max_tokens = MAX_TOKENS - text_tokens)

		return response['choices'][0]['text'].lstrip()
		
	except Exception as e:
		print_system_text(MODEL_ERROR_TEXT + str(e), False) 
		return ""


def send_prompt(primeDirectives, prompt, context):
	if primeDirectives:
		primeDirectives += "\n"

	command = USER_TEXT + primeDirectives + prompt + ASSISTANT_TEXT

	context.append(command)

	response = get_completion_from_messages(context) 

	context.append(response)

	return response


def print_system_text(text, missionMode):
	print(END_COLOR + SYSTEM_COLOR + text + END_COLOR)
	
	if missionMode:
		save_mission_log(text)	

	
def print_magi_text(text, missionMode):
	print(END_COLOR + MAGI_COLOR + text + END_COLOR)
	
	if missionMode:
		save_mission_log(text)	


def save_mission_log(text):
	with open(MISSION_LOG_FILE_PATH, 'a') as missionFile:
		missionFile.write(text + "\n")

	
def user_input(missionMode):
	sys.stdin.flush()

	prompt = input(USER_COLOR + "\n$ ")
	
	if missionMode:
		save_mission_log(prompt)	
	
	return prompt		


def basic_summary(text1, text2):
	context = []	
	summary = send_prompt("", BASIC_SUMMARY_TEXT + text1 + "\n" + text2, context) 
	
	return summary


def summarize(topic, context, text):
	summary = send_prompt("", text + SUMMARIZE_TEXT + topic, context) 
	
	return summary
	

def update_summary(topic, context, summary, text):
	if text:
		if summary:
			summary = summarize(topic, context, summary + "\n" + text)
		else:
			summary = text

	return summary


def summarize_block_array(topic, blockArray):
	context = []
	summary = ""

	# Summarize
	for block in blockArray:
		summary = update_summary(topic, context, summary, block)

	return summary		


def load_mission_data(prompt):
	missionData = read_text_file(MISSION_DATA_FILE_PATH)
		
	blockArray = split_text_in_blocks(missionData)

	summary = summarize_block_array(prompt, blockArray)	
		
	return summary			

	
def is_prompt_completed(prompt, context):
	answer = False

	response = send_prompt("", prompt, context)

	if response:	
		response = response.split()[0].replace(".", "").replace(",", "").strip().upper()
	
	if response == "YES":
		answer = True
		
	return answer
	

def read_text_file(path):
	try:
		with open(path) as textFile:
			text = textFile.read().strip()
			return text	
	
	except FileNotFoundError:
		print_system_text(READ_TEXT_FILE_WARNING + str(path), False)
		return ""
	

def load_model():
	model = None

	fileArray = os.listdir()

	# Filter for .bin files
	binFileArray = [f for f in fileArray if f.endswith('.bin')]

	if binFileArray:
		# Get the first .bin file
		modelFile = binFileArray[0]

		# Get the file name without the .bin extension
		modelName = os.path.splitext(modelFile)[0]
		
		print()
		
		# Load model		
		model = Llama(model_path = modelFile, n_ctx = MAX_TOKENS)
		model.verbose = False

		# Print model name		
		print_system_text(MODEL_TEXT + modelName, False)	
	else:
		print_system_text(MODEL_NOT_FOUND_ERROR, False)
		exit()		

	return model

	
# Initialize
model = load_model()
	
