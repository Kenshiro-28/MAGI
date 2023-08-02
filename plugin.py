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

WEB_SEARCH_TEXT = "\n[WEB SEARCH] "
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
GOOGLE_TRANSLATE_URL_TEXT = "translate.google.com"

WEB_PLUGIN_ACTIVE = False
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"

TELEGRAM_PLUGIN_ACTIVE = False
TELEGRAM_PLUGIN_ENABLED_TEXT = "\nTelegram plugin: enabled"
TELEGRAM_PLUGIN_DISABLED_TEXT = "\nTelegram plugin: disabled"
ENABLE_TELEGRAM_PLUGIN_KEY = "ENABLE_TELEGRAM_PLUGIN"
TELEGRAM_BOT_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
TELEGRAM_USER_ID_KEY = "TELEGRAM_USER_ID"
TELEGRAM_PLUGIN_WAIT_TIME = 3

STABLE_DIFFUSION_PLUGIN_ACTIVE = False
STABLE_DIFFUSION_PLUGIN_ENABLED_TEXT = "\nStable Diffusion plugin: enabled"
STABLE_DIFFUSION_PLUGIN_DISABLED_TEXT = "\nStable Diffusion plugin: disabled"
ENABLE_STABLE_DIFFUSION_PLUGIN_KEY = "ENABLE_STABLE_DIFFUSION_PLUGIN"
STABLE_DIFFUSION_MODEL_KEY = "STABLE_DIFFUSION_MODEL"


# WEB PLUGIN OPERATIONS

def webSearch(query, ai_mode):
	context = []
	summary	= ""

	query = query.replace('"', '')

	core.print_system_text(WEB_SEARCH_TEXT + query, ai_mode)

	urls = web.search(query, WEB_SEARCH_LIMIT)

	for url in urls:
		# Ignore translated web pages
		if GOOGLE_TRANSLATE_URL_TEXT in url:
			continue
			
		core.print_system_text("\n" + url, ai_mode)
		text = web.scrape(url)
		blockArray = core.split_text_in_blocks(text)

		webSummary = core.summarize_block_array(query, blockArray)

		summary = core.update_summary(query, context, summary, webSummary)

		if webSummary:			
			core.print_system_text("\n" + webSummary, ai_mode)
			
	return summary


# TELEGRAM PLUGIN OPERATIONS

def send_telegram_bot(text):
	bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)	

	time.sleep(TELEGRAM_PLUGIN_WAIT_TIME)

	try:
		asyncio.run(bot.send(text))
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


# STABLE DIFFUSION OPERATIONS

stable_diffusion_counter = 1

def generate_image(prompt):
	global stable_diffusion_counter

	image = stable_diffusion.generate_image(prompt, STABLE_DIFFUSION_MODEL)

	try:
		if image:
			path = PLUGIN_WORKSPACE_FOLDER + "/image_" + str(stable_diffusion_counter) + ".png"		
			image.save(path)
			stable_diffusion_counter += 1

	except Exception as e:
		print(SAVE_FILE_ERROR + str(e)) 		
		

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
	core.print_system_text(STABLE_DIFFUSION_PLUGIN_ENABLED_TEXT, core.AiMode.NORMAL)
else:
	core.print_system_text(STABLE_DIFFUSION_PLUGIN_DISABLED_TEXT, core.AiMode.NORMAL)


