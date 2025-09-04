import os
import core
import asyncio
import time

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
WEB_SEARCH_QUERY = "Write a web search query to obtain relevant results on the following topic. Don't write titles, headings or comments. Don't write more than 20 words. TOPIC = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_REVIEW = "\n\nUse the following information obtained from the Internet:\n\n" 

# TELEGRAM PLUGIN
TELEGRAM_PLUGIN_ACTIVE = False
TELEGRAM_PLUGIN_WAIT_TIME = 3
TELEGRAM_PLUGIN_CHAR_LIMIT = 4096
TELEGRAM_PLUGIN_ENABLED_TEXT = "\nTelegram plugin: enabled"
TELEGRAM_PLUGIN_DISABLED_TEXT = "\nTelegram plugin: disabled"
TELEGRAM_PLUGIN_INPUT_READY_TEXT = "Ready for inquiry."
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
IMAGE_GENERATION_NEGATIVE_PROMPT_KEY = "IMAGE_GENERATION_NEGATIVE_PROMPT"
IMAGE_GENERATION_WIDTH_KEY = "IMAGE_GENERATION_WIDTH"
IMAGE_GENERATION_HEIGHT_KEY = "IMAGE_GENERATION_HEIGHT"
IMAGE_GENERATION_SYSTEM_PROMPT = "You write clear, visual prompts for image generation."
GENERATE_IMAGE_TEXT = """First, think about what static image best represents TEXT. Then think about the best single composition for that image. Use standard terms like the following examples:

- extreme close-up (isolates a single, small detail)
- close-up (a person's head and shoulders)
- medium shot (a person from the hips to head)
- medium long shot (a person from the knees to head)
- full shot (a person or object fully visible in its setting)
- wide shot (the subject is small in a large environment)
- panoramic (a vast landscape or cityscape)

If none of these are the best fit, you can use other standard compositional terms. The final prompt should be a clear, physical description of the scene. If the TEXT includes a specific artistic style (like "in the style of H.R. Giger" or "gritty"), you should include it.

Crucially, if the TEXT describes a specific, physical light source that is part of the scene (like a 'candle', 'fireplace', 'neon sign', or 'flashlight'), you SHOULD include it.

Here are examples of how to correctly format the final prompt:
---
EXAMPLE 1 (Keeping a physical light source)
TEXT = a beautiful woman in a dark room lit only by a single candle
CORRECT PROMPT = close-up: A beautiful woman's face, lit by a single candle.

EXAMPLE 2 (Removing a stylistic light description)
TEXT = a knight in shining armor on a horse, under dramatic, moody lighting
CORRECT PROMPT = full shot: A knight in shining armor on a horse.

EXAMPLE 3 (Style Included)
TEXT = a portrait of a biomechanoid in the style of H.R. Giger
CORRECT PROMPT = medium shot: A portrait of a biomechanoid in the style of H.R. Giger.
---

Finally, using these examples as a guide, write an image generation prompt describing ONLY the visible elements, the requested style, and any physical light sources.

Don't describe multiple images or compositions. Don't describe camera settings, camera movements, or camera zoom. Don't describe general atmospheric or stylistic lighting. Don't use metaphors or poetic language. Don't write titles, headings or comments. Write less than 90 words. Don't write the number of words.\n\nTEXT = """
IMAGE_GENERATION_TAG = "\n[IMAGE] "

# CODE RUNNER PLUGIN
CODE_RUNNER_PLUGIN_ACTIVE = False
CODE_RUNNER_PLUGIN_ENABLED_TEXT = "\nCode Runner plugin: enabled"
CODE_RUNNER_PLUGIN_DISABLED_TEXT = "\nCode Runner plugin: disabled"
ENABLE_CODE_RUNNER_PLUGIN_KEY = "ENABLE_CODE_RUNNER_PLUGIN"
CODE_RUNNER_CHECK = "Determine if you need to write and execute a Python program to fulfill the following MISSION. Respond ONLY with YES or NO.\n\nMISSION: "
CODE_RUNNER_SYSTEM_PROMPT = "You are a skilled Python programmer that writes clean, efficient, and error-free code to solve specific tasks. Always ensure the code is standalone, uses print() for all outputs, and handles any necessary imports or package installations via comments. Do not use any APIs, web services, or resources that require authentication, API keys, or other credentials unless those exact credentials are explicitly provided. Never use placeholders like 'PUT YOUR API HERE' or assume credentials will be added later. If no suitable service is available without credentials or if credentials are not provided, use alternative methods like local calculations, simulations, or built-in libraries instead. Ensure all printed outputs are detailed, self-explanatory, and fully understandable standalone. Include labels, descriptions, units, and context for results, as if the reader has no access to the code."
CODE_RUNNER_GENERATION_TEXT = "Write a single file Python program to solve the following MISSION. The program should be text-based, printing all results to the console using print(). Do not create files, GUIs, or non-console outputs. The program must run non-interactively without requiring any user input. Include necessary imports. If packages are needed, list them in a comment like # pip install package1 package2. Make outputs detailed and self-explanatory, with clear labels, explanations, and summaries (e.g., 'Final result: [value] - Explanation: [brief context]'), ensuring they can be understood without seeing the code. Output only the Python code itself, without any markdown, wrappers, or additional text. MISSION: "
CODE_RUNNER_FIX_PROGRAM_TEXT = "The previous program had issues. Fix the program to correctly solve the MISSION. Output only the improved Python code itself, without any markdown, wrappers, or additional text.\nPrevious program:\n"
CODE_RUNNER_LINT_OUTPUT_TEXT = "\n\nLint output:\n\n"
CODE_RUNNER_PROGRAM_OUTPUT_TEXT = "\n\nProgram output:\n\n"
CODE_RUNNER_MISSION_TEXT = "\nMISSION: "
CODE_RUNNER_PROGRAM_OUTPUT_REVIEW = "Does the following program output fully and correctly complete the MISSION? Respond ONLY with YES or NO.\nProgram:\n"
CODE_RUNNER_EXTENDED_ACTION_TEXT = "\nYou previously wrote and executed a Python program for this task, producing the following output. Incorporate it into your response. Program output: "
CODE_RUNNER_TAG = "\n[CODE RUNNER] "
CODE_RUNNER_MAX_REVIEWS = 10


telegram_input_ready = True


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
    global telegram_input_ready

    if TELEGRAM_PLUGIN_ACTIVE:
        if not telegram_input_ready:
            send_telegram_bot(TELEGRAM_PLUGIN_INPUT_READY_TEXT)
            telegram_input_ready = True

        prompt = receive_telegram_bot()

        if prompt:
            core.print_system_text(TELEGRAM_TAG + prompt)
            telegram_input_ready = False
    else:
        prompt = core.user_input()

    return prompt.strip()


def binary_question(primeDirectives, question, context):
    aux_context = context[:]

    response = core.send_prompt(primeDirectives, question, aux_context, hide_reasoning = True)
    response = response.upper().replace(".", "").replace("'", "").replace("\"", "").strip()

    if response == "YES":
        answer = True
    else:
        answer = False

    return answer


def runAction(primeDirectives, action, context):
    extended_action = action

    # Search for updated information on the Internet
    if WEB_PLUGIN_ACTIVE:
        web_summary = web_search(primeDirectives, action, context)
        
        if web_summary:
            extended_action = action + WEB_SUMMARY_REVIEW + web_summary

    # Generate and execute code if necessary
    if CODE_RUNNER_PLUGIN_ACTIVE:
        extended_action = code_runner_action(primeDirectives, extended_action, context)

    # Run action
    response = core.send_prompt(primeDirectives, extended_action, context)

    # Print the response
    printMagiText("\n" + response)

    # Remove extended reasoning
    response = core.remove_reasoning(response)

    # Generate image
    if IMAGE_GENERATION_PLUGIN_ACTIVE:
        aux_context = []
        image_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_TEXT + action + " - " + response, aux_context, hide_reasoning = True)
        printSystemText(IMAGE_GENERATION_TAG + image_prompt + "\n")
        image = generate_image(image_prompt)
        
        if TELEGRAM_PLUGIN_ACTIVE and image:
            send_image_telegram_bot(image)        
    
    return response


# WEB PLUGIN OPERATIONS

def web_search(primeDirectives, action, context):
    summary = ""

    run_web_search = binary_question(primeDirectives, WEB_SEARCH_CHECK + action, context)

    if run_web_search:
        aux_context = context[:]
        query = core.send_prompt(primeDirectives, WEB_SEARCH_QUERY + action, aux_context, hide_reasoning = True)
        query = query.replace('"', '')

        printSystemText(WEB_SEARCH_TAG + query)

        urls = web.search(query, WEB_SEARCH_LIMIT)

        for url in urls:
            printSystemText("\n" + url)
            text = web.scrape(url)
            blockArray = core.split_text_in_blocks(text)

            web_summary = core.summarize_block_array(query, blockArray[:WEB_MAX_SIZE])

            summary = core.update_summary(query, summary, web_summary)

            if not web_summary:
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

    image = image_generation.generate_image(prompt, IMAGE_GENERATION_NEGATIVE_PROMPT, IMAGE_GENERATION_MODEL, IMAGE_GENERATION_LORA, IMAGE_GENERATION_SPECS, IMAGE_GENERATION_WIDTH, IMAGE_GENERATION_HEIGHT)

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


# CODE RUNNER OPERATIONS

def code_runner_action(primeDirectives, action, context):
    extended_action = action

    write_program = binary_question(primeDirectives, CODE_RUNNER_CHECK + action, context)

    if write_program:
        review = 0
        mission_completed = False
        program = ""
        lint_output = ""
        program_output = ""

        while review < CODE_RUNNER_MAX_REVIEWS and not mission_completed:
            aux_context = context[:]

            if review == 0:
                prompt = CODE_RUNNER_GENERATION_TEXT + action
            else:
                prompt = CODE_RUNNER_FIX_PROGRAM_TEXT + program + CODE_RUNNER_LINT_OUTPUT_TEXT + lint_output + CODE_RUNNER_PROGRAM_OUTPUT_TEXT + program_output + CODE_RUNNER_MISSION_TEXT + action

            # Generate the code
            response = core.send_prompt(CODE_RUNNER_SYSTEM_PROMPT, prompt, aux_context, hide_reasoning = True)

            # Extract code if wrapped in markdown block
            if '```python' in response:
                program = response.split('```python')[1].split('```')[0].strip()
            elif '```' in response:
                program = response.split('```')[1].strip()
            else:
                program = response

            printSystemText(CODE_RUNNER_TAG + program + "\n")

            lint_output, program_output = code_runner.run_python_code(program)

            # Review the program output
            if program_output:
                printSystemText(program_output)
                prompt = CODE_RUNNER_PROGRAM_OUTPUT_REVIEW + program + CODE_RUNNER_PROGRAM_OUTPUT_TEXT + program_output + CODE_RUNNER_MISSION_TEXT + action
                mission_completed = binary_question(primeDirectives, prompt, aux_context)
            else:
                printSystemText(lint_output)

            review += 1

        if mission_completed:
            extended_action += CODE_RUNNER_EXTENDED_ACTION_TEXT + program_output
    
    return extended_action


# INITIALIZE PLUGINS

try:
    # Workspace
    if not os.path.exists(PLUGIN_WORKSPACE_FOLDER):
        os.makedirs(PLUGIN_WORKSPACE_FOLDER)

    # Code Runner plugin
    if core.config.get(ENABLE_CODE_RUNNER_PLUGIN_KEY, '').upper() == "YES":
        from plugins.code_runner import code_runner
        CODE_RUNNER_PLUGIN_ACTIVE = True
        core.print_system_text(CODE_RUNNER_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(CODE_RUNNER_PLUGIN_DISABLED_TEXT)

    # Image generation plugin
    if core.config.get(ENABLE_IMAGE_GENERATION_PLUGIN_KEY, '').upper() == "YES":
        from plugins.image_generation import image_generation
        IMAGE_GENERATION_PLUGIN_ACTIVE = True
        IMAGE_GENERATION_MODEL = core.config.get(IMAGE_GENERATION_MODEL_KEY, '')
        IMAGE_GENERATION_LORA = core.config.get(IMAGE_GENERATION_LORA_KEY, '')
        IMAGE_GENERATION_SPECS = core.config.get(IMAGE_GENERATION_SPECS_KEY, '')
        IMAGE_GENERATION_NEGATIVE_PROMPT = core.config.get(IMAGE_GENERATION_NEGATIVE_PROMPT_KEY, '')
        IMAGE_GENERATION_WIDTH = int(core.config.get(IMAGE_GENERATION_WIDTH_KEY, '0'))
        IMAGE_GENERATION_HEIGHT = int(core.config.get(IMAGE_GENERATION_HEIGHT_KEY, '0'))

        core.print_system_text(IMAGE_GENERATION_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(IMAGE_GENERATION_PLUGIN_DISABLED_TEXT)

    # Telegram plugin
    if core.config.get(ENABLE_TELEGRAM_PLUGIN_KEY, '').upper() == "YES":
        from plugins.telegram_bot import telegram_bot
        TELEGRAM_PLUGIN_ACTIVE = True
        TELEGRAM_BOT_TOKEN = core.config.get(TELEGRAM_BOT_TOKEN_KEY, '')
        TELEGRAM_USER_ID = core.config.get(TELEGRAM_USER_ID_KEY, '')
        core.print_system_text(TELEGRAM_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(TELEGRAM_PLUGIN_DISABLED_TEXT)

    # Web plugin
    if core.config.get(ENABLE_WEB_PLUGIN_KEY, '').upper() == "YES":
        from plugins.web import web
        WEB_PLUGIN_ACTIVE = True
        core.print_system_text(WEB_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(WEB_PLUGIN_DISABLED_TEXT)

except Exception as e:
    print(core.CONFIG_ERROR + str(e) + "\n")
    exit()


