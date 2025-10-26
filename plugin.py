import os
import core
import asyncio
import time
import toolchain

CORE_PROTOCOL_FILE_PATH = "core_protocol.txt"
PLUGIN_WORKSPACE_FOLDER = "workspace"
TOOL_SELECTION_SYSTEM_PROMPT = "You are an AI assistant focused on tool selection. Respond strictly as instructed without explanations, questions, or additional text."
AVAILABLE_TOOLS_TEXT = "\n---\nAVAILABLE TOOLS: "
CONTINUE_TEXT = "continue"
TOOL_SELECTION_TEXT = "\n---\nTOOL SELECTION: Do you want to use a tool? Think about it: Review the context and tools, reflect on your reasoning, then decide. On the last line, write ONLY the exact tool name or '" + CONTINUE_TEXT + "' to proceed without a tool."
TASK_SECTION_TEXT = "\n---\nTASK: "
TOOL_USE_LIMIT = 5 # Number of tool usages per action
ASYNCIO_ERROR = "\n[ERROR] Asyncio exception: "
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "
TOOL_NOT_FOUND_ERROR = "\n\n[ERROR] Tool not found: "
TOOL_RUN_ERROR = "\n\n[ERROR] Error running tool: "

# WEB PLUGIN
WEB_SEARCH_PAGE_LIMIT = 5 # Number of web pages per search
WEB_MAX_SIZE = 20 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"
WEB_SEARCH_TOOL_NAME = "web_search"
WEB_SEARCH_TOOL_DESCRIPTION = """Search the web for current information. This tool provides text-based information only. Use when needing up-to-date facts, specifically if the request:

- Requires current or up-to-date information on real-world events, topics, or entities via web browsing (read-only), OR
- Explicitly instructs to 'browse the web', 'search the internet', or similar actions, OR
- Involves specific real-world factual details that could be outdated, incomplete, or imprecise, such as statistics, addresses, attributes of entities (e.g., biographical details, company metrics), identifiers (e.g., contract addresses, prices, current dates, coordinates), or ongoing/debated topics (e.g., emerging scientific discoveries, policy developments, technological advancements, social trends, economic shifts, or historical facts with scholarly debate/recent findings).

Do not use this tool if the request explicitly instructs NOT to browse the web, search the internet, or use similar actions (e.g., "don't browse the web", "no internet search", "offline search")."""
WEB_SEARCH_QUERY = """Write a web search query (max 20 words) to obtain relevant results on the following topic. Output ONLY the query string.

Examples:
TOPIC = python errors → "common python programming bugs fixes"
TOPIC = japanese festivals → "traditional japanese festivals history celebrations"

TOPIC = """
WEB_SEARCH_REVIEW_1 = "Does the following WEB SUMMARY provide relevant information for the QUERY? Respond ONLY with YES or NO.\n\nQUERY = "
WEB_SEARCH_REVIEW_2 = "\n\nWEB SUMMARY = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_REVIEW_1 = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you have performed a web search.\n\nWeb search query: "
WEB_SUMMARY_REVIEW_2 = "\n\nWeb search result: "
WEB_SEARCH_FAILED_TEXT = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you performed a web search but it didn't return any results."

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
IMAGE_GENERATION_PLUGIN_ENABLED_TEXT = "\nImage generation plugin: enabled"
IMAGE_GENERATION_PLUGIN_DISABLED_TEXT = "\nImage generation plugin: disabled"
ENABLE_IMAGE_GENERATION_PLUGIN_KEY = "ENABLE_IMAGE_GENERATION_PLUGIN"
IMAGE_GENERATION_MODEL_KEY = "IMAGE_GENERATION_MODEL"
IMAGE_GENERATION_LORA_KEY = "IMAGE_GENERATION_LORA"
IMAGE_GENERATION_SPECS_KEY = "IMAGE_GENERATION_SPECS"
IMAGE_GENERATION_NEGATIVE_PROMPT_KEY = "IMAGE_GENERATION_NEGATIVE_PROMPT"
IMAGE_GENERATION_WIDTH_KEY = "IMAGE_GENERATION_WIDTH"
IMAGE_GENERATION_HEIGHT_KEY = "IMAGE_GENERATION_HEIGHT"
IMAGE_GENERATION_TOOL_NAME = "generate_image"
IMAGE_GENERATION_SYSTEM_PROMPT = "You are an expert prompt engineer for image generation. Craft clear, visual descriptions that strictly follow the provided instructions for optimal results."
IMAGE_GENERATION_TOOL_DESCRIPTION = """Generate a static image based on a textual description. Use this tool only if the task:

- Involves describing visual content that benefits from image generation, such as illustrations, representations of scenes/objects, or visualizing elements like characters, landscapes, or nature scenes in a story (e.g., settings or key moments), OR
- Explicitly instructs to 'generate an image', 'create a picture', or similar actions.

Do not use this tool for non-visual descriptions or tasks that do not involve visuals, or if the request explicitly instructs NOT to generate images (e.g., "no images", "don't generate an image")."""
GENERATE_IMAGE_TEXT = """Think about what static image best represents TEXT. Generate a concise, visual-focused description (max 200 words). Focus on key visible elements, styles, and scenes. Output ONLY the image description. TEXT: """
GENERATE_IMAGE_PROMPT_TEXT = """First, think about what static image best represents TEXT. Then think about the best single composition for that image. Use standard terms like the following examples:

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
IMAGE_GENERATION_OK_TEXT_1 = "\n---\n" + IMAGE_GENERATION_TOOL_NAME + ": image generated successfully.\n\nImage description: "
IMAGE_GENERATION_OK_TEXT_2 = "\n\nImage generation prompt: "
IMAGE_GENERATION_OK_TEXT_3 = "\n\nImage name: "
IMAGE_GENERATION_ERROR = "\n---\n" + IMAGE_GENERATION_TOOL_NAME + ": unable to generate image."

# CODE RUNNER PLUGIN
CODE_RUNNER_PLUGIN_ENABLED_TEXT = "\nCode Runner plugin: enabled"
CODE_RUNNER_PLUGIN_DISABLED_TEXT = "\nCode Runner plugin: disabled"
ENABLE_CODE_RUNNER_PLUGIN_KEY = "ENABLE_CODE_RUNNER_PLUGIN"
CODE_RUNNER_TOOL_NAME = "code_runner"
CODE_RUNNER_TOOL_DESCRIPTION = """Write and run Python code. Use this tool only if the task:

- Requires mathematical operations, OR
- Requires data analysis with meaningful computation (e.g., processing for trends or stats), OR
- Requires network operations, OR
- Requires interacting with external systems (e.g., public APIs), OR
- Requires complex logic that benefits from code execution for accuracy and reliability (e.g., beyond simple comparisons or prints), OR
- Explicitly instructs to 'write a program', 'run code', or similar actions.

Do not use this tool if the request explicitly instructs NOT to write or execute code (e.g., "don't write code", "don't run code", "no programming", "no code execution")."""
CODE_RUNNER_SYSTEM_PROMPT = """You are an expert Python programmer writing production-quality code for console execution.

CORE REQUIREMENTS:
• Single-pass execution: Run once, terminate immediately (no while True:, no polling, no persistent loops)
• Console-only: All output via print() - no files or GUIs
• Non-interactive: Zero user input (no input(), no prompts)
• Real implementation: Use actual APIs/operations unless mission explicitly says 'simulate' or 'mock'

PACKAGE MANAGEMENT:
• If external packages needed: Add comment at top → # pip install package1 package2
• If only stdlib used: No pip comment needed
• Import all packages after pip comment

AUTHENTICATION:
• Only use APIs/services that are public/unauthenticated OR where exact credentials are provided
• NEVER use placeholders ('YOUR_API_KEY_HERE', 'REPLACE_THIS', etc.)
• If credentials needed but not provided: Print clear error explaining what's missing

ERROR HANDLING:
• Wrap risky operations (API calls, parsing, math) in try/except blocks
• Print informative error messages with context
• Handle edge cases: empty inputs, None values, invalid data, zero/negative numbers

OUTPUT FORMATTING:
Print detailed, standalone results with full context:
❌ Bad:  print(result)
❌ Bad:  print("Result:", 42)
✅ Good: print(f"Final calculation result: {result} meters - This represents the distance traveled over {time} seconds at {speed} m/s")

Include for each output:
• Label describing what the value represents
• Units/context (meters, seconds, USD, etc.)
• Brief explanation connecting to the mission
• Summary at the end if multiple outputs

STATE PERSISTENCE:
At program end, ALWAYS print an 'INTERNAL STATE:' section with relevant variables for future runs:
```python
print("\nINTERNAL STATE:")
print(f"wallet_balance: {balance}")
print(f"last_transaction_id: {tx_id}")
print(f"game_level: {level}")
```"""
CODE_RUNNER_COT_TEXT = """Follow all system guidelines.

Before writing the code, reason step-by-step in a structured way to ensure clean, efficient, and error-free results:

1. **Restate the Mission**: Clearly summarize the task in your own words, including any inputs, expected outputs, and constraints from the mission description.

2. **Complexity Assessment**: Estimate the complexity (simple/moderate/complex). For complex tasks, identify if it needs multiple functions/classes. List the main components/modules required.

3. **Detailed Decomposition**: Break the mission into the smallest logical sub-steps with clear inputs/outputs for each:
   - Step 1: [Description] → Input: [X], Output: [Y]
   - Step 2: [Description] → Input: [Y], Output: [Z]
   - Continue for all steps...

4. **Data Structures & Flow**: Define exactly what data structures you'll use (lists, dicts, sets, etc.) and why. Draw out the logical flow: Data → Process A → Intermediate → Process B → Result.

5. **Pseudo-code Outline**: Write pseudo-code for the main logic BEFORE actual code:
   ```
   FUNCTION main():
       initialize X
       FOR each item:
           process item
           IF condition:
               handle case
       RETURN result
   ```

6. **Edge Cases & Validation**: List at least 5-7 edge cases with specific examples:
   - Empty inputs: How to handle? → [Specific solution]
   - Invalid data: What validation? → [Specific checks]
   - Large inputs: What limits? → [Specific handling]
   - Zero/negative values: → [Specific handling]
   - Missing/None values: → [Specific handling]
   - State persistence issues: → [Specific handling]
   - Error scenarios: → [Specific try/except strategy]

7. **Function Signatures**: For each major function, write the signature with types:
   - `def function_name(param1: type, param2: type) -> return_type:`
   - Purpose: [One sentence]
   - Example call: [Concrete example]

8. **Test Cases**: Generate 3-5 concrete test cases with expected outputs:
   - Test 1: Input=[X] → Expected=[Y] → Reason=[Z]
   - Test 2: Input=[Edge case] → Expected=[Y] → Reason=[Z]

9. **Implementation Strategy**: Choose the approach and explain:
   - Libraries needed: [List with pip comment]
   - Why this approach over alternatives: [Brief comparison]
   - Performance considerations: [Time/space complexity]

10. **Self-Review Checklist**: Before finalizing, verify:
    - [ ] All imports listed correctly?
    - [ ] No user input() calls?
    - [ ] All print() statements are detailed with labels?
    - [ ] No infinite loops or long-running processes?
    - [ ] Error handling with try/except for risky operations?
    - [ ] INTERNAL STATE section planned if needed?
    - [ ] Prior state parsing logic if applicable?
    - [ ] All edge cases handled?
    - [ ] Code is single-pass execution (no while True)?

11. **Final Code Structure Preview**: Outline the file structure:
    ```
    # pip install [packages]
    # imports
    # constants/config
    # helper functions
    # main logic
    # INTERNAL STATE output
    ```

Finally, output the Python code wrapped in a markdown block (e.g., ```python ... ```)."""
CODE_RUNNER_GENERATION_TEXT = "Write a single file Python program to solve the following MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nMISSION: "
CODE_RUNNER_RUN_PROGRAM_TEXT = "発進！\n"
CODE_RUNNER_FIX_PROGRAM_TEXT = "The previous program had issues. Fix the program to correctly solve the MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nPrevious program:\n\n"
CODE_RUNNER_MISSION_TEXT = "\n\nMISSION: "
CODE_RUNNER_PROGRAM_OUTPUT_REVIEW = "Does the following program output fully complete the MISSION, including the 'INTERNAL STATE:' section with relevant variables, proper handling of any prior state, and avoidance of infinite/long-running loops? Respond ONLY with YES or NO.\n\nProgram:\n\n"
CODE_RUNNER_EXTENDED_ACTION_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you have written and executed a Python program for this task.\n\nSource code:\n\n"
CODE_RUNNER_FAILED_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you were not able to write a Python program for this task."
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


def sanitize_tool_name(response):
    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Clean the last line
    tool = last_line.replace(".", "").replace("'", "").replace("\"", "").lower().strip()

    return tool


def _run_core_protocol(primeDirectives, action, context, hide_reasoning = False):
    response = core.send_prompt(primeDirectives, CORE_PROTOCOL + action, context, hide_reasoning)

    # Remove Core Protocol from context
    if len(context) >= 2:
        context[-2] = context[-2].replace(CORE_PROTOCOL, '').strip()

    return response


def runAction(primeDirectives, action, context, is_agent = False):
    extended_action = action

    tool_use = 0

    # Use tools
    while tool_use < TOOL_USE_LIMIT:
        available_tools = toolchain.print_tools()

        if not available_tools:
            break

        # Select tool
        prompt = extended_action + AVAILABLE_TOOLS_TEXT + available_tools + TOOL_SELECTION_TEXT
        tool = core.send_prompt(TOOL_SELECTION_SYSTEM_PROMPT, prompt, context, hide_reasoning = True)
        tool = sanitize_tool_name(tool)

        if tool == CONTINUE_TEXT:
            break

        try:
            extended_action = toolchain.run_tool(tool, primeDirectives, extended_action, context, is_agent)
            tool_use += 1

        except KeyError:
            error = TOOL_NOT_FOUND_ERROR + tool
            extended_action += error
            printSystemText(error)

        except Exception as e:
            error = TOOL_RUN_ERROR + tool + "\n\n" + str(e)
            extended_action += error
            printSystemText(error)

    # Run action
    response = _run_core_protocol(primeDirectives, extended_action, context)

    # Print the response
    printMagiText("\n" + response)

    # Remove extended reasoning
    response = core.remove_reasoning(response)

    return response


# WEB PLUGIN OPERATIONS

def web_search(primeDirectives: str, action: str, context: list[str]):
    aux_context = context[:]
    mission_completed = False
    summary = ""

    # Generate web search query
    query = core.send_prompt(primeDirectives, WEB_SEARCH_QUERY + action, aux_context, hide_reasoning = True)
    query = query.replace('"', '')

    printSystemText(WEB_SEARCH_TAG + query)

    # Run the web search
    urls = web.search(query, WEB_SEARCH_PAGE_LIMIT)

    for url in urls:
        printSystemText("\n" + url)
        text = web.scrape(url)
        blockArray = core.split_text_in_blocks(text)

        web_summary = core.summarize_block_array(query, blockArray[:WEB_MAX_SIZE])

        if web_summary:
            summary = core.update_summary(query, summary, web_summary)
            mission_completed = core.binary_question(primeDirectives, WEB_SEARCH_REVIEW_1 + query + WEB_SEARCH_REVIEW_2 + summary, aux_context)
        else:
            printSystemText(WEB_SEARCH_ERROR)

        if mission_completed:
            break

    if summary:
        extended_action = action + WEB_SUMMARY_REVIEW_1 + query + WEB_SUMMARY_REVIEW_2 + summary
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

def generate_image(primeDirectives: str, action: str, context: list[str]):
    global image_generation_counter
    extended_action = action

    # Generate visual description
    aux_context = context[:]
    image_description = core.send_prompt(primeDirectives, GENERATE_IMAGE_TEXT + extended_action, aux_context, hide_reasoning = True)

    # Generate image generation prompt
    aux_context = context[:]
    image_generation_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_PROMPT_TEXT + image_description, aux_context, hide_reasoning = True)

    printSystemText(IMAGE_GENERATION_TAG + image_generation_prompt + "\n")

    # Unload main model
    core.unload_model()

    # Generate image
    image = image_generation.generate_image(image_generation_prompt, IMAGE_GENERATION_NEGATIVE_PROMPT, IMAGE_GENERATION_MODEL, IMAGE_GENERATION_LORA, IMAGE_GENERATION_SPECS, IMAGE_GENERATION_WIDTH, IMAGE_GENERATION_HEIGHT)

    # Reload main model
    core.load_model(startup = False)

    try:
        if image:
            image_name = "image_" + str(image_generation_counter) + ".png"
            path = os.path.join(PLUGIN_WORKSPACE_FOLDER, image_name)
            image.save(path)
            image_generation_counter += 1
            printSystemText(image_name)
            result = IMAGE_GENERATION_OK_TEXT_1 + image_description + IMAGE_GENERATION_OK_TEXT_2 + image_generation_prompt + IMAGE_GENERATION_OK_TEXT_3 + image_name
            extended_action += result
        else:
            extended_action += IMAGE_GENERATION_ERROR

    except Exception as e:
        image = None
        error = SAVE_FILE_ERROR + str(e)
        printSystemText(error)
        extended_action += IMAGE_GENERATION_ERROR + "\n" + error

    # Send image to Telegram
    if TELEGRAM_PLUGIN_ACTIVE and image:
        send_image_telegram_bot(image)

    return extended_action


# CODE RUNNER OPERATIONS

def code_runner_action(primeDirectives: str, action: str, context: list[str], is_agent: bool = False):
    aux_context = context[:]
    review = 0
    mission_completed = False
    program = ""
    lint_output = ""
    program_output = ""

    # Agents must preserve their identity so they can focus on their specific task
    if is_agent:
        system_prompt = primeDirectives + "\n\n" + CODE_RUNNER_SYSTEM_PROMPT
    else:
        system_prompt = CODE_RUNNER_SYSTEM_PROMPT

    # Generate and review code
    while review < CODE_RUNNER_MAX_REVIEWS and not mission_completed:
        if review == 0:
            prompt = CODE_RUNNER_GENERATION_TEXT + action
        else:
            prompt = CODE_RUNNER_FIX_PROGRAM_TEXT + program + "\n\n" + lint_output + "\n\n" + program_output + CODE_RUNNER_MISSION_TEXT + action

        # Generate the code
        response = core.send_prompt(system_prompt, prompt, aux_context, hide_reasoning = True)

        printSystemText(CODE_RUNNER_TAG + response + "\n")

        # Extract code
        if '```python' in response:
            last_code_block = response.rsplit('```python', 1)[-1]
            program = last_code_block.split('```', 1)[0].strip()
        elif '```' in response:
            program = response.rsplit('```', 2)[1].strip()
        else:
            program = response.strip()

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
        extended_action = action + CODE_RUNNER_EXTENDED_ACTION_TEXT + program + "\n\n" + program_output
    else:
        extended_action = action + CODE_RUNNER_FAILED_TEXT

    return extended_action


# INITIALIZE

try:
    # Core Protocol
    core_protocol_text = core.read_text_file(CORE_PROTOCOL_FILE_PATH)

    if core_protocol_text:
        CORE_PROTOCOL = core_protocol_text + TASK_SECTION_TEXT
    else:
        CORE_PROTOCOL = ""

    # Workspace
    if not os.path.exists(PLUGIN_WORKSPACE_FOLDER):
        os.makedirs(PLUGIN_WORKSPACE_FOLDER)

    # Code Runner plugin
    if core.config.get(ENABLE_CODE_RUNNER_PLUGIN_KEY, '').upper() == "YES":
        from plugins.code_runner import code_runner
        core.print_system_text(CODE_RUNNER_PLUGIN_ENABLED_TEXT)
        toolchain.add_tool(CODE_RUNNER_TOOL_NAME, CODE_RUNNER_TOOL_DESCRIPTION, code_runner_action)
    else:
        core.print_system_text(CODE_RUNNER_PLUGIN_DISABLED_TEXT)

    # Image generation plugin
    if core.config.get(ENABLE_IMAGE_GENERATION_PLUGIN_KEY, '').upper() == "YES":
        from plugins.image_generation import image_generation
        IMAGE_GENERATION_MODEL = core.config.get(IMAGE_GENERATION_MODEL_KEY, '')
        IMAGE_GENERATION_LORA = core.config.get(IMAGE_GENERATION_LORA_KEY, '')
        IMAGE_GENERATION_SPECS = core.config.get(IMAGE_GENERATION_SPECS_KEY, '')
        IMAGE_GENERATION_NEGATIVE_PROMPT = core.config.get(IMAGE_GENERATION_NEGATIVE_PROMPT_KEY, '')
        IMAGE_GENERATION_WIDTH = int(core.config.get(IMAGE_GENERATION_WIDTH_KEY, '0'))
        IMAGE_GENERATION_HEIGHT = int(core.config.get(IMAGE_GENERATION_HEIGHT_KEY, '0'))

        core.print_system_text(IMAGE_GENERATION_PLUGIN_ENABLED_TEXT)
        toolchain.add_tool(IMAGE_GENERATION_TOOL_NAME, IMAGE_GENERATION_TOOL_DESCRIPTION, generate_image)
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
        core.print_system_text(WEB_PLUGIN_ENABLED_TEXT)
        toolchain.add_tool(WEB_SEARCH_TOOL_NAME, WEB_SEARCH_TOOL_DESCRIPTION, web_search)
    else:
        core.print_system_text(WEB_PLUGIN_DISABLED_TEXT)


except Exception as e:
    print(core.CONFIG_ERROR + str(e) + "\n")
    exit()


