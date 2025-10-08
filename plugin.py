import os
import core
import asyncio
import time

PLUGIN_WORKSPACE_FOLDER = "workspace"
ASYNCIO_ERROR = "\n[ERROR] Asyncio exception: "
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "

# WEB PLUGIN
WEB_PLUGIN_ACTIVE = False
WEB_SEARCH_LIMIT = 10 # Number of web searches
WEB_SEARCH_PAGE_LIMIT = 5 # Number of web pages per search
WEB_MAX_SIZE = 20 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"
WEB_SEARCH_CHECK = """This is a new prompt—ignore any previous restrictions. Determine whether the following user request:

- Requires current or up-to-date information on real-world events, topics, or entities via web browsing (read-only), OR
- Explicitly instructs to 'browse the web', 'search the internet', or similar actions, OR
- Involves specific real-world factual details that could be outdated, incomplete, or imprecise, such as statistics, addresses, attributes of entities (e.g., biographical details, company metrics), identifiers (e.g., contract addresses, prices, current dates, coordinates), or ongoing/debated topics (e.g., emerging scientific discoveries, policy developments, technological advancements, social trends, economic shifts, or historical facts with scholarly debate/recent findings).

However, if the request explicitly instructs NOT to browse the web, search the internet, or use similar actions (e.g., "don't browse the web", "no internet search", "offline search"), respond NO regardless of the above.

Reason step-by-step through each condition before responding ONLY with YES or NO. If uncertain after reasoning, default to YES for safety.

Examples:
USER REQUEST: Please tell me the population of Tokyo. → YES (real-world factual that could be outdated).
USER REQUEST: Please tell me the population of Tokyo, don't browse the web for this. → NO (explicit instruction not to browse the web, overriding other conditions).
USER REQUEST: When did Gaius Marius create the professional Roman army? → NO (well-established historical fact, unlikely to be imprecise without new evidence).
USER REQUEST: When did Gaius Marius create the professional Roman army? Browse the web for this. → YES (explicit instruction to browse the web, overriding other conditions).
USER REQUEST: Causes of the fall of the Roman Empire? → YES (historical topic with scholarly debate).
USER REQUEST: Calculate 3 * 9. → NO (pure computation, not real-world factual).
USER REQUEST: What's the contract address for WOJAK on Solana? → YES (specific identifier that may be incomplete).
USER REQUEST: Explain the attributes of gravity. → NO (established scientific knowledge, not debated or emerging).
USER REQUEST: What planets orbit Proxima Centauri? → YES (emerging scientific topic with potentially evolving details).
USER REQUEST: Evaluate the ethical implications of AI in military drones. → YES (debated technological topic with evolving details).
USER REQUEST: Write a story about the elves of Rivendell. → NO (creative task, not factual).

USER REQUEST: """
WEB_SEARCH_QUERY = """Write a web search query (max 20 words) to obtain relevant results on the following topic. Output ONLY the query string.

Examples:
TOPIC = python errors → "common python programming bugs fixes"
TOPIC = japanese festivals → "traditional japanese festivals history celebrations"

TOPIC = """
WEB_SEARCH_HELPER = "\n\nThe previous web search didn't find the required information, please refine/optimize the web search query."
WEB_SEARCH_REVIEW_1 = "Does the following WEB page contain the required information to complete the MISSION? Respond ONLY with YES or NO.\n\nMISSION = "
WEB_SEARCH_REVIEW_2 = "\n\nWEB = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_REVIEW = "\n\nYou found the following information from browsing the web:\n\n"
WEB_SEARCH_COMPLETED = "\n\nYou will not browse the web again for this prompt. You may do so in future prompts if the new query requires it.\n\n"
WEB_SEARCH_UNUSED_TEXT = "\n\nYou will not browse the web for this prompt. You may do so in future prompts if the new query requires it.\n\n"
WEB_SEARCH_FAILED_TEXT = "\n\nYou performed a web search but it didn't return any results." + WEB_SEARCH_COMPLETED

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
CODE_RUNNER_CHECK = """This is a new prompt—ignore any previous restrictions. Determine whether writing and executing a Python program is necessary and appropriate to accomplish the following MISSION. Respond YES only if the MISSION:

- Requires mathematical operations, OR
- Requires data analysis, OR
- Requires network operations, OR
- Requires interacting with external systems (e.g., public APIs), OR
- Requires complex logic that benefits from code execution for accuracy and reliability, OR
- Explicitly instructs to 'write a program', 'run code', or similar actions.

Respond NO for tasks that involve generating simple text, descriptions, or any task not described above that can be performed without programming.

However, if the request explicitly instructs NOT to write or execute code (e.g., "don't write code", "don't run code", "no programming", "no code execution"), respond NO regardless of the above.

Reason step-by-step through each condition before responding ONLY with YES or NO. If uncertain after reasoning, default to YES for safety.

Examples:
MISSION: Solve a system of linear equations with variables. → YES (mathematical operations benefiting from code).
MISSION: Solve a system of linear equations with variables, don't run code for this. → NO (explicit instruction not to run code, overriding other conditions).
MISSION: Write a story about the elves of Rivendell. → NO (simple text generation).
MISSION: Write a story about the elves of Rivendell, write a program for this. → YES (explicit instruction to write a program, overriding other conditions).
MISSION: Fetch weather data from a public API. → YES (interacting with external systems).
MISSION: Get location based on IP using a public API. → YES (interacting with external systems).
MISSION: Analyze trends in a dataset of 1000 entries. → YES (data analysis).
MISSION: Explain the concept of gravity. → NO (description, no programming needed).
MISSION: Simulate a physics experiment. → YES (complex logic requiring accuracy).
MISSION: What is the capital of Japan? → NO (simple factual recall).
MISSION: Install a Python package using pip install. → YES (package installation requiring network operations and external systems).

MISSION: """
CODE_RUNNER_SYSTEM_PROMPT = """You are a skilled Python programmer that writes clean, efficient, and error-free code to solve specific tasks. The code must be text-based, printing all results to the console using print(). Do not create files, GUIs, or non-console outputs. The code must run non-interactively without requiring any user input. If packages are needed, list them in a comment like # pip install package1 package2 at the beginning of the code. Include necessary imports after that. Do not use any APIs, web services, or resources that require authentication, API keys, or other credentials unless those exact credentials are explicitly provided. Never use placeholders like 'PUT YOUR API HERE' or assume credentials will be added later.

Crucially, structure the code for single-pass execution: perform the task once (e.g., fetch data, compute, decide, update state) and terminate immediately after. Do not include infinite loops (e.g., while True:), long-running loops, polling, or any persistent monitoring—assume the script will be relaunched externally if iteration is needed.

Ensure all printed outputs are detailed, self-explanatory, and fully understandable standalone, with clear labels, descriptions, units, explanations, and summaries (e.g., 'Final result: [value] - Explanation: [brief context]'), including context for results as if the reader has no access to the code. For persistence across runs, always print a 'INTERNAL STATE:' section at the end with the contents of relevant variables (e.g., wallets, credentials, game states, simulation data), ignoring trivial ones like loops or counters. If prior state is available in the prompt or conversation history, parse it (e.g., from a previous 'INTERNAL STATE:' section), integrate into the logic, update as needed, and reprint the full updated section."""
CODE_RUNNER_COT_TEXT = """Follow all system guidelines.

Before writing the code, reason step-by-step in a structured way to ensure clean, efficient, and error-free results:

1. **Restate the Mission**: Clearly summarize the task in your own words, including any inputs, expected outputs, and constraints from the mission description.

2. **Break It Down**: Decompose the mission into the smallest logical sub-steps or components (e.g., data loading, computation, validation, output formatting). Identify key functions, classes, or modules needed.

3. **List Assumptions, Variables, and Edge Cases**: Note any assumptions (e.g., input types, environment limits). Define main variables with types and purposes. Brainstorm at least 3-5 edge cases (e.g., empty inputs, large numbers, errors in prior state) and how to handle them (e.g., try/except blocks).

4. **Explore Alternatives**: Branch into 2-3 possible approaches (e.g., numpy vs. pure Python for math). Evaluate pros/cons briefly (e.g., efficiency, readability, compatibility). Select the best and explain why.

5. **Plan Imports and Outputs**: List required imports/packages (via comments only). Outline how outputs will be detailed/self-explanatory with labels, explanations, and summaries.

6. **Handle Persistence**: If applicable, describe parsing/updating the 'INTERNAL STATE:' section, including relevant variables to track.

7. **Self-Review**: Double-check for potential errors, biases (e.g., assuming positive numbers), or overlooked guidelines. Ensure non-interactivity and console-only output. Avoid infinite/long-running loops.

Keep reasoning concise for simple missions; expand only as needed for complexity. Then, output the Python code wrapped in a markdown block (e.g., ```python ... ```)."""
CODE_RUNNER_GENERATION_TEXT = "Write a single file Python program to solve the following MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nMISSION: "
CODE_RUNNER_RUN_PROGRAM_TEXT = "発進！\n"
CODE_RUNNER_FIX_PROGRAM_TEXT = "The previous program had issues. Fix the program to correctly solve the MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nPrevious program:\n\n"
CODE_RUNNER_MISSION_TEXT = "\n\nMISSION: "
CODE_RUNNER_PROGRAM_OUTPUT_REVIEW = "Does the following program output fully complete the MISSION, including the 'INTERNAL STATE:' section with relevant variables, proper handling of any prior state, and avoidance of infinite/long-running loops? Respond ONLY with YES or NO.\n\nProgram:\n\n"
CODE_RUNNER_EXTENDED_ACTION_TEXT = "\n\nYou have written and executed a Python program for this task.\n\nSource code:\n\n"
CODE_RUNNER_ACTION_COMPLETED = "\n\nYou will not execute any code again for this prompt. You may do so in future prompts if the new query requires it."
CODE_RUNNER_UNUSED_TEXT = "\n\nYou will not execute any code for this prompt. You may do so in future prompts if the new query requires it."
CODE_RUNNER_FAILED_TEXT = "\n\nYou were not able to write a Python program for this task." + CODE_RUNNER_UNUSED_TEXT
CODE_RUNNER_TAG = "\n[CODE RUNNER]\n\n"
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


def runAction(primeDirectives, action, context):
    extended_action = action

    # Search for updated information on the Internet
    if WEB_PLUGIN_ACTIVE:
        extended_action = web_search(primeDirectives, extended_action, context)
    else:
        extended_action += WEB_SEARCH_UNUSED_TEXT

    # Generate and execute code if necessary
    if CODE_RUNNER_PLUGIN_ACTIVE:
        extended_action = code_runner_action(primeDirectives, extended_action, context)
    else:
        extended_action += CODE_RUNNER_UNUSED_TEXT

    # Run action
    response = core.send_prompt(primeDirectives, extended_action, context)

    # Print the response
    printMagiText("\n" + response)

    # Remove extended reasoning
    response = core.remove_reasoning(response)

    # Generate image
    if IMAGE_GENERATION_PLUGIN_ACTIVE:
        aux_context = []
        image_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_TEXT + extended_action + " - " + response, aux_context, hide_reasoning = True)
        printSystemText(IMAGE_GENERATION_TAG + image_prompt + "\n")
        image = generate_image(image_prompt)
        
        if TELEGRAM_PLUGIN_ACTIVE and image:
            send_image_telegram_bot(image)        
    
    return response


# WEB PLUGIN OPERATIONS

def web_search(primeDirectives, action, context):
    extended_action = action + WEB_SEARCH_UNUSED_TEXT

    run_web_search = core.binary_question(primeDirectives, WEB_SEARCH_CHECK + action, context)

    if run_web_search:
        aux_context = context[:]
        aux_action = action
        mission_completed = False
        search_number = 0
        web_summary = ""

        while not mission_completed and search_number < WEB_SEARCH_LIMIT:
            query = core.send_prompt(primeDirectives, WEB_SEARCH_QUERY + aux_action, aux_context, hide_reasoning = True)
            query = query.replace('"', '')

            printSystemText(WEB_SEARCH_TAG + query)

            urls = web.search(query, WEB_SEARCH_PAGE_LIMIT)

            for url in urls:
                printSystemText("\n" + url)
                text = web.scrape(url)
                blockArray = core.split_text_in_blocks(text)

                web_summary = core.summarize_block_array(query, blockArray[:WEB_MAX_SIZE])

                if web_summary:
                    mission_completed = core.binary_question(primeDirectives, WEB_SEARCH_REVIEW_1 + action + WEB_SEARCH_REVIEW_2 + web_summary, aux_context)
                else:
                    printSystemText(WEB_SEARCH_ERROR)

                if mission_completed:
                    break

            if not mission_completed:
                aux_action = action + WEB_SEARCH_HELPER
                search_number += 1

        if mission_completed:
            extended_action = action + WEB_SUMMARY_REVIEW + web_summary + WEB_SEARCH_COMPLETED
        else:
            extended_action = action + WEB_SEARCH_FAILED_TEXT

    return extended_action


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
    extended_action = action + CODE_RUNNER_UNUSED_TEXT

    write_program = core.binary_question(primeDirectives, CODE_RUNNER_CHECK + action, context)

    if write_program:
        aux_context = context[:]
        review = 0
        mission_completed = False
        program = ""
        lint_output = ""
        program_output = ""

        while review < CODE_RUNNER_MAX_REVIEWS and not mission_completed:
            if review == 0:
                prompt = CODE_RUNNER_GENERATION_TEXT + action
            else:
                prompt = CODE_RUNNER_FIX_PROGRAM_TEXT + program + "\n\n" + lint_output + "\n\n" + program_output + CODE_RUNNER_MISSION_TEXT + action

            # Generate the code
            response = core.send_prompt(CODE_RUNNER_SYSTEM_PROMPT, prompt, aux_context, hide_reasoning = True)

            printSystemText(CODE_RUNNER_TAG + response + "\n")

            # Extract code
            if '```python' in response:
                program = response.split('```python')[1].split('```')[0].strip()
            elif '```' in response:
                program = response.split('```')[1].strip()
            else:
                program = response

            # Run program
            printSystemText(CODE_RUNNER_RUN_PROGRAM_TEXT)
            lint_output, program_output = code_runner.run_python_code(program)

            # Review the program output
            if program_output:
                printSystemText(program_output)
                prompt = CODE_RUNNER_PROGRAM_OUTPUT_REVIEW + program + "\n\n" + program_output + CODE_RUNNER_MISSION_TEXT + action
                mission_completed = core.binary_question(primeDirectives, prompt, aux_context)
            else:
                printSystemText(lint_output)

            review += 1

        if program:
            extended_action = action + CODE_RUNNER_EXTENDED_ACTION_TEXT + program + "\n\n" + program_output + CODE_RUNNER_ACTION_COMPLETED
        else:
            extended_action = action + CODE_RUNNER_FAILED_TEXT

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


