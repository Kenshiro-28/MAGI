import core
import comms
import json
import re
from plugins.codex import codex_operations
from plugins.codex.codex_operations import CODEX_LIST_ALL
from plugins.codex.codex_operations import CODEX_NO_RESULT

CODEX_SYSTEM_PROMPT = "You are a precise data extraction assistant that manages the Codex, a long-term memory tool. Extract structured information exactly as instructed, with no additions or commentary."
USER_PROFILE_TEXT = "User profile"
CODEX_EXTRACT_QUERY_PROMPT = f"""Extract the search intent from ACTION.

For queries about the user's personal information, identity, or background — including requests to list facts about the user (e.g. "tell me about myself", "list everything you remember about me") — use the phrase "{USER_PROFILE_TEXT}".
If ACTION asks to list or show ALL stored entries with no user-scope restriction (e.g. "list all your memories", "what's in the Codex", "list all Codex entries"), output exactly: "{CODEX_LIST_ALL}".
If ACTION is a natural conversation starter like a greeting (e.g. "hi", "hello", "hey"), use the phrase "{USER_PROFILE_TEXT}".

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output ONLY a short descriptive search phrase (max 20 words) OR exactly "{CODEX_LIST_ALL}".
- Nothing else after </think>. No commentary, no quotes, no explanation.

ACTION = """
CODEX_EXTRACT_WRITE_PROMPT_1 = """Extract structured fields from the ACTION below into a JSON object.

You must use this exact structure:
{
  "title": "short specific title for the knowledge entry",
  "content": "the most reusable, self-contained knowledge",
  "tags": "comma-separated lowercase keywords"
}

The ACTION to extract from is delimited below.

=== BEGIN ACTION ===
"""
CODEX_EXTRACT_WRITE_PROMPT_2 = f"""
=== END ACTION ===

Now extract the fields from the ACTION above into one valid JSON object.

STRICT RULES (apply in this exact order):
1. "title": short specific title for the knowledge entry; for personal facts about the user use the stable title "{USER_PROFILE_TEXT}"
2. "content":
   - Never glue words together or remove spaces between words.
   - If the ACTION contains a full Python script that executed successfully, store the ENTIRE script as-is without any summarization or extraction.
   - For any other knowledge, store the most reusable, self-contained portion of the knowledge.
   - If the full content exceeds 32000 characters, keep the most important and reusable parts (imports, key functions/classes, main logic, critical information) while preserving structure and readability.
   - For personal facts about the user, consolidate as a list of sentences.
3. CRITICAL RULE: Only include information that is directly relevant to the chosen title.
   Drop any facts that do not belong to this exact title (e.g. general user profile facts belong only in "{USER_PROFILE_TEXT}").
4. "tags": comma-separated lowercase keywords

Example of correct output:
{{
  "title": "Drone Swarm Urban Reconnaissance Protocol",
  "content": "Autonomous drone swarm deploys 12-24 units in mesh network formation. Each unit maintains 50m spacing with real-time AI flocking. Primary objective: penetrate urban signal jamming and provide live 360° ISR feed to command node while preserving formation integrity.",
  "tags": "drone, swarm, reconnaissance, urban, ai, electronic-warfare"
}}

When creating the JSON, follow this process inside your <think>...</think> block:
1. First, create a draft of the "content" field based on the ACTION.
2. Review the draft carefully for accuracy:
   - Do not change numbers, dates, names, spellings, or specific terms unless explicitly required.
   - Check for glued words or missing spaces and preserve original wording exactly.
   - Preserve the original meaning and wording as faithfully as possible.
   - Only apply changes if they are clearly needed.
3. After the content review, do a quick structure check:
   - Ensure the JSON has the correct keys: "title", "content", and "tags".
   - Make sure the output will be valid JSON.
4. Only after both reviews, output the final JSON object.

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output EXACTLY one valid JSON object and NOTHING ELSE.
- Nothing else after </think>. No markdown, no code fences, no preamble, no explanation, no trailing text."""
CODEX_RETRY_WRITE_PROMPT = """\n\nIMPORTANT: The previous attempt failed to produce valid JSON.
Re-read the STRICT RULES and OUTPUT CONTRACT carefully.
Pay special attention to factual accuracy and do not alter details from the original ACTION.
Output EXACTLY one valid JSON object and NOTHING ELSE."""
CODEX_MERGE_TEXT = """

=== BEGIN PREVIOUSLY_KNOWN_FACTS ===
{known_facts}
=== END PREVIOUSLY_KNOWN_FACTS ===

MERGE OPERATION for title "{title}".

Inside your <think>...</think> block, follow this process **before** reading the merge rules below:

1. Create a draft of the merged content.
2. Review the draft against PREVIOUSLY_KNOWN_FACTS with high conservatism:
   - Never glue words together or remove spaces between words.
   - Remove only **exact or very clear near-duplicates**.
   - Consolidate facts only when they clearly describe the **exact same information**.
   - Do **not** rephrase, rewrite, or remove facts simply because they appear awkwardly worded, unusual, or messy.
   - Do not alter numbers, dates, names, spellings, or specific terms unless a fact is clearly SUPERSEDED.
   - When in doubt, always preserve the original content.
   - However, if you find clearly redundant or repetitive information across multiple facts, you may consolidate them into a cleaner, single statement (only when you are confident it does not lose important details).
3. After the review, do a quick structure check to ensure the final JSON is valid.
4. Only after completing the conservative review, apply the merge rules below and output the final JSON.

DEFAULT BEHAVIOR (strict):
Every fact from PREVIOUSLY_KNOWN_FACTS must be preserved unless it is **clearly SUPERSEDED** or an **exact/near duplicate**.

The "content" field must contain the consolidated UNION of all PREVIOUSLY_KNOWN_FACTS and the new facts from the ACTION.

SUPERSEDED → Keep the new fact, drop the old one.
DUPLICATE / NEAR-DUPLICATE → Keep only the clearer or more recent version.
UNCERTAIN / AWKWARD / MESSY CONTENT → Preserve as-is. Do not clean just because it looks messy.

Be extremely conservative. Do not remove or significantly modify existing facts unless there is clear and unambiguous justification. Slow accumulation of minor redundancy is acceptable if it avoids any risk of losing useful information.

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output EXACTLY one valid JSON object and NOTHING ELSE.
- Nothing else after </think>. No markdown, no code fences, no preamble, no explanation, no trailing text."""
CODEX_EXTRACT_TITLE_PROMPT = """Extract the entry title to delete from ACTION.
Do not include dates, tags, or any other metadata.

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output ONLY the exact title string.
- Nothing else after </think>. No quotes, no commentary.

ACTION = """
CODEX_READ_TAG = "\n[CODEX] Read\n\nQuery: "
CODEX_WRITE_TAG = "\n[CODEX] Write\n\nTitle: "
CODEX_DELETE_TAG = "\n[CODEX] Delete\n\nTitle: "
CODEX_TOOL_TEXT = "Codex long-term memory tool"
CODEX_READ_TEXT = "\n---\n" + CODEX_TOOL_TEXT + ": you have performed a memory read operation:\n\nQuery: "
CODEX_RESULT_TEXT = "\n\nResult: "
CODEX_NOT_FOUND_TEXT = "No relevant entries found."
CODEX_WRITE_TEXT = "\n---\n" + CODEX_TOOL_TEXT + ": you have performed a memory write operation:\n\nTitle: "
CODEX_CONTENT_TEXT = "\n\nContent: "
CODEX_TAGS_TEXT = "\n\nTags: "
CODEX_WRITE_EXTRACT_ERROR = "\n[CODEX] Write\n\nERROR: Could not extract title or content."
CODEX_WRITE_ERROR = "\n---\n" + CODEX_TOOL_TEXT + ": memory write operation failed:\n\nReason: Could not extract title or content from the action."
CODEX_DELETE_TEXT = "\n---\n" + CODEX_TOOL_TEXT + ": you have performed a memory delete operation:\n\nTitle: "


def _parse_json_response(response: str) -> dict:
    cleaned = response.strip()

    # Strip markdown fences
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1]

        if cleaned.startswith("json"):
            cleaned = cleaned[4:]

        cleaned = cleaned.strip()

    try:
        # Extract the JSON object in case there is preamble or trailing text
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start != -1 and end > start:
            cleaned = cleaned[start:end]

        json_data: dict = json.loads(cleaned)

        title = str(json_data.get("title", "")).strip()
        content = str(json_data.get("content", "")).strip()
        tags = str(json_data.get("tags", "")).strip()

    except (json.JSONDecodeError, AttributeError, ValueError):
        title = ""
        content = ""
        tags = ""

    return {"title": title, "content": content, "tags": tags}


def read_codex(action: str) -> str:
    # Extract search query from the action
    response = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_QUERY_PROMPT + action, [], hide_reasoning = True)

    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Strip any surrounding quotes
    query = last_line.strip('"\'')

    if not query:
        return ""

    result = codex_operations.read_codex(query)

    read_data = query + CODEX_RESULT_TEXT

    if result == CODEX_NO_RESULT:
        read_data += CODEX_NOT_FOUND_TEXT
    else:
        read_data += result
        comms.printSystemText(CODEX_READ_TAG + read_data)

    return CODEX_READ_TEXT + read_data


def write_codex(action: str) -> str:
    aux_context: list[str] = []

    # Extract title, content and tags from the action
    response = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_WRITE_PROMPT_1 + action + CODEX_EXTRACT_WRITE_PROMPT_2, aux_context, hide_reasoning = True)

    fields = _parse_json_response(response)
    title = fields["title"]
    content = fields["content"]
    tags = fields["tags"]

    if not title or not content:
        # Fix json structure
        retry_prompt = CODEX_EXTRACT_WRITE_PROMPT_1 + action + CODEX_EXTRACT_WRITE_PROMPT_2 + CODEX_RETRY_WRITE_PROMPT
        response = core.send_prompt(CODEX_SYSTEM_PROMPT, retry_prompt, aux_context, hide_reasoning = True)

        fields = _parse_json_response(response)
        title = fields["title"]
        content = fields["content"]
        tags = fields["tags"]

        if not title or not content:
            comms.printSystemText(CODEX_WRITE_EXTRACT_ERROR)
            return CODEX_WRITE_ERROR

    # Check if there are previously known facts for this title
    known_facts = codex_operations.read_codex(title)

    if known_facts and known_facts != CODEX_NO_RESULT:
        # Clean the metadata header
        if '<entry' in known_facts:
            contents = re.findall(r'<entry[^>]*>(.*?)</entry>', known_facts, re.DOTALL)
            known_facts = '\n'.join(c.strip() for c in contents)

        # Merge operation
        prompt = CODEX_EXTRACT_WRITE_PROMPT_1 + action + CODEX_EXTRACT_WRITE_PROMPT_2 + CODEX_MERGE_TEXT.format(title=title, known_facts=known_facts)
        response = core.send_prompt(CODEX_SYSTEM_PROMPT, prompt, [], hide_reasoning = True)

        try:
            fields = _parse_json_response(response)
            new_content = str(fields.get("content", "")).strip()
            new_tags = str(fields.get("tags", "")).strip()

            if new_content:
                content = new_content
            else:
                content = (known_facts + "\n" + content).strip()

            if new_tags:
                tags = new_tags

        except Exception:
            content = (known_facts + "\n" + content).strip()

    # Normalize tags (works for both normal writes and merges)
    if tags:
        tag_list = sorted(set(t.strip().lower() for t in tags.split(",") if t.strip()))
        tags = ", ".join(tag_list)

    result = codex_operations.write_codex(title, content, tags)

    write_data = title + CODEX_CONTENT_TEXT + content + CODEX_TAGS_TEXT + tags + CODEX_RESULT_TEXT + result

    comms.printSystemText(CODEX_WRITE_TAG + write_data)

    return CODEX_WRITE_TEXT + write_data


def delete_codex(action: str) -> str:
    # Extract entry title from the action
    response = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_TITLE_PROMPT + action, [], hide_reasoning = True)

    # Get the last line
    lines = response.split('\n')
    last_line = lines[-1]

    # Strip any surrounding quotes
    title = last_line.strip('"\'')

    if not title:
        return ""

    # === HARD PROTECTION FOR USER PROFILE ===
    if title.lower() == USER_PROFILE_TEXT.lower():
        return ""

    result = codex_operations.delete_codex(title)

    delete_data = title + CODEX_RESULT_TEXT + result

    comms.printSystemText(CODEX_DELETE_TAG + delete_data)

    return CODEX_DELETE_TEXT + delete_data


