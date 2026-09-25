import os
import re
import core
import comms
import toolchain
from PIL import Image  # noqa: TC002

PLUGIN_WORKSPACE_FOLDER = "workspace"
PLUGINS_TEXT = "\n\n----- Plugins -----\n"
SAVE_FILE_ERROR = "\n[ERROR] An exception occurred while trying to save a file: "

# WEB PLUGIN
WEB_SEARCH_PAGE_LIMIT = 5 # Number of web pages per search
WEB_MAX_SIZE = 45 # Max text blocks per web page
WEB_PLUGIN_ENABLED_TEXT  = "Web        : enabled"
WEB_PLUGIN_DISABLED_TEXT = "Web        : disabled"
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
WEB_SEARCH_SYSTEM_PROMPT = "You write a web search query to obtain relevant results. Think carefully, use as much reasoning as the task requires, and verify your output before responding."
WEB_SEARCH_GENERATE_QUERY = """Generate an effective web search query (maximum 20 words) for the following TOPIC.

QUERY OPTIMIZATION:
- Select the most relevant keywords, names, locations, and specific details.
- Prefer concise, focused queries. Avoid filler words, repetition, and unnecessary constraints.
- Use unquoted keywords by default to allow flexible search engine matching.
- Use double quotes around specific phrases ONLY when exact matching would improve relevance (e.g., error messages, titles, distinctive names, or exact expressions).
- Never surround the entire query with quotation marks unless searching for that exact complete phrase.
- Never escape quotation marks or include backslashes.
- Use search operators (e.g., site:) only when they meaningfully improve results.
- Choose the most appropriate search language for the topic and location.
- Preserve important proper names, identifiers, technical terms, and explicit constraints.
- Do not invent facts, names, dates, or restrictions not supported by the TOPIC.
- Consider previous web searches only when they address the same specific information need as the current TOPIC. Do not avoid useful queries merely because they were used for related but different objectives.
- If previous searches for the same information need were insufficient, adapt the query based on what remains unanswered. Refine, broaden, or use alternative terminology, languages, or sources as appropriate. Prioritize relevance over novelty; reuse a previous query when justified.

EXAMPLES:
TOPIC = python errors
QUERY = common Python programming errors fixes

TOPIC = japanese festivals
QUERY = traditional Japanese festivals history celebrations

TOPIC = Christmas markets in Berlin
QUERY = Weihnachtsmärkte Berlin Öffnungszeiten Standorte

TOPIC = Python error No module named requests
QUERY = "No module named requests" Python fix

TOPIC = official PyTorch documentation
QUERY = PyTorch documentation site:pytorch.org

OUTPUT:
Output ONLY the final search query on a single line.
Do not include headings, explanations, comments, code fences, or unnecessary surrounding quotation marks.

TOPIC = """
WEB_SEARCH_TARGET_SYSTEM_PROMPT = "You are a research manager. Your job is to tell a junior researcher exactly what information to look for. Think carefully, use as much reasoning as the task requires, and verify your output before responding."
WEB_SEARCH_GENERATE_TARGET = """Analyze the USER_REQUEST.
Define a clear, concise "Extraction Goal" for the summarizer.
This goal must specify exactly what facts, numbers, or details to extract from the web pages.

Then, on the final line, output ONLY the extraction goal string. Don't write titles, headings or comments.

USER_REQUEST = """
WEB_SEARCH_REVIEW_1 = """Does the following WEB_SUMMARY provide relevant information for the REQUESTED_GOAL? Reason step-by-step:
1. Identify key goal elements.
2. Check if summary matches them.
3. Decide if it's sufficient.

Reflect on your reasoning: Ensure it is based strictly on relevance and sufficiency.

Answer YES only if WEB_SUMMARY contains sufficient information to address all essential parts of REQUESTED_GOAL. Otherwise, answer NO. Relevant but incomplete information is not sufficient.

Then, on the final line, respond ONLY with YES or NO. Do not add explanations or any other text.

REQUESTED_GOAL = """
WEB_SEARCH_REVIEW_2 = "\n\nWEB_SUMMARY = "
WEB_SEARCH_ERROR = "\nUnable to parse web page."
WEB_SEARCH_TAG = "\n[WEB SEARCH] "
WEB_SUMMARY_REVIEW_1 = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you have performed a web search.\n\nWeb search query: "
WEB_SUMMARY_REVIEW_2 = "\n\nWeb search result: "
WEB_SEARCH_FAILED_TEXT = "\n---\n" + WEB_SEARCH_TOOL_NAME + ": you performed a web search but it didn't return any results."
WEB_DIRECT_SEARCH = "Direct Link Navigation"
WEB_URL_PATTERN = r'(https?://[^\s<>"]+|www\.[^\s<>"]+)'
TOOL_DELIMITER = "\n---\n"

# TELEGRAM PLUGIN
TELEGRAM_PLUGIN_ENABLED_TEXT  = "Telegram   : enabled"
TELEGRAM_PLUGIN_DISABLED_TEXT = "Telegram   : disabled"
ENABLE_TELEGRAM_PLUGIN_KEY = "ENABLE_TELEGRAM_PLUGIN"
TELEGRAM_BOT_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
TELEGRAM_USER_ID_KEY = "TELEGRAM_USER_ID"

# IMAGE GENERATION PLUGIN
IMAGE_GENERATION_PLUGIN_ENABLED_TEXT  = "Image Gen  : enabled"
IMAGE_GENERATION_PLUGIN_DISABLED_TEXT = "Image Gen  : disabled"
ENABLE_IMAGE_GENERATION_PLUGIN_KEY = "ENABLE_IMAGE_GENERATION_PLUGIN"
IMAGE_GENERATION_MODEL_KEY = "IMAGE_GENERATION_MODEL"
IMAGE_GENERATION_LORA_KEY = "IMAGE_GENERATION_LORA"
IMAGE_GENERATION_TYPE_KEY = "IMAGE_GENERATION_TYPE"
IMAGE_GENERATION_SPECS_KEY = "IMAGE_GENERATION_SPECS"
IMAGE_GENERATION_NEGATIVE_PROMPT_KEY = "IMAGE_GENERATION_NEGATIVE_PROMPT"
IMAGE_GENERATION_WIDTH_KEY = "IMAGE_GENERATION_WIDTH"
IMAGE_GENERATION_HEIGHT_KEY = "IMAGE_GENERATION_HEIGHT"
IMAGE_GENERATION_TOOL_NAME = "generate_image"
IMAGE_DESCRIPTION_SYSTEM_PROMPT = """You are an expert visual scene interpreter. Transform the current image request into one clear natural-language description of a single static image.

Treat the provided request as the only image to describe. Use conversation context only to resolve explicit or clearly implied references in the current request; otherwise ignore it. Never carry over visual details merely because they appear in conversation context.

Never continue a task list, plan another task, describe a previous or next image, mention tool use or task execution, include meta commentary, or repeat the scene description.

Think carefully, use as much reasoning as the task requires, and verify your output before responding."""
IMAGE_GENERATION_SYSTEM_PROMPT = "You are an expert prompt engineer for image generation. Craft clear, visual descriptions that strictly follow the provided instructions for optimal results. Think carefully, use as much reasoning as the task requires, and verify your output before responding."
IMAGE_GENERATION_TOOL_DESCRIPTION = """Generate a static image based on a textual description. Use this tool only if the task:

- Involves describing visual content that benefits from image generation, such as illustrations, representations of scenes/objects, or visualizing elements like characters, landscapes, or nature scenes in a story (e.g., settings or key moments), OR
- Explicitly instructs to 'generate an image', 'create a picture', or similar actions.

DO NOT USE this tool for non-visual descriptions or tasks that do not involve visuals, or if the request explicitly instructs NOT to generate images (e.g., "no images", "don't generate an image")."""
GENERATE_IMAGE_TEXT = """GLOBAL CONSTRAINT:
Do not include blur or optical softness effects of any kind. The sole exception is motion blur: preserve it only when explicitly specified in TEXT; otherwise, do not add it. Omit all other blur, soft-focus, out-of-focus, shallow depth of field, or bokeh effects even if TEXT specifies them.

Analyze TEXT and determine its nature:

If TEXT already contains visual descriptions (subjects, objects, scenes, physical attributes, colors, materials, compositions, etc.):
- PRESERVE all specified details exactly as given, except where the global constraint above requires omission
- You may ADD complementary visual details that enhance the scene
- NEVER contradict, oppose, or modify any other TEXT-specified attributes

If TEXT is conceptual, abstract, or non-visual (ideas, emotions, stories without visual details):
- Think about what static image best represents it
- Create a clear visual description from scratch

Generate an image description (max 80 words). Prioritize TEXT-specified details over added details. Focus on key visible elements, styles, and scenes. Output ONLY the image description. TEXT: """
GENERATE_IMAGE_PROMPT_TEXT = """First, think about what static image best represents TEXT. Then think about the best single composition for that image. Use standard terms like the following examples:
- extreme close-up (isolates a single, small detail)
- close-up (a person's head and shoulders)
- medium shot (a person from the waist to head)
- medium long shot (a person from the knees to head)
- full shot (a person or object fully visible in its setting)
- wide shot (the subject is small in a large environment)
- panoramic (a vast landscape or cityscape)

When using close-up for people or humanoids, include "head and shoulders" to maintain framing.

When using medium shot for people or humanoids, include "waist up" to maintain framing.

When using medium long shot for people or humanoids, include "knees up" to maintain framing.

If none of these are the best fit, you can use other standard compositional terms. The final prompt should be a clear, physical description of the scene, including any physical descriptions of people (body type, physique, facial features, proportions).

IMPORTANT: The chosen composition must show all important details retained in the final prompt. If the TEXT describes elements that would be cut off by the requested framing (e.g., thigh-high stockings in a "waist up" shot, bare feet in a "knees up" shot, floor-length dress in a "head and shoulders" shot), use a wider composition that can include those details.

If the TEXT includes a specific artistic style (like "in the style of H.R. Giger" or "gritty"), you should include it.

Crucially, if the TEXT describes a specific, physical light source that is part of the scene (like a 'candle', 'fireplace', 'neon sign', or 'flashlight'), you SHOULD include it.

Remove general lighting style terms like 'dramatic lighting', 'cinematic lighting', or 'moody lighting'. Keep specific details about light sources.

Remove general rendering or medium terms like 'photorealistic', 'anime', or '3D render'.

Do not introduce or preserve blur or optical softness effects of any kind. The sole exception is motion blur, which may be preserved only if it is already explicitly present in TEXT; otherwise, do not add it.

Here are examples of how to correctly format the final prompt:
---
EXAMPLE 1 (Removing a stylistic light description)
TEXT = a knight in shining armor on a horse, under dramatic, moody lighting
CORRECT PROMPT = full shot: knight in shining armor riding horse.

EXAMPLE 2 (Keeping light source details)
TEXT = a slender elven archer with long auburn hair and emerald eyes by a flickering oil lantern under cinematic lighting
CORRECT PROMPT = full shot: slender elven archer with long auburn hair and emerald eyes, by flickering oil lantern.

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
CORRECT PROMPT = full shot: curvy blonde model with blue eyes wearing elegant black lingerie and sheer thigh-high stockings.

EXAMPLE 7 (Adjusting composition to show described details)
TEXT = a medium shot of a Roman centurion in polished lorica segmentata and leather caligae standing on marble steps
CORRECT PROMPT = full shot: Roman centurion in polished lorica segmentata and leather caligae, standing on marble steps.

EXAMPLE 8 (Adjusting composition to show described details)
TEXT = a headshot of a woman in an elegant floor-length gown
CORRECT PROMPT = full shot: woman wearing elegant floor-length gown.
---

Finally, using these examples as a guide, write an image generation prompt describing ONLY the visible elements, the requested artistic style, and any physical light sources.

Order details by visual importance. Start with the composition and primary subject, followed by the subject's defining physical attributes, clothing, and action. Place environment, requested artistic style permitted by the rules above, and physical light sources afterward unless they are central to the image. Put the least important details last.

Don't describe multiple images or compositions. Don't describe camera settings, camera movements, or camera zoom. Don't use metaphors or poetic language. Don't write titles, headings or comments. Write exactly one concise sentence. Use telegraphic phrasing: bind attributes, details, and clothing to the subject using words like "with" or "wearing", but use commas to separate the main subject from the background and lighting. Drop unnecessary filler words (like "a", "an", "the"). Do not exceed 30 words. This is a HARD OUTPUT LIMIT and takes priority over completeness. Preserve as many important specific visual details from TEXT as possible within that limit. Order details by visual importance, placing the most important concepts earliest. If necessary, omit the least important details first rather than exceed 30 words. Don't write the number of words.

The process below is a verification and finalization procedure only. It does not replace, weaken, or override any instruction above. Every rule above remains mandatory during the Draft, Review, and Finalize steps.

Before finalizing, follow this process inside your <think>...</think> block:

1. Draft:
   * First create a complete draft of the image-generation prompt.
   * Apply all composition, visibility, style, lighting, ordering, telegraphic-phrasing, and 30-word rules above.

2. Review the draft carefully against TEXT:
   * Source-detail check: verify that every retained subject, physical attribute, clothing item, object, action, environment detail, requested artistic style permitted by the rules above, and physical light source accurately represents TEXT. Do not accidentally change, invert, replace, or invent details.
   * Source-word check: for distinctive words or terms taken from TEXT, preserve their spelling exactly unless an earlier rule explicitly requires omitting or transforming them. Never "correct", expand, complete, or substitute a proper noun, named entity, unusual term, identifier, or quoted wording merely because another spelling seems more familiar.
   * Generated-word check: inspect every newly generated word and phrase for obvious accidental misspellings, malformed words, truncated words, accidental word concatenations, duplicated fragments, or incomplete phrases. Correct those errors before finalizing.
   * Contradiction check: ensure no generated detail contradicts anything explicitly specified in TEXT.
   * Composition check: ensure the chosen framing can visibly include all important details retained in the prompt.
   * Constraint check: ensure prohibited blur or optical-softness terms, unwanted general lighting terms, rendering-medium terms, camera settings, metaphors, poetic language, and unnecessary filler have not slipped into the draft.
   * Completeness check: ensure every retained word and phrase is complete and the prompt does not end abruptly.

3. Finalize:
   * Finalize the reviewed draft as exactly one concise telegraphic sentence, making only changes required by the rules above.
   * Order details by visual importance according to the rules above.
   * Count the words and ensure the final prompt does not exceed 30 words.
   * If it exceeds 30 words, remove the least important complete detail first and count again. Never truncate a word or phrase to satisfy the limit.
   * Perform one final read for complete words, complete phrases, clear telegraphic coherence, fidelity to TEXT, and compliance with every rule above.
   * If any problem remains, correct it before outputting the final prompt.

Only after completing all three steps output the final image-generation prompt.

OUTPUT CONTRACT — read carefully:
- All reasoning, drafts, reviews, checks, corrections, and word counting must stay inside the <think>...</think> block.
- After the closing </think> tag, output ONLY the final image-generation prompt.
- Nothing else after </think>. No explanations, reasoning, drafts, review notes, word counts, quotes, headings, or comments.

TEXT = """
IMAGE_GENERATION_TAG = "\n[IMAGE] "
IMAGE_GENERATION_OK_TEXT_1 = "\n---\n" + IMAGE_GENERATION_TOOL_NAME + ": image generated successfully.\n\nImage description: "
IMAGE_GENERATION_OK_TEXT_2 = "\n\nImage generation prompt: "
IMAGE_GENERATION_OK_TEXT_3 = "\n\nImage name: "
IMAGE_GENERATION_ERROR = "\n---\n" + IMAGE_GENERATION_TOOL_NAME + ": unable to generate image."

# CODE RUNNER PLUGIN
CODE_RUNNER_PLUGIN_ENABLED_TEXT  = "Code Runner: enabled"
CODE_RUNNER_PLUGIN_DISABLED_TEXT = "Code Runner: disabled"
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
- Working directory: Any files generated by other tools are available in the current working directory and can be accessed directly by filename (e.g., open('image_1.png')).

DO NOT USE this tool for:
- Logical puzzles, riddles, or brain teasers that can be solved via deduction.
- Simple math or motion problems (e.g., calculating travel time given speed and distance) that do not require a formal algorithm.
- Situational reasoning where the answer depends on interpreting a story or set of rules.
- Any task that a person could solve with a simple pen-and-paper calculation in under a minute.
- Requests where the user explicitly instructs NOT to write or execute code (e.g., "don't write code", "don't run code", "no programming")."""
CODE_RUNNER_SYSTEM_PROMPT = """You are an expert Python programmer writing production-quality code for console execution.

Think thoroughly and systematically, using as much reasoning as the task requires. Consider relevant alternatives and validate key assumptions. Before responding, trace the program's execution from entry point to output, verifying function calls, data flows, external dependencies, important error paths, and expected results. Identify and correct any problems found before finalizing.

CORE CONSTRAINTS:
- Single-pass execution: no while True, no infinite loops, no polling
- Console-only output via print() with clear, labeled messages — no GUIs, no audio
- No user input() calls
- Use real APIs and operations. Never invent credentials or use placeholder API keys or tokens.
- Exactly 4 spaces for indentation. Never tabs. Never mixed.
- Only straight ASCII quotes (`"` or `'`). Never curly/smart quotes.
- If third-party packages are needed, put exactly one line at the very top: `# pip install package1 package2`. Otherwise, no pip install line at all.
- You may read and write files in the current working directory ONLY when needed.
- Write purely executable code: NO comments and NO docstrings (except the single `# pip install` line at the top if required). Use type hints where they improve clarity.
- Never print or expose passwords, API keys, authentication tokens, or other secrets, including in diagnostics.
- Define reusable functions and classes outside the main guard; execute the mission only inside `if __name__ == "__main__":`."""
CODE_RUNNER_COT_TEXT = """Follow all CORE CONSTRAINTS from the system prompt.

Before outputting code, think carefully through these steps:
1. Understand the MISSION and identify the exact result required, preserving all requirements and constraints.
2. Choose the simplest reliable solution. Verify API requirements, credentials, parameters, response fields, units, and dependencies when possible. If a required service or credential is unavailable, use a valid alternative or report the limitation; never fabricate results.
3. Implement clean, reusable functions and classes. Validate inputs, function outputs, and external API responses where necessary, including required fields, types, ranges, and units. Handle errors explicitly; never hide failures or fabricate success.
4. Execute the actual mission inside `if __name__ == "__main__":`, printing real results. On failure, report the error and exit with a nonzero status.
5. Reread the entire program carefully. Check correctness, edge cases, API assumptions, syntax, indentation, variable scope, dependencies, and potential Ruff errors. Correct all problems found.

Do not generate unit tests unless the MISSION explicitly requires them.

Output the complete Python code in a single markdown block (```python ... ```), with no other text."""
CODE_RUNNER_GENERATION_TEXT = "Write a single-file Python program to solve the following MISSION.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nMISSION: "
CODE_RUNNER_FIX_PROGRAM_TEXT = "The previous solution did not fully satisfy the MISSION. Review the previous program and latest results, fix root causes, preserve correct functionality, and avoid unnecessary changes.\n\n" + CODE_RUNNER_COT_TEXT + "\n\nPrevious program:\n\n"
CODE_RUNNER_MISSION_TEXT = "\n\nMISSION: "
CODE_RUNNER_PROGRAM_OUTPUT_REVIEW = """Analyze the execution results to determine if the MISSION is complete.

CRITERIA:
1. Execution Success: The output must show actual results without runtime errors, printed failures, or incomplete work. A claimed success without evidence is not success.
2. Mission Fulfillment: Check that the code and actual results fully and correctly solve the original MISSION, including required data, operations, and external API assumptions.
3. Reliability: The program must validate important inputs and external results where needed, and must not fabricate results, hide errors, or treat failed operations as success.

Answer YES only if all three criteria are satisfied. If the available evidence is insufficient, answer NO.

CRITICAL: The very last line of your response must be exactly "YES" or "NO".

PROGRAM_CODE:
"""
CODE_RUNNER_EXTENDED_ACTION_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you have generated a Python program for this task.\n\nSource code:\n\n"
CODE_RUNNER_FAILED_TEXT = "\n---\n" + CODE_RUNNER_TOOL_NAME + ": you were not able to write a Python program for this task."
CODE_RUNNER_GENERATE_CODE_TAG = "\n[CODE RUNNER] Generating code ...\n"
CODE_RUNNER_RUN_PROGRAM_TAG = "\n[CODE RUNNER] 発進！\n"
CODE_RUNNER_MAX_REVIEWS = 10
CODE_RUNNER_LINT_OUTPUT_LIMIT = 5000  # Chars
CODE_RUNNER_PROGRAM_OUTPUT_LIMIT = 30000  # Chars
CODE_RUNNER_PROGRAM_OUTPUT_ERROR = "\n\n[ERROR: Program output truncated. Refine the code to print specific data points or summaries instead of raw dumps.]"

# CODEX PLUGIN
CODEX_PLUGIN_ENABLED_TEXT  = "Codex      : enabled"
CODEX_PLUGIN_DISABLED_TEXT = "Codex      : disabled"
ENABLE_CODEX_PLUGIN_KEY = "ENABLE_CODEX_PLUGIN"


# WEB PLUGIN TOOL

def web_search(primeDirectives: str, action: str, context: list[str]) -> str:
    aux_context = context[:]
    mission_completed = False
    summary = ""
    raw_summary = ""
    urls: list[str] = []
    query = WEB_DIRECT_SEARCH

    # Compute web search target
    target_prompt = WEB_SEARCH_GENERATE_TARGET + action
    target = core.send_prompt(WEB_SEARCH_TARGET_SYSTEM_PROMPT, target_prompt, aux_context, hide_reasoning = True)

    # Get the last line
    target = target.split('\n')[-1].strip()

    # Check if the user prompt provided specific URLs
    user_prompt = action.split(TOOL_DELIMITER, 1)[0]
    urls = re.findall(WEB_URL_PATTERN, user_prompt)

    if urls:
        comms.printSystemText(WEB_SEARCH_TAG + query + "\n\n" + target)
    else:
        # Generate web search query
        query = core.send_prompt(WEB_SEARCH_SYSTEM_PROMPT, WEB_SEARCH_GENERATE_QUERY + target, aux_context, hide_reasoning = True)

        # Normalize escaped quotation marks
        query = query.replace(r'\"', '"')

        # Get the last line
        query = query.split('\n')[-1].strip()

        comms.printSystemText(WEB_SEARCH_TAG + query + "\n\n" + target)

        # Run the web search
        urls = web.search(query, WEB_SEARCH_PAGE_LIMIT)

    for url in urls:
        comms.printSystemText("\n" + url)
        text = web.scrape(url)
        blockArray = core.split_text_in_blocks(text)

        web_summary = core.summarize_block_array(target, blockArray[:WEB_MAX_SIZE])

        if web_summary:
            raw_summary = core.update_summary(target, raw_summary, web_summary)

            # Prevent prompt injection
            summary = core.DATA_ONLY_START_TAG + raw_summary + core.DATA_ONLY_END_TAG

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


# IMAGE GENERATION TOOL

image_generation_counter: int = 1

def generate_image(primeDirectives: str, action: str, context: list[str]) -> str:
    global image_generation_counter
    extended_action = action
    image: Image.Image = None

    # Preserve the last conversation turn without assistant reasoning
    aux_context = context[:1]

    if len(context) >= 3:
        aux_context += [context[-2], core.remove_reasoning(context[-1])]

    # Generate visual description
    image_description = core.send_prompt(IMAGE_DESCRIPTION_SYSTEM_PROMPT, GENERATE_IMAGE_TEXT + extended_action, aux_context, hide_reasoning = True)

    # Generate image generation prompt
    image_generation_prompt = core.send_prompt(IMAGE_GENERATION_SYSTEM_PROMPT, GENERATE_IMAGE_PROMPT_TEXT + image_description, [], hide_reasoning = True)

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
        comms.send_image_telegram_bot(path)

    return extended_action


# CODE RUNNER TOOL

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
            prompt = CODE_RUNNER_FIX_PROGRAM_TEXT + program + "\n\n" + lint_output + "\n\n" + program_output

        # Generate code
        comms.printSystemText(CODE_RUNNER_GENERATE_CODE_TAG)
        response = core.send_prompt(system_prompt, prompt, aux_context, hide_reasoning = True)
        comms.printSystemText(response)

        # Extract code
        code_blocks = list(re.finditer(
            r"(?m)^[ \t]*(?P<fence>`{3,})[^\r\n`]*\r?\n(?P<body>.*?)(?:^[ \t]*(?P=fence)[ \t]*(?:\r?\n|\Z)|\Z)",
            response,
            re.DOTALL
        ))

        # Get last code block
        if code_blocks:
            program = code_blocks[-1].group("body").strip()
        else:
            program = response.strip()

        # Run program
        comms.printSystemText(CODE_RUNNER_RUN_PROGRAM_TAG)
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
            mission_completed = core.binary_question(system_prompt, prompt, aux_context)
        else:
            comms.printSystemText(lint_output)

        review += 1

    if program:
        extended_action = action + CODE_RUNNER_EXTENDED_ACTION_TEXT + program + "\n\n" + (program_output or lint_output)
    else:
        extended_action = action + CODE_RUNNER_FAILED_TEXT

    return extended_action


# INITIALIZE

try:
    # Workspace
    if not os.path.exists(PLUGIN_WORKSPACE_FOLDER):
        os.makedirs(PLUGIN_WORKSPACE_FOLDER)

    core.print_system_text(PLUGINS_TEXT)

    # Code Runner plugin
    if core.config.get(ENABLE_CODE_RUNNER_PLUGIN_KEY, '').upper() == "YES":
        from plugins.code_runner import code_runner
        core.print_system_text(CODE_RUNNER_PLUGIN_ENABLED_TEXT)
        toolchain.add_tool(CODE_RUNNER_TOOL_NAME, CODE_RUNNER_TOOL_DESCRIPTION, code_runner_action)
    else:
        core.print_system_text(CODE_RUNNER_PLUGIN_DISABLED_TEXT)

    # Codex plugin
    if core.config.get(ENABLE_CODEX_PLUGIN_KEY, '').upper() == "YES":
        toolchain.codex_enabled = True

        core.print_system_text(CODEX_PLUGIN_ENABLED_TEXT)
    else:
        core.print_system_text(CODEX_PLUGIN_DISABLED_TEXT)

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

