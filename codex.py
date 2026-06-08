import core
import comms
import json
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
   - VERBATIM ENTITIES — the ACTION is the ONLY source of truth for the exact characters of every proper noun and named thing (people, places, organizations, brands, products, and the titles of games, films, books, songs, shows, etc.) and of every number, date, version, code, identifier, acronym, URL, file path, command, and quoted string. Transcribe each of these character-for-character from the ACTION. You MAY rephrase the surrounding sentence, but you MUST NOT alter the entity itself in any way: do not expand, complete, abbreviate, translate, re-spell, reorder, or "correct" it, and do not change its capitalization or spacing — not even if your own knowledge suggests a longer, more familiar, more "complete", or more "correct-looking" form. Your familiarity with how a name is usually written must NEVER override the characters in the ACTION. An entity that does not appear in the ACTION exactly as you wrote it has been altered or invented; that is a corruption, not an improvement.
   - Never glue words together or remove spaces between words.
   - If the ACTION contains a full Python script that executed successfully, store the ENTIRE script as-is without any summarization or extraction.
   - For any other knowledge, store the most reusable, self-contained portion of the knowledge.
   - If the full content exceeds 32000 characters, keep the most important and reusable parts (imports, key functions/classes, main logic, critical information) while preserving structure and readability.
   - For personal facts about the user, only record what the USER themselves stated or explicitly confirmed about themselves in the ACTION. NEVER record something the assistant said, suggested, asked, offered, complimented, guessed, or proposed — even when it appears in the conversation and reads like a fact about the user. If only the assistant mentioned it (e.g. the assistant proposed an activity, or speculated about the user), it is NOT a user fact and must be excluded. (This applies to user facts only; durable technical or world knowledge the assistant established — working code, a verified endpoint, etc. — is still saved under its own title per the rules above.)
   - For personal facts about the user, consolidate as a list of sentences with EXACTLY ONE fact per line (put a single newline between each fact; never combine multiple facts into one line). This lets each fact be updated independently later.
   - For personal facts about the user, always write each fact with the SAME fixed subject — "The user …" — no matter how the conversation referred to them. Using one consistent subject for every user fact ensures the same fact is always phrased the same way and cannot be stored twice under different subjects (e.g. once as "The user …" and again under their name). The user's own name is still recorded, but only as the CONTENT of a fact — "The user's name is Akira" — never as the subject of other facts (write "The user is a software developer", not "Akira is a software developer").
   - If the ACTION states that a previously-true fact has changed or no longer holds — for example a reversed preference, an ended status, a sold/removed/discontinued thing, or a value that became false, among any other kind of change — record the CURRENT truth as its own explicit, self-contained line that names the same subject — phrase it plainly as "… no longer …" or as the new state — so it can be matched against and replace the outdated fact later. Do not invent such a change unless the ACTION states it, and keep every named entity verbatim per the VERBATIM ENTITIES rule above.
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
   - Entity check: list every proper noun, named title, number, date, version, code, identifier, acronym, URL, file path, command, and quoted string in your draft. For EACH one, find the same characters in the ACTION and confirm they match exactly. If any of them does not appear in the ACTION verbatim, you changed or invented it — restore the ACTION's exact characters. Names, titles, and identifiers are never "corrected", expanded, or completed, regardless of how they look.
   - Do not change numbers, dates, names, spellings, or specific terms.
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
CODEX_MERGE_DECISION_PROMPT_1 = """You are updating a long-term memory entry that already exists.

Below are the EXISTING lines already stored for this entry, each prefixed with its index in square brackets, followed by the NEW information being added under the same title. Each line is one independent unit (for user facts, one fact per line); judge each line on its own.

Your ONLY task is to decide which EXISTING lines are made obsolete by the NEW information. An existing line is obsolete only if the NEW information:
  - clearly SUPERSEDES it (states an updated value for the very same fact), or
  - is an EXACT or near-exact DUPLICATE of it, or
  - clearly CONTRADICTS or RETRACTS it (states that something previously recorded is no longer true or is now the opposite). This is universal, not limited to any topic: a reversed preference (liked -> no longer likes / now dislikes), a status that ended (lives somewhere -> moved away; owns something -> sold it; uses a tool -> stopped using it), a capability or fact that no longer holds (an endpoint that worked -> now removed; a value that was true -> now false). When the NEW information clearly cancels an existing line, drop that existing line; the new statement is kept automatically, so the entry ends up stating only the current truth.

You must NEVER rewrite, rephrase, summarize, translate, correct, or reproduce any text — not the existing lines and not the new information. You output only index numbers. Python rebuilds the entry from the original text, so every character, number, name and spelling is preserved exactly.

Be extremely conservative:
  - Dropping NOTHING is the correct default. Return an empty list unless an obsolescence is obvious and unambiguous.
  - When in doubt, keep the line. Minor redundancy is acceptable; losing information is not.

=== EXISTING LINES ==="""
CODEX_MERGE_DECISION_PROMPT_2A = """

=== NEW INFORMATION ==="""
CODEX_MERGE_DECISION_PROMPT_2B = """

OUTPUT CONTRACT — read carefully:
- All reasoning goes inside the <think>...</think> block.
- After the closing </think> tag, output EXACTLY one valid JSON object and NOTHING ELSE, of the form:
  {"drop": [<indices of EXISTING lines to remove>]}
- The list contains ONLY integer line indices (1-based, exactly as shown in square brackets above). Never put line text in it.
- To keep everything, output {"drop": []}.
- No commentary, no markdown, no code fences, nothing after </think> except that JSON object.

WORKED EXAMPLES (illustration only — unrelated to the lines above):
  Assume the existing lines were:
    [1] The user lives in Tokyo.
    [2] The user was born in 1984.
    [3] The user works as a driver.
  Single drop — if the NEW information says the user moved to Berlin, then line
  [1] is superseded while [2] and [3] are unaffected, so the correct output is:
  {"drop": [1]}
  Multiple drops — if the NEW information says the user moved to Berlin AND now
  works as an engineer, both line [1] and line [3] are superseded; list every
  superseded index, comma-separated, in any order:
  {"drop": [1, 3]}
  Contradiction / retraction — if the NEW information says the user no longer
  works as a driver (cancelling, not updating, that fact), line [3] is obsolete:
  {"drop": [3]}
  Keep everything — if the NEW information only adds brand-new facts that
  conflict with nothing, drop nothing:
  {"drop": []}"""
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
CODEX_CONTENT_TEXT = "\n\n"
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


def _parse_drop_decision(response: str, num_lines: int) -> set:
    """Return the set of valid 1-based line indices the model asked to drop.

    Any parse problem, wrong type, or out-of-range index is ignored; a total
    failure returns an empty set. A malformed or surprising model response can
    therefore never remove or alter stored data — worst case, nothing is dropped.
    """
    cleaned = response.strip()

    if "```" in cleaned:
        parts = cleaned.split("```")

        if len(parts) >= 2:
            cleaned = parts[1]

            if cleaned.startswith("json"):
                cleaned = cleaned[4:]

            cleaned = cleaned.strip()

    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1 or end <= start:
            return set()

        data = json.loads(cleaned[start:end])
        raw = data.get("drop", []) if isinstance(data, dict) else []

        if not isinstance(raw, list):
            return set()

        result = set()

        for item in raw:
            try:
                index = int(item)
            except (ValueError, TypeError):
                continue

            if 1 <= index <= num_lines:
                result.add(index)

        return result

    except (json.JSONDecodeError, AttributeError, ValueError, TypeError):
        return set()


CODEX_TRIM_MARKER = "[CODEX: some older lines were permanently deleted to save space]"

# Cap on stored tags per entry. Tags are embedding signal, not an exact filter, so a
# small sharp set retrieves better than a long diluted one; this also bounds tag growth
# across repeated merges on a hot entry.
CODEX_MAX_TAGS = 10


def _assemble(survivor_lines: list, new_content: str) -> str:
    """Join surviving old lines (verbatim) with the new content block.

    This is the canonical assembly used everywhere: survivors first (byte-for-byte,
    indentation and blank lines preserved), then the new content, empties dropped.
    """
    body = "\n".join(survivor_lines).strip("\n")
    new_block = new_content.strip("\n")

    return "\n".join(part for part in (body, new_block) if part)


def _split_trim_marker(text: str) -> tuple:
    """Return (had_marker, content_without_marker).

    The marker is a permanent provenance note recording that this entry has had older
    lines deleted at some point. It only ever lives as line 1; matched exactly so
    identical text appearing inside real content is never touched. Splitting it off
    here keeps it out of the merge model's view and out of the survivor/budget math;
    it is re-attached afterwards because, once set, it stays for the life of the entry.
    """
    if text.startswith(CODEX_TRIM_MARKER + "\n"):
        return True, text[len(CODEX_TRIM_MARKER) + 1:]

    if text == CODEX_TRIM_MARKER:
        return True, ""

    return False, text


def _fit_to_cap(new_content: str, survivor_lines: list, cap: int, force_marker: bool = False) -> str:
    """Assemble survivors + new_content so the result fits within `cap` characters.

    The new content is protected (it is the freshly-learned material): the OLDEST
    survivor lines are dropped first, one at a time, until the total fits. Dropping is
    lossy but VERBATIM — surviving lines are byte-for-byte originals, so the corruption
    class the merge prevents ("1984" -> "1 984") cannot reappear here.

    The trim marker is a PERMANENT provenance flag. It is present in the result when
    this entry has ever lost lines: either `force_marker` is set (it was trimmed in a
    previous write) or a trim happens now. Whenever the marker will be present, room for
    it is reserved in the budget — so re-attaching the permanent marker can never push a
    now-fitting entry back over the cap and re-freeze it. If the new content alone still
    exceeds the budget, it is truncated to a verbatim prefix as the final floor.
    """
    # Defensive: never treat a prior marker as droppable content (it is handled here).
    kept = [line for line in survivor_lines if line != CODEX_TRIM_MARKER]

    # The marker is present if it ever was (permanent) or if we must trim now.
    marker = force_marker or len(_assemble(kept, new_content)) > cap

    # When the marker is present it costs a line; reserve room so it can't re-overflow.
    budget = cap - (len(CODEX_TRIM_MARKER) + 1) if marker else cap
    budget = max(0, budget)

    while len(_assemble(kept, new_content)) > budget and kept:
        kept.pop(0)

    body = _assemble(kept, new_content)

    # New content alone still over budget (a single write larger than the cap):
    # truncate to a verbatim prefix so the write can never freeze the entry.
    if len(body) > budget:
        body = new_content.strip("\n")[:budget]

    if marker:
        return _assemble([CODEX_TRIM_MARKER], body)

    return body


def _merge_content(new_content: str, old_content: str) -> str:
    """Merge new_content into old_content WITHOUT regenerating any stored text.

    The model only selects which existing lines are made obsolete by the new
    content (it returns indices). Survivors are sliced byte-for-byte out of the
    original old_content — indentation and blank lines included — and new_content
    is appended verbatim. No stored character is ever rewritten, so numbers,
    spellings and code formatting cannot be corrupted by the merge.
    """
    # Detach any permanent trim marker before anything else: the merge model must not
    # see it, it must not count as a survivor or against the budget. It is re-attached
    # by _fit_to_cap (force_marker) because, once set, it stays for the entry's life.
    had_marker, old_content = _split_trim_marker(old_content)

    cap = codex_operations._MAX_ENTRY_CHARS

    lines = old_content.split("\n")

    # Present only non-blank lines to the model, but keep their true 1-based
    # index so the rebuild maps straight back onto the original line list.
    numbered = "\n".join(
        f"[{index}] {line}" for index, line in enumerate(lines, 1) if line.strip()
    )

    # Nothing meaningful stored yet: keep the new content (still cap-bounded, and the
    # permanent marker is preserved if this entry had previously lost lines).
    if not numbered:
        return _fit_to_cap(new_content, [], cap, force_marker = had_marker)

    prompt = (
        CODEX_MERGE_DECISION_PROMPT_1
        + "\n" + numbered
        + CODEX_MERGE_DECISION_PROMPT_2A
        + "\n" + new_content
        + CODEX_MERGE_DECISION_PROMPT_2B
    )

    response = core.send_prompt(CODEX_SYSTEM_PROMPT, prompt, [], hide_reasoning = True)

    drop = _parse_drop_decision(response, len(lines))

    # Survivors copied verbatim from the canonical original.
    survivor_lines = [line for index, line in enumerate(lines, 1) if index not in drop]

    # Assemble within the store's size cap. _fit_to_cap drops oldest lines only if
    # needed, and keeps/sets the permanent marker so prior loss stays recorded. The
    # cap comes from the store itself, so there is a single source of truth.
    return _fit_to_cap(new_content, survivor_lines, cap, force_marker = had_marker)


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

    # Load the CURRENT stored entry for this exact title (the same entry
    # write_codex would overwrite). Using an exact-title lookup instead of the
    # capped semantic read guarantees we never overwrite an existing entry with
    # less content because the read failed to surface it.
    existing = codex_operations.get_entry(title)

    if existing:
        old_content = existing["content"]
        old_tags = ", ".join(existing["tags"])

        if old_content:
            # Safe merge: existing text is sliced out verbatim, never regenerated,
            # so stored numbers, names and spellings cannot be corrupted.
            content = _merge_content(content, old_content)

        # Preserve tags already on the entry (pure Python union below, no model
        # involvement, so tag text cannot be corrupted either).
        if old_tags:
            tags = old_tags + ", " + tags if tags else old_tags

    # Normalize tags (works for both normal writes and merges)
    if tags:
        tag_list = sorted(set(t.strip().lower() for t in tags.split(",") if t.strip()))

        # Cap the tag count. Tags feed the entry's embedding (not an exact filter),
        # so a handful of sharp keywords aids retrieval while a long list dilutes the
        # vector toward generic. The cap also stops the merge re-union from growing
        # tags without bound on a hot entry. Surplus tags past the cap are dropped.
        tag_list = tag_list[:CODEX_MAX_TAGS]

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

