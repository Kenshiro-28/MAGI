import os
import core
import asyncio
import time
from plugins.web import web
from plugins.telegram_bot import telegram_bot
from plugins.stable_diffusion import stable_diffusion

PLUGIN_WORKSPACE_FOLDER = "workspace"
ASYNCIO_ERROR = "\n[ERROR] Asyncio exception: "
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "

# WEB PLUGIN
WEB_PLUGIN_ACTIVE = False
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
WEB_MAX_SIZE = 30 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"
WEB_SEARCH_QUERY = "Write a single-line Google search query to obtain the most comprehensive and relevant results on the following topic. Don't write titles or headings. TOPIC = "
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_TAG = "\n[WEB SUMMARY] "

# TELEGRAM PLUGIN
TELEGRAM_PLUGIN_ACTIVE = False
TELEGRAM_PLUGIN_WAIT_TIME = 3
TELEGRAM_PLUGIN_CHAR_LIMIT = 4096
TELEGRAM_PLUGIN_ENABLED_TEXT = "\nTelegram plugin: enabled"
TELEGRAM_PLUGIN_DISABLED_TEXT = "\nTelegram plugin: disabled"
ENABLE_TELEGRAM_PLUGIN_KEY = "ENABLE_TELEGRAM_PLUGIN"
TELEGRAM_BOT_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
TELEGRAM_USER_ID_KEY = "TELEGRAM_USER_ID"
TELEGRAM_TAG = "\n[TELEGRAM] "

# STABLE DIFFUSION PLUGIN
STABLE_DIFFUSION_PLUGIN_ACTIVE = False
STABLE_DIFFUSION_PLUGIN_ENABLED_TEXT = "\nStable Diffusion plugin: enabled"
STABLE_DIFFUSION_PLUGIN_DISABLED_TEXT = "\nStable Diffusion plugin: disabled"
ENABLE_STABLE_DIFFUSION_PLUGIN_KEY = "ENABLE_STABLE_DIFFUSION_PLUGIN"
STABLE_DIFFUSION_MODEL_KEY = "STABLE_DIFFUSION_MODEL"
STABLE_DIFFUSION_IMAGE_SPECS_KEY = "STABLE_DIFFUSION_IMAGE_SPECS"
STABLE_DIFFUSION_NEGATIVE_PROMPT_KEY = "STABLE_DIFFUSION_NEGATIVE_PROMPT"
GENERATE_IMAGE_TEXT = "Write an image description of no more than 100 words that captures the essence of the following text. Omit any introductory phrases or names. TEXT = "
STABLE_DIFFUSION_TAG = "\n[STABLE DIFFUSION] "


# SHARED OPERATIONS
def printMagiText(text, ai_mode):
	if TELEGRAM_PLUGIN_ACTIVE:
		send_telegram_bot(text)
		
	core.print_magi_text(text, ai_mode)


def printSystemText(text, ai_mode):
	if TELEGRAM_PLUGIN_ACTIVE:
		send_telegram_bot(text)
		
	core.print_system_text(text, ai_mode)


def userInput(ai_mode):
	if TELEGRAM_PLUGIN_ACTIVE:
		prompt = receive_telegram_bot()
		
		if prompt:
			core.print_system_text(TELEGRAM_TAG + prompt, ai_mode)		
	else:
		prompt = core.user_input(ai_mode)
		
	return prompt.strip()


def runAction(primeDirectives, action, context, ai_mode):
	response = core.send_prompt(primeDirectives, action, context)

	printMagiText("\n" + response, ai_mode)

	# Search for updated information on the Internet
	if WEB_PLUGIN_ACTIVE:
		query = core.send_prompt("", WEB_SEARCH_QUERY + action, context) 
		webSummary = WEB_SUMMARY_TAG + webSearch(query, ai_mode)
		printMagiText(webSummary, ai_mode)
		response += webSummary
	
	# Generate Stable Diffusion image
	if STABLE_DIFFUSION_PLUGIN_ACTIVE:
		image_prompt = core.send_prompt("", GENERATE_IMAGE_TEXT + response, context)
		printSystemText(STABLE_DIFFUSION_TAG + image_prompt + "\n", ai_mode)
		image = generate_image(image_prompt)
		
		if TELEGRAM_PLUGIN_ACTIVE and image:
			send_image_telegram_bot(image)		
	
	return response


# WEB PLUGIN OPERATIONS

def webSearch(query, ai_mode):
	context = []
	summary	= ""

	query = query.replace('"', '')

	printSystemText(WEB_SEARCH_TAG + query, ai_mode)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		printSystemText("\n" + url, ai_mode)
		text = web.scrape(url)
		blockArray = core.split_text_in_blocks(text)

		webSummary = core.summarize_block_array(query, blockArray[:WEB_MAX_SIZE])

		summary = core.update_summary(query, context, summary, webSummary)

		if webSummary:			
			printSystemText("\n" + webSummary, ai_mode)
			
	return summary


# TELEGRAM PLUGIN OPERATIONS

def send_telegram_bot(text):
	for i in range(0, len(text), TELEGRAM_PLUGIN_CHAR_LIMIT):
		bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)	
	
		message = text[i:i + TELEGRAM_PLUGIN_CHAR_LIMIT]

		time.sleep(TELEGRAM_PLUGIN_WAIT_TIME)

		try:
			asyncio.run(bot.send(message))
		except Exception as e:
			print(ASYNCIO_ERROR + str(e))


def receive_telegram_bot():
	message = ""

	bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)	

	time.sleep(TELEGRAM_PLUGIN_WAIT_TIME)
	
	try:	
		messageList = asyncio.run(bot.receive())
		
		if messageList:
			message = "\n".join(messageList)
			
	except Exception as e:
		print(ASYNCIO_ERROR + str(e))

	return message		


def send_image_telegram_bot(image):
	bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
	
	time.sleep(TELEGRAM_PLUGIN_WAIT_TIME)		

	try:
		asyncio.run(bot.send_image(image))
	except Exception as e:
		print(ASYNCIO_ERROR + str(e))


# STABLE DIFFUSION OPERATIONS

stable_diffusion_counter = 1

def generate_image(prompt):
	global stable_diffusion_counter

	image = stable_diffusion.generate_image(prompt, STABLE_DIFFUSION_MODEL, STABLE_DIFFUSION_IMAGE_SPECS, STABLE_DIFFUSION_NEGATIVE_PROMPT)

	try:
		if image:
			path = PLUGIN_WORKSPACE_FOLDER + "/image_" + str(stable_diffusion_counter) + ".png"		
			image.save(path)
			stable_diffusion_counter += 1

	except Exception as e:
		print(SAVE_FILE_ERROR + str(e))
		
	return image
	

# INITIALIZE PLUGINS

# Workspace
if not os.path.exists(PLUGIN_WORKSPACE_FOLDER):
	os.makedirs(PLUGIN_WORKSPACE_FOLDER)

# Web plugin
if core.config.get(ENABLE_WEB_PLUGIN_KEY, '').upper() == "YES":
	WEB_PLUGIN_ACTIVE = True
	core.print_system_text(WEB_PLUGIN_ENABLED_TEXT, core.AiMode.NORMAL)
else:
	core.print_system_text(WEB_PLUGIN_DISABLED_TEXT, core.AiMode.NORMAL)
	
# Telegram plugin
if core.config.get(ENABLE_TELEGRAM_PLUGIN_KEY, '').upper() == "YES":
	TELEGRAM_PLUGIN_ACTIVE = True
	TELEGRAM_BOT_TOKEN = core.config.get(TELEGRAM_BOT_TOKEN_KEY, '')
	TELEGRAM_USER_ID = core.config.get(TELEGRAM_USER_ID_KEY, '')
	core.print_system_text(TELEGRAM_PLUGIN_ENABLED_TEXT, core.AiMode.NORMAL)
else:
	core.print_system_text(TELEGRAM_PLUGIN_DISABLED_TEXT, core.AiMode.NORMAL)

# Stable Diffusion plugin
if core.config.get(ENABLE_STABLE_DIFFUSION_PLUGIN_KEY, '').upper() == "YES":
	STABLE_DIFFUSION_PLUGIN_ACTIVE = True
	STABLE_DIFFUSION_MODEL = core.config.get(STABLE_DIFFUSION_MODEL_KEY, '')
	STABLE_DIFFUSION_IMAGE_SPECS = core.config.get(STABLE_DIFFUSION_IMAGE_SPECS_KEY, '')
	STABLE_DIFFUSION_NEGATIVE_PROMPT = core.config.get(STABLE_DIFFUSION_NEGATIVE_PROMPT_KEY, '')		
	core.print_system_text(STABLE_DIFFUSION_PLUGIN_ENABLED_TEXT, core.AiMode.NORMAL)
else:
	core.print_system_text(STABLE_DIFFUSION_PLUGIN_DISABLED_TEXT, core.AiMode.NORMAL)


