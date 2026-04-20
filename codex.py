import core
import comms
import json
import re
from plugins.codex import codex_operations
from plugins.codex.codex_operations import CODEX_LIST_ALL
from plugins.codex.codex_operations import CODEX_NO_RESULT

CODEX_SYSTEM_PROMPT = "You are a precise data extraction assistant that manages the Codex, a long-term memory tool. Extract structured information exactly as instructed, with no additions or commentary."
USER_PROFILE_TEXT = "User profile"
CODEX_EXTRACT_QUERY_PROMPT = f"""Extract the search intent from ACTION and output ONLY a short descriptive search phrase (max 20 words) suitable for a semantic knowledge base query. For queries about the user's personal information, identity, or background, use the phrase "{USER_PROFILE_TEXT}".
If ACTION describes listing, browsing, showing, or displaying all Codex entries or the Codex itself (e.g. "show me the Codex", "what's in the Codex", "list all Codex entries"), output exactly: "{CODEX_LIST_ALL}".
If ACTION is a natural conversation starter like a greeting (e.g. "hi", "hello", "hey"), use the phrase "{USER_PROFILE_TEXT}".
Output ONLY the search phrase or "{CODEX_LIST_ALL}". No commentary.
ACTION = """
CODEX_EXTRACT_WRITE_PROMPT = f"""Output **EXACTLY one valid JSON object** and nothing else.
No markdown, no code fences, no preamble, no explanation, no extra text whatsoever.

Extract the fields **strictly from the ACTION provided at the end**.
Base your response exclusively on that text. Do not add, invent, or use any information outside of it.

You must use this exact structure:
{{
  "title": "short specific title for the knowledge entry",
  "content": "the most reusable, self-contained knowledge",
  "tags": "comma-separated lowercase keywords"
}}

STRICT RULES (apply in this exact order):
1. "title": short specific title for the knowledge entry; for personal facts about the user use the stable title "{USER_PROFILE_TEXT}"
2. "content":
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

ACTION = """
CODEX_MERGE_TEXT = f"""\n\nIMPORTANT: This is a MERGE operation for the exact title "{{title}}".
Keep ONLY facts that are directly relevant to this title.
Drop any facts that do not belong to this title (e.g. general user profile facts belong only in "{USER_PROFILE_TEXT}").
Add the new facts and keep previously known facts that still apply to this title.
Only drop facts that will be obsolete after adding the new facts.

PREVIOUSLY_KNOWN_FACTS = """
CODEX_EXTRACT_TITLE_PROMPT = """Extract the entry title to delete from ACTION and output ONLY the exact title string. Do not include dates, tags, or any other metadata. No commentary.
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

    # Extract the JSON object in case there is preamble or trailing text
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1

    if start != -1 and end > start:
        cleaned = cleaned[start:end]

    return json.loads(cleaned)


def read_codex(action: str, context: list[str]) -> str:
    aux_context = context[:]

    # Extract search query from the action
    query = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_QUERY_PROMPT + action, aux_context, hide_reasoning = True).strip()

    if not query:
        return action

    result = codex_operations.read_codex(query)

    read_data = query + CODEX_RESULT_TEXT

    if result == CODEX_NO_RESULT:
        read_data += CODEX_NOT_FOUND_TEXT
    else:
        read_data += result
        comms.printSystemText(CODEX_READ_TAG + read_data)

    return action + CODEX_READ_TEXT + read_data


def write_codex(action: str, context: list[str]) -> str:
    aux_context = context[:]

    # Extract title, content and tags from the action
    response = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_WRITE_PROMPT + action, aux_context, hide_reasoning = True)

    try:
        fields = _parse_json_response(response)
        title = str(fields.get("title", "")).strip()
        content = str(fields.get("content", "")).strip()
        tags = str(fields.get("tags", "")).strip()
    except (json.JSONDecodeError, AttributeError, ValueError):
        title = ""
        content = ""
        tags = ""

    if not title or not content:
        comms.printSystemText(CODEX_WRITE_EXTRACT_ERROR)
        return action + CODEX_WRITE_ERROR

    # Check if there are previously known facts for this title
    known_facts = codex_operations.read_codex(title)

    if known_facts and known_facts != CODEX_NO_RESULT:
        # Clean the metadata header
        if '<entry' in known_facts:
            contents = re.findall(r'<entry[^>]*>(.*?)</entry>', known_facts, re.DOTALL)
            known_facts = '\n'.join(c.strip() for c in contents)

        prompt = CODEX_EXTRACT_WRITE_PROMPT + action + CODEX_MERGE_TEXT.format(title=title) + known_facts
        response = core.send_prompt(CODEX_SYSTEM_PROMPT, prompt, aux_context, hide_reasoning = True)

        try:
            fields = _parse_json_response(response)
            content = str(fields.get("content", "")).strip()
        except Exception:
            pass  # fallback if merge fails

    result = codex_operations.write_codex(title, content, tags)

    write_data = title + CODEX_CONTENT_TEXT + content + CODEX_TAGS_TEXT + tags + CODEX_RESULT_TEXT + result

    comms.printSystemText(CODEX_WRITE_TAG + write_data)

    return action + CODEX_WRITE_TEXT + write_data


def delete_codex(action: str, context: list[str]) -> str:
    aux_context = context[:]

    # Extract entry title from the action
    title = core.send_prompt(CODEX_SYSTEM_PROMPT, CODEX_EXTRACT_TITLE_PROMPT + action, aux_context, hide_reasoning = True).strip()

    # === HARD PROTECTION FOR USER PROFILE ===
    if title.lower() == USER_PROFILE_TEXT.lower():
        return action

    result = codex_operations.delete_codex(title)

    delete_data = title + CODEX_RESULT_TEXT + result

    comms.printSystemText(CODEX_DELETE_TAG + delete_data)

    return action + CODEX_DELETE_TEXT + delete_data
