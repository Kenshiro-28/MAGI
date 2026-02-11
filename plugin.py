import os
import re
import core
import comms
import toolchain
from PIL import Image  # noqa: TC002

PLUGIN_WORKSPACE_FOLDER = "workspace"
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "

# WEB PLUGIN
WEB_SEARCH_PAGE_LIMIT = 5 # Number of web pages per search
WEB_MAX_SIZE = 45 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT = "\nWeb plugin: enabled"
WEB_PLUGIN_DISABLED_TEXT = "\nWeb plugin: disabled"
ENABLE_WEB_PLUGIN_KEY = "ENABLE_WEB_PLUGIN"
WEB_SEARCH_TOOL_NAME = "web_search"
WEB_SEARCH_TOOL_DESCRIPTION = """Search the web for current information. This tool extracts text content from web pages and online documents found via web search (HTML, PDF, DOCX, DOC, ODT). Use when needing up-to-date facts, specifically if the request:

- Explicitly provides a URL to read or summarize, OR
- Requires current or up-to-date information on real-world events, topics, or entities via web browsing (read-only), OR
- Explicitly instructs to 'browse the web', 'search the internet', or similar actions, OR
- Involves specific real-world factual details that could be outdated, incomplete, or imprecise, such as statistics, addresses, attributes of entities (e.g., biographical details, company metrics), identifiers (e.g., contract addresses, prices, current dates, coordinates), or ongoing/debated topics (e.g., emerging scientific discoveries, policy developments, technological advancements, social trends, economic shifts, or historical facts with scholarly debate/recent findings).

CONSTRAINTS:
- Text-only: This tool retrieves text only. It does NOT retrieve images, videos, or visual layouts.
- Read-only: This tool cannot interact with forms, log in, or execute dynamic page actions (non-interactive).
- Console-based: The extracted content is returned as plain text summaries.

DO NOT USE this tool if the request explicitly instructs NOT to browse the web, search the internet, or use similar actions (e.g., "don't browse the web", "no internet search", "offline search")."""
WEB_SEARCH_SYSTEM_PROMPT = "You write a web search query to obtain relevant results."
WEB_SEARCH_GENERATE_QUERY = """Write a web search query (max 20 words) to obtain relevant results on the following topic.

Examples:
TOPIC = python errors → "common python programming bugs fixes"
TOPIC = japanese festivals → "traditional japanese festivals history celebrations"

Reason step-by-step. Reflect about your reasoning. Then, on the final line, output ONLY the query string. Don't write titles, headings or comments.

TOPIC = """
WEB_SEARCH_TARGET_SYSTEM_PROMPT = "You are a research manager. Your job is to tell a junior researcher exactly what information to look for."
WEB_SEARCH_GENERATE_TARGET = """Analyze the USER_REQUEST.
Define a clear, concise "Extraction Goal" for the summarizer.
This goal must specify exactly what facts, numbers, or details to extract from the web pages.

Reason step-by-step. Reflect about your reasoning. Then, on the final line, output ONLY the extraction goal string. Don't write titles, headings or comments.

USER_REQUEST = """
WEB_SEARCH_REVIEW_1 = """Does the following WEB_SUMMARY provide relevant information for the REQUESTED_GOAL? Reason step-by-step:
1. Identify key goal elements.
2. Check if summary matches them.
3. Decide if it's sufficient.

Reflect about your reasoning: Ensure it is based strictly on relevance and sufficiency. Then, on the final line, respond ONLY with YES or NO. Do not add explanations or any other text.

REQUESTED_GOAL = """
WEB_SEARCH_REVIEW_2 = "\n\nWEB_SUMMARY = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_REVIEW_1 = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you have performed a web search.\n\nWeb search query: "
WEB_SUMMARY_REVIEW_2 = "\n\nWeb search result: "
WEB_SEARCH_FAILED_TEXT = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you performed a web search but it didn't return any results."
WEB_DIRECT_SEARCH = "Direct Link Navigation"
WEB_URL_PATTERN = r'(https?://[^\s<>"]+|www\.[^\s<>"]+)'

# TELEGRAM PLUGIN
TELEGRAM_PLUGIN_ENABLED_TEXT = "\nTelegram plugin: enabled"
TELEGRAM_PLUGIN_DISABLED_TEXT = "\nTelegram plugin: disabled"
ENABLE_TELEGRAM_PLUGIN_KEY = "ENABLE_TELEGRAM_PLUGIN"
TELEGRAM_BOT_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
TELEGRAM_USER_ID_KEY = "TELEGRAM_USER_ID"

# IMAGE GENERATION PLUGIN
IMAGE_GENERATION_PLUGIN_ENABLED_TEXT = "\nImage generation plugin: enabled"
IMAGE_GENERATION_PLUGIN_DISABLED_TEXT = "\nImage generation plugin: disabled"
ENABLE_IMAGE_GENERATION_PLUGIN_KEY = "ENABLE_IMAGE_GENERATION_PLUGIN"
IMAGE_GENERATION_MODEL_KEY = "IMAGE_GENERATION_MODEL"
IMAGE_GENERATION_LORA_KEY = "IMAGE_GENERATION_LORA"
IMAGE_GENERATION_TYPE_KEY = "IMAGE_GENERATION_TYPE"
IMAGE_GENERATION_SPECS_KEY = "IMAGE_GENERATION_SPECS"
IMAGE_GENERATION_NEGATIVE_PROMPT_KEY = "IMAGE_GENERATION_NEGATIVE_PROMPT"
IMAGE_GENERATION_WIDTH_KEY = "IMAGE_GENERATION_WIDTH"
IMAGE_GENERATION_HEIGHT_KEY = "IMAGE_GENERATION_HEIGHT"
IMAGE_GENERATION_TOOL_NAME = "generate_image"
IMAGE_GENERATION_SYSTEM_PROMPT = "You are an expert prompt engineer for image generation. Craft clear, visual descriptions that strictly follow the provided instructions for optimal results."
IMAGE_GENERATION_TOOL_DESCRIPTION = """Generate a static image based on a textual description. Use this tool only if the task:

- Involves describing visual content that benefits from image generation, such as illustrations, representations of scenes/objects, or visualizing elements like characters, landscapes, or nature scenes in a story (e.g., settings or key moments), OR
- Explicitly instructs to 'generate an image', 'create a picture', or similar actions.

DO NOT USE this tool for non-visual descriptions or tasks that do not involve visuals, or if the request explicitly instructs NOT to generate images (e.g., "no images", "don't generate an image")."""
GENERATE_IMAGE_TEXT = """Analyze TEXT and determine its nature:

If TEXT already contains visual descriptions (subjects, objects, scenes, physical attributes, colors, materials, compositions, etc.):
- PRESERVE all specified details exactly as given
- You may ADD complementary visual details that enhance the scene
- NEVER contradict, oppose, or modify any user-specified attributes

If TEXT is conceptual, abstract, or non-visual (ideas, emotions, stories without visual details):
- Think about what static image best represents it
- Create a clear visual description from scratch

Generate an image description (max 200 words). Focus on key visible elements, styles, and scenes. Output ONLY the image description. TEXT: """
GENERATE_IMAGE_PROMPT_TEXT = """First, think about what static image best represents TEXT. Then think about the best single composition for that image. Use standard terms like the following examples:
- extreme close-up (isolates a single, small detail)
- close-up (a person's head and shoulders)
- medium shot (a person from the hips to head)
- medium long shot (a person from the knees to head)
- full shot (a person or object fully visible in its setting)
- wide shot (the subject is small in a large environment)
- panoramic (a vast landscape or cityscape)

When using close-up for people or humanoids, include "head and shoulders" to maintain framing.

When using medium shot for people or humanoids, include "waist up" to maintain framing.

When using medium long shot for people or humanoids, include "knees up" to maintain framing.

When using full shot for people or humanoids, include "full body in frame".

If none of these are the best fit, you can use other standard compositional terms. The final prompt should be a clear, physical description of the scene, including any physical descriptions of people (body type, physique, facial features, proportions).

IMPORTANT: The chosen composition must show all described details. If the TEXT describes elements that would be cut off by the requested framing (e.g., thigh-high stockings in a "waist up" shot, bare feet in a "knees up" shot, floor-length dress in a "head and shoulders" shot), use a wider composition that can include those details.

If the TEXT includes a specific artistic style (like "in the style of H.R. Giger" or "gritty"), you should include it.

Crucially, if the TEXT describes a specific, physical light source that is part of the scene (like a 'candle', 'fireplace', 'neon sign', or 'flashlight'), you SHOULD include it.

Remove general lighting style terms like 'dramatic lighting', 'cinematic lighting', or 'moody lighting'. Keep specific details about light sources.

Here are examples of how to correctly format the final prompt:
---
EXAMPLE 1 (Removing a stylistic light description)
TEXT = a knight in shining armor on a horse, under dramatic, moody lighting
CORRECT PROMPT = full body in frame: knight in shining armor riding horse.

EXAMPLE 2 (Keeping light source details)
TEXT = a slender elven archer with long auburn hair and emerald eyes by a flickering oil lantern under cinematic lighting
CORRECT PROMPT = full body in frame: slender elven archer with long auburn hair and emerald eyes, by flickering oil lantern.

EXAMPLE 3 (Honoring framing request and keeping physical descriptions)
TEXT = a medium shot of a curvy woman with a voluptuous figure, blue eyes and long blonde hair in a room lit only by a single candle
CORRECT PROMPT = waist up: curvy woman with voluptuous figure, blue eyes, and long blonde hair, in room lit only by single candle.

EXAMPLE 4 (Style Included)
TEXT = a biomechanoid inside a big alien ship in the style of H.R. Giger
CORRECT PROMPT = wide shot: biomechanoid inside big alien ship, H.R. Giger style.

EXAMPLE 5 (Panoramic for vast scenes)
TEXT = a futuristic Tokyo cityscape with neon skyscrapers stretching to the horizon
CORRECT PROMPT = panoramic: futuristic Tokyo cityscape with neon skyscrapers stretching to horizon.

EXAMPLE 6 (Adjusting composition to show described details)
TEXT = a close-up of a curvy blonde model with blue eyes wearing elegant black lingerie and sheer thigh-high stockings
CORRECT PROMPT = full body in frame: curvy blonde model with blue eyes wearing elegant black lingerie and sheer thigh-high stockings.

EXAMPLE 7 (Adjusting composition to show described details)
TEXT = a medium shot of a Roman centurion in polished lorica segmentata and leather caligae standing on marble steps
CORRECT PROMPT = full body in frame: Roman centurion in polished lorica segmentata and leather caligae, standing on marble steps.

EXAMPLE 8 (Adjusting composition to show described details)
TEXT = a headshot of a woman in an elegant floor-length gown
CORRECT PROMPT = full body in frame: woman wearing elegant floor-length gown.
---
Finally, using these examples as a guide, write an image generation prompt describing ONLY the visible elements, the requested style, and any physical light sources.

Don't describe multiple images or compositions. Don't describe camera settings, camera movements, or camera zoom. Don't use metaphors or poetic language. Don't write titles, headings or comments. Write exactly one highly condensed sentence. Use telegraphic phrasing: bind attributes, details, and clothing to the subject using words like "with" or "wearing", but use commas to separate the main subject from the background and lighting. Drop unnecessary filler words (like "a", "an", "the") to strictly limit your response to 30 words or fewer. Don't write the number of words.\n\nTEXT = """
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

- Requires complex mathematical operations, OR
- Requires data analysis with meaningful computation (e.g., processing for trends or stats), OR
- Requires network operations, OR
- Requires interacting with external systems (e.g., public APIs), OR
- Explicitly instructs to 'write a program', 'run code', or similar actions.

CONSTRAINTS:
- Console-only: This tool runs in a headless environment. NO GUIs, NO image display (plots must be saved to files), NO audio.
- Non-interactive: NO user input (no input() functions).
- Text-based output: Results must be printed to the console (print functions).
- Single-pass: The code must run to completion without waiting.

DO NOT USE this tool for:
- Logical puzzles, riddles, or brain teasers that can be solved via deduction.
- Simple math or motion problems (e.g., calculating travel time given speed and distance) that do not require a formal algorithm.
- Situational reasoning where the answer depends on interpreting a story or set of rules.
- Any task that a person could solve with a simple pen-and-paper calculation in under a minute.
- Requests where the user explicitly instructs NOT to write or execute code (e.g., "don't write code", "don't run code", "no programming")."""
CODE_RUNNER_SYSTEM_PROMPT = """You are an expert Python programmer writing production-quality code for console execution.

CORE CONSTRAINTS:
• Single-pass execution: Run once, terminate immediately (no while True:, no polling).
• Console-only: All output via print() - no files (except explicit saves), no GUIs.
• Non-interactive: Zero user input (no input(), no prompts).
• Real implementation: Use actual APIs/operations. Do not use placeholders (e.g., 'YOUR_KEY_HERE').
• Detailed Output: Print labeled, complete results with units and context."""
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
   - Libraries needed: [List with pip comment if external]
   - Authentication: [CONFIRM: Do you have the API keys? If NO, print an error. NEVER use placeholders like 'YOUR_KEY_HERE'.]
   - Performance considerations: [Time/space complexity]

10. **Output & State Strategy**: Plan the exact print statements.
    - **Detailed Results**: "Final Value: [X] [Units]" (Never print just numbers).
    - **Internal State**: Write the EXACT code block to preserve state for the next run:
      ```python
      print("\\nINTERNAL STATE:")
      print(f"variable_name: {value}")
      ```

11. **Self-Review Checklist**: Before finalizing, verify:
    - [ ] All imports listed correctly?
    - [ ] No user input() calls?
    - [ ] All print() statements are detailed with labels?
    - [ ] No infinite loops or long-running processes?
    - [ ] Error handling with try/except for risky operations?
    - [ ] INTERNAL STATE section planned exactly as specified?
    - [ ] NO PLACEHOLDERS (like 'YOUR_KEY') used?
    - [ ] Code is single-pass execution (no while True)?

12. **Final Code Structure Preview**: Outline the file structure:
    ```python
    # pip install [packages]
    # imports
    # constants/config
    # helper functions
    # main logic
    # print detailed results
    # print("\nINTERNAL STATE:")
    # print(f"key: {value}")
    ```

Finally, output the Python code wrapped in a markdown block (e.g., ```python ... ```)."""
CODE_RUNNER_GENERATION_TEXT = "Write a single file Python program to solve the following MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nMISSION: "
CODE_RUNNER_RUN_PROGRAM_TEXT = "発進！\n"
CODE_RUNNER_FIX_PROGRAM_TEXT = "The previous program had issues. Fix the program to correctly solve the MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nPrevious program:\n\n"
CODE_RUNNER_MISSION_TEXT = "\n\nMISSION: "
CODE_RUNNER_PROGRAM_OUTPUT_REVIEW = """Analyze the execution results to determine if the MISSION is complete.

CRITERIA:
1. Execution Success: Did the program run without errors?
2. State Preservation: Is the 'INTERNAL STATE:' section present and correct?
3. Mission Fulfillment: Do the results fully answer the request?

Think step-by-step. Reflect on each criterion.

CRITICAL: The very last line of your response must be exactly "YES" or "NO".

PROGRAM_CODE:
"""
CODE_RUNNER_EXTENDED_ACTION_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you have written and executed a Python program for this task.\n\nSource code:\n\n"
CODE_RUNNER_FAILED_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you were not able to write a Python program for this task."
CODE_RUNNER_TAG = "\n[CODE RUNNER]\n\n"
CODE_RUNNER_MAX_REVIEWS = 10
CODE_RUNNER_LINT_OUTPUT_LIMIT = 5000  # Chars
CODE_RUNNER_PROGRAM_OUTPUT_LIMIT = 30000  # Chars
CODE_RUNNER_PROGRAM_OUTPUT_ERROR = "\n\n[ERROR: Program output truncated. Refine the code to print specific data points or summaries instead of raw dumps.]"


# WEB PLUGIN OPERATIONS


def web_search(primeDirectives: str, action: str, context: list[str]) -> str:
    aux_context = context[:]
    mission_completed = False
    summary = ""
    urls: list[str] = []
    query = WEB_DIRECT_SEARCH

    # Compute web search target
    target_prompt = WEB_SEARCH_GENERATE_TARGET + action
    target = core.send_prompt(WEB_SEARCH_TARGET_SYSTEM_PROMPT, target_prompt, aux_context, hide_reasoning = True)

    # Check if action provided specific URLs
    urls = re.findall(WEB_URL_PATTERN, action)

    if urls:
        comms.printSystemText(WEB_SEARCH_TAG + query + "\n\n" + target)
    else:
        # Generate web search query
        query = core.send_prompt(WEB_SEARCH_SYSTEM_PROMPT, WEB_SEARCH_GENERATE_QUERY + target, aux_context, hide_reasoning = True)
        query = query.replace('"', '')

        comms.printSystemText(WEB_SEARCH_TAG + query + "\n\n" + target)

        # Run the web search
        urls = web.search(query, WEB_SEARCH_PAGE_LIMIT)

    for url in urls:
        comms.printSystemText("\n" + url)
        text = web.scrape(url)
        blockArray = core.split_text_in_blocks(text)

        web_summary = core.summarize_block_array(target, blockArray[:WEB_MAX_SIZE])

        if web_summary:
            summary = core.update_summary(target, summary, web_summary)
            mission_completed = core.binary_question(primeDirectives, WEB_SEARCH_REVIEW_1 + target + WEB_SEARCH_REVIEW_2 + summary, aux_context)
        else:
            comms.printSystemText(WEB_SEARCH_ERROR)

        if mission_completed:
            break

    if summary:
        comms.printSystemText("\n" + summary)
        extended_action = action + WEB_SUMMARY_REVIEW_1 + query + WEB_SUMMARY_REVIEW_2 + summary
    else:
        extended_action = action + WEB_SEARCH_FAILED_TEXT

    return extended_action


# IMAGE GENERATION OPERATIONS

image_generation_counter: int = 1

def generate_image(primeDirectives: str, action: str, context: list[str]) -> str:
    global image_generation_counter
    extended_action = action
    image: Image.Image = None

    # Generate visual description
    aux_context = context[:]
    image_description = core.send_prompt(primeDirectives, GENERATE_IMAGE_TEXT + extended_action, aux_context, hide_reasoning = True)

    # Generate image generation prompt
    aux_context = context[:]
    image_generation_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_PROMPT_TEXT + image_description, aux_context, hide_reasoning = True)

    comms.printSystemText(IMAGE_GENERATION_TAG + image_generation_prompt + "\n")

    # Unload main model
    core.unload_model()

    # Generate image
    image = image_generation.generate_image(image_generation_prompt, IMAGE_GENERATION_NEGATIVE_PROMPT, IMAGE_GENERATION_MODEL, IMAGE_GENERATION_LORA, IMAGE_GENERATION_TYPE, IMAGE_GENERATION_SPECS, IMAGE_GENERATION_WIDTH, IMAGE_GENERATION_HEIGHT)

    # Reload main model
    core.load_model(startup = False)

    try:
        if image:
            image_name = "image_" + str(image_generation_counter) + ".png"
            path = os.path.join(PLUGIN_WORKSPACE_FOLDER, image_name)
            image.save(path)
            image_generation_counter += 1
            comms.printSystemText("\n" + image_name)
            result = IMAGE_GENERATION_OK_TEXT_1 + image_description + IMAGE_GENERATION_OK_TEXT_2 + image_generation_prompt + IMAGE_GENERATION_OK_TEXT_3 + image_name
            extended_action += result
        else:
            extended_action += IMAGE_GENERATION_ERROR

    except Exception as e:
        image = None
        error = SAVE_FILE_ERROR + str(e)
        comms.printSystemText(error)
        extended_action += IMAGE_GENERATION_ERROR + "\n" + error

    # Send image to Telegram
    if comms.telegram_bot_enabled and image:
        comms.send_image_telegram_bot(image)

    return extended_action


# CODE RUNNER OPERATIONS

def code_runner_action(primeDirectives: str, action: str, context: list[str], is_agent: bool = False) -> str:
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

        comms.printSystemText(CODE_RUNNER_TAG + response + "\n")

        # Extract code
        if '```python' in response:
            last_code_block = response.rsplit('```python', 1)[-1]
            program = last_code_block.split('```', 1)[0].strip()
        elif '```' in response:
            program = response.rsplit('```', 2)[1].strip()
        else:
            program = response.strip()

        # Run program
        comms.printSystemText(CODE_RUNNER_RUN_PROGRAM_TEXT)
        lint_output, program_output = code_runner.run_python_code(program)

        # Check lint output size
        if len(lint_output) > CODE_RUNNER_LINT_OUTPUT_LIMIT:
            lint_output = lint_output[:CODE_RUNNER_LINT_OUTPUT_LIMIT]

        # Check program output size
        if len(program_output) > CODE_RUNNER_PROGRAM_OUTPUT_LIMIT:
            program_output = program_output[:CODE_RUNNER_PROGRAM_OUTPUT_LIMIT] + CODE_RUNNER_PROGRAM_OUTPUT_ERROR

        # Review the program output
        if program_output:
            comms.printSystemText(program_output)
            prompt = CODE_RUNNER_PROGRAM_OUTPUT_REVIEW + program + "\n\n" + program_output + CODE_RUNNER_MISSION_TEXT + action
            mission_completed = core.binary_question(primeDirectives, prompt, aux_context)
        else:
            comms.printSystemText(lint_output)

        review += 1

    if program:
        extended_action = action + CODE_RUNNER_EXTENDED_ACTION_TEXT + program + "\n\n" + program_output
    else:
        extended_action = action + CODE_RUNNER_FAILED_TEXT

    return extended_action


# INITIALIZE

try:
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
        IMAGE_GENERATION_TYPE = core.config.get(IMAGE_GENERATION_TYPE_KEY, '')
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
        telegram_bot_token = core.config.get(TELEGRAM_BOT_TOKEN_KEY, '')
        telegram_user_id = core.config.get(TELEGRAM_USER_ID_KEY, '')

        comms.initialize_telegram_bot(telegram_bot_token, telegram_user_id)

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


