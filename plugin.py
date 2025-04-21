import os
import core
import asyncio
import time
from plugins.web import web
from plugins.telegram_bot import telegram_bot
from plugins.image_generation import image_generation

PLUGIN_WORKSPACE_FOLDER = "workspace"
ASYNCIO_ERROR = "\n[ERROR] Asyncio exception: "
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "

# WEB PLUGIN
WEB_PLUGIN_ACTIVE = False
WEB_SEARCH_LIMIT = 3 # Number of web pages per search
WEB_MAX_SIZE = 10 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"
WEB_SEARCH_CHECK = "Determine whether the following user request refers specifically to a present or future moment in time and may require access to current information from the Internet. Respond ONLY with YES or NO.\n\nUSER REQUEST: "
WEB_SEARCH_QUERY = "Write a single-line Google search query to obtain the most comprehensive and relevant results on the following topic. Don't write titles or headings. TOPIC = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_TAG = "\n[WEB SUMMARY] "
WEB_SUMMARY_REVIEW = "\n\nUse the following information obtained from the Internet:\n\n" 

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

# IMAGE GENERATION PLUGIN
IMAGE_GENERATION_PLUGIN_ACTIVE = False
IMAGE_GENERATION_PLUGIN_ENABLED_TEXT = "\nImage generation plugin: enabled"
IMAGE_GENERATION_PLUGIN_DISABLED_TEXT = "\nImage generation plugin: disabled"
ENABLE_IMAGE_GENERATION_PLUGIN_KEY = "ENABLE_IMAGE_GENERATION_PLUGIN"
IMAGE_GENERATION_MODEL_KEY = "IMAGE_GENERATION_MODEL"
IMAGE_GENERATION_LORA_KEY = "IMAGE_GENERATION_LORA"
IMAGE_GENERATION_SPECS_KEY = "IMAGE_GENERATION_SPECS"
IMAGE_GENERATION_WIDTH_KEY = "IMAGE_GENERATION_WIDTH"
IMAGE_GENERATION_HEIGHT_KEY = "IMAGE_GENERATION_HEIGHT"
IMAGE_GENERATION_SYSTEM_PROMPT = "Write image generation prompts, emphasize key visual elements in priority order: main details, exact pose/action/expression, environmental context, composition and framing, lighting conditions and atmosphere, textures and materials, artistic style and medium. Use commas to separate elements. Start with the most important aspect and build detail progressively."
GENERATE_IMAGE_TEXT = "Write an image generation prompt from the following text (max 150 words). Don't write titles or headings. Don't start with command verbs like 'create', 'make', or 'generate'. TEXT = "
IMAGE_GENERATION_TAG = "\n[IMAGE] "


# SHARED OPERATIONS

def printMagiText(text):
    if TELEGRAM_PLUGIN_ACTIVE:
        send_telegram_bot(text)
        
    core.print_magi_text(text)


def printSystemText(text):
    if TELEGRAM_PLUGIN_ACTIVE:
        send_telegram_bot(text)
        
    core.print_system_text(text)


def userInput():
    if TELEGRAM_PLUGIN_ACTIVE:
        prompt = receive_telegram_bot()
        
        if prompt:
            core.print_system_text(TELEGRAM_TAG + prompt)        
    else:
        prompt = core.user_input()
        
    return prompt.strip()


def runAction(primeDirectives, action, context):
    # Search for updated information on the Internet
    if WEB_PLUGIN_ACTIVE:
        aux_context = context[:]
        run_web_search = core.send_prompt(primeDirectives, WEB_SEARCH_CHECK + action, aux_context, hide_reasoning = True)
        run_web_search = run_web_search.upper().replace(".", "").replace("'", "").replace("\"", "").strip()

        if run_web_search == "YES":
            aux_context = context[:]
            query = core.send_prompt(primeDirectives, WEB_SEARCH_QUERY + action, aux_context, hide_reasoning = True)
            webSummary = WEB_SUMMARY_TAG + webSearch(query)

            response = core.send_prompt(primeDirectives, action + WEB_SUMMARY_REVIEW + webSummary, context)
        else:
            response = core.send_prompt(primeDirectives, action, context)
    else:
        response = core.send_prompt(primeDirectives, action, context)

    # Print the response (from model knowledge or web-scraped data)
    printMagiText("\n" + response)

    # Remove extended reasoning
    response = core.remove_reasoning(response)

    # Generate image
    if IMAGE_GENERATION_PLUGIN_ACTIVE:
        aux_context = []
        image_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_TEXT + response, aux_context, hide_reasoning = True)
        printSystemText(IMAGE_GENERATION_TAG + image_prompt + "\n")
        image = generate_image(image_prompt)
        
        if TELEGRAM_PLUGIN_ACTIVE and image:
            send_image_telegram_bot(image)        
    
    return response


# WEB PLUGIN OPERATIONS

def webSearch(query):
    summary = ""

    query = query.replace('"', '')

    printSystemText(WEB_SEARCH_TAG + query)

    urls = web.search(query, WEB_SEARCH_LIMIT)

    for url in urls:
        printSystemText("\n" + url)
        text = web.scrape(url)
        blockArray = core.split_text_in_blocks(text)

        webSummary = core.summarize_block_array(query, blockArray[:WEB_MAX_SIZE])

        summary = core.update_summary(query, summary, webSummary)

        if not webSummary:
            printSystemText(WEB_SEARCH_ERROR)
            
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


# IMAGE GENERATION OPERATIONS

image_generation_counter = 1

def generate_image(prompt):
    global image_generation_counter
    
    # Unload main model
    core.unload_model()

    image = image_generation.generate_image(prompt, IMAGE_GENERATION_MODEL, IMAGE_GENERATION_LORA, IMAGE_GENERATION_SPECS, IMAGE_GENERATION_WIDTH, IMAGE_GENERATION_HEIGHT)

    # Reload main model
    core.load_model(startup = False)

    try:
        if image:
            path = PLUGIN_WORKSPACE_FOLDER + "/image_" + str(image_generation_counter) + ".png"        
            image.save(path)
            image_generation_counter += 1

    except Exception as e:
        print(SAVE_FILE_ERROR + str(e))
        
    return image
    

# INITIALIZE PLUGINS

try:
    # Workspace
    if not os.path.exists(PLUGIN_WORKSPACE_FOLDER):
        os.makedirs(PLUGIN_WORKSPACE_FOLDER)

    # Web plugin
    if core.config.get(ENABLE_WEB_PLUGIN_KEY, '').upper() == "YES":
        WEB_PLUGIN_ACTIVE = True
        core.print_system_text(WEB_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(WEB_PLUGIN_DISABLED_TEXT)
        
    # Telegram plugin
    if core.config.get(ENABLE_TELEGRAM_PLUGIN_KEY, '').upper() == "YES":
        TELEGRAM_PLUGIN_ACTIVE = True
        TELEGRAM_BOT_TOKEN = core.config.get(TELEGRAM_BOT_TOKEN_KEY, '')
        TELEGRAM_USER_ID = core.config.get(TELEGRAM_USER_ID_KEY, '')
        core.print_system_text(TELEGRAM_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(TELEGRAM_PLUGIN_DISABLED_TEXT)

    # Image generation plugin
    if core.config.get(ENABLE_IMAGE_GENERATION_PLUGIN_KEY, '').upper() == "YES":
        IMAGE_GENERATION_PLUGIN_ACTIVE = True
        IMAGE_GENERATION_MODEL = core.config.get(IMAGE_GENERATION_MODEL_KEY, '')
        IMAGE_GENERATION_LORA = core.config.get(IMAGE_GENERATION_LORA_KEY, '')
        IMAGE_GENERATION_SPECS = core.config.get(IMAGE_GENERATION_SPECS_KEY, '')
        IMAGE_GENERATION_WIDTH = int(core.config.get(IMAGE_GENERATION_WIDTH_KEY, ''))
        IMAGE_GENERATION_HEIGHT = int(core.config.get(IMAGE_GENERATION_HEIGHT_KEY, ''))

        core.print_system_text(IMAGE_GENERATION_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(IMAGE_GENERATION_PLUGIN_DISABLED_TEXT)

except Exception as e:
    print(core.CONFIG_ERROR + str(e) + "\n")
    exit()


