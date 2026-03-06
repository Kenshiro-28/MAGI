import json
import os
import hashlib
from datetime import datetime
import numpy as np

CODEX_FILE = "codex.json"

# --- Thresholds ---
_DUPLICATE_THRESHOLD = 0.90
_SIMILAR_THRESHOLD = 0.75
_READ_THRESHOLD = 0.32

# Returns the best matches when querying
_MAX_READ_RESULTS = 3
_MAX_ENTRY_CHARS = 8000
_MAX_TITLE_CHARS = 200

# all-mpnet-base-v2 has a 514-token limit (~1800 chars).
# Content is chunked at this size with overlap so long code snippets
# get a representative embedding instead of being silently truncated.
_CHUNK_SIZE = 1800
_CHUNK_OVERLAP = 200

# Query to list all entries.
CODEX_LIST_ALL = "[CODEX:LIST_ALL]"

# Sentinel returned by read_codex when no relevant entries are found.
# Used by callers to detect "no results" without fragile string matching.
CODEX_NO_RESULT = "[CODEX:NO_RESULT]"

_model = None


def _get_model():
    """Lazy-load the sentence transformer model (all-mpnet-base-v2)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-mpnet-base-v2")
    return _model


def _embed_single(text: str) -> list:
    """Return normalized embedding for a single text chunk."""
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def _embed(text: str) -> list:
    """
    Embed text that may exceed the model's token limit by splitting into
    overlapping chunks and averaging the resulting embeddings.
    This ensures long code snippets get a meaningful representation.
    """
    if len(text) <= _CHUNK_SIZE:
        return _embed_single(text)

    chunks = []
    start = 0
    while start < len(text):
        end = start + _CHUNK_SIZE
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += _CHUNK_SIZE - _CHUNK_OVERLAP

    embeddings = np.array([_embed_single(chunk) for chunk in chunks])

    # Average and re-normalize
    averaged = embeddings.mean(axis=0)
    norm = np.linalg.norm(averaged)
    if norm > 0:
        averaged /= norm

    return averaged.tolist()


def _cosine(a: list, b: list) -> float:
    """Cosine similarity between two normalized embedding vectors."""
    return float(np.dot(a, b))


def _entry_repr(entry: dict) -> str:
    """String representation of an entry used for embedding."""
    tags = ", ".join(entry.get("tags", []))
    content = entry.get("content", "")
    return f"{entry.get('title', '')}. Tags: {tags}. {content}"


def _generate_embedding(title: str, tags: list, content: str) -> list:
    """Generate a chunked-averaged embedding from title, tags and full content."""
    text = _entry_repr({"title": title, "tags": tags, "content": content})
    return _embed(text)


def _hash(content: str) -> str:
    """Return a short hash of the content for duplicate detection."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _validate_entry(entry: dict) -> bool:
    """Return True if the entry has the required fields."""
    return (
        isinstance(entry, dict)
        and isinstance(entry.get("title"), str)
        and isinstance(entry.get("content"), str)
        and isinstance(entry.get("tags"), list)
    )


def _load() -> list:
    """Load the codex JSON file, recovering from corruption if needed."""
    if not os.path.exists(CODEX_FILE):
        return []

    try:
        with open(CODEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError) as e:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupt_backup = f"{CODEX_FILE}.corrupt_{timestamp}"

        print(
            f"WARNING: Could not read '{CODEX_FILE}' ({e}). "
            f"Quarantining to {corrupt_backup}"
        )

        try:
            os.rename(CODEX_FILE, corrupt_backup)
        except OSError:
            pass

        return []


def _save(entries: list) -> None:
    """Atomically save the codex entries to disk."""
    temp_file = f"{CODEX_FILE}.tmp"

    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, CODEX_FILE)

    except Exception as e:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise RuntimeError(f"Failed to save Codex: {e}")


def _ensure_embedding(entry: dict) -> bool:
    """
    Add missing embedding to an entry (backward compatibility).
    Returns True if the entry was modified.
    """
    if "embedding" not in entry:
        entry["embedding"] = _generate_embedding(
            entry.get("title", ""),
            entry.get("tags", []),
            entry.get("content", "")
        )
        return True
    return False


# ─────────────────────────────────────────────
# Tool: write_codex
# ─────────────────────────────────────────────

def write_codex(title: str, content: str, tags: str) -> str:
    """
    Save or update an entry in the Codex.
    Returns a user-facing message.
    """
    if len(title) > _MAX_TITLE_CHARS:
        return (
            f"Title too long ({len(title)} chars, max {_MAX_TITLE_CHARS}). "
            "Please shorten the title."
        )

    if len(content) > _MAX_ENTRY_CHARS:
        return (
            f"Entry too long ({len(content)} chars, max {_MAX_ENTRY_CHARS}). "
            "Please summarize or trim the content before saving."
        )

    entries = _load()

    tag_list = sorted(
        {t.strip().lower() for t in tags.split(",") if t.strip()}
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    content_hash = _hash(content + "|" + ",".join(tag_list))

    # 1. Exact content duplicate (hash match)
    for entry in entries:
        if entry.get("hash") == content_hash:
            return (
                f"Identical content already stored as '{entry['title']}'. "
                "Skipped."
            )

    # 2. Exact title update
    for entry in entries:
        if not _validate_entry(entry):
            continue
        if entry.get("title", "").lower() == title.lower():
            entry["content"] = content
            entry["tags"] = tag_list
            entry["updated"] = timestamp
            entry["hash"] = content_hash
            entry["embedding"] = _generate_embedding(title, tag_list, content)

            _save(entries)
            return f"Entry updated: '{title}'"

    # 3. Semantic duplicate detection
    new_embedding = _generate_embedding(title, tag_list, content)

    best_title = ""
    best_score = 0.0
    dirty = False

    for entry in entries:
        if not _validate_entry(entry):
            continue
        if _ensure_embedding(entry):
            dirty = True

        score = _cosine(new_embedding, entry["embedding"])

        if score > best_score:
            best_score = score
            best_title = entry.get("title", "")

    if dirty:
        _save(entries)

    if best_score >= _DUPLICATE_THRESHOLD:
        return (
            f"Likely duplicate detected (similarity {best_score:.2f}). "
            f"Existing entry: '{best_title}'. "
            "Use write_codex with that exact title to update it, "
            "or use a more specific title if this entry is genuinely distinct."
        )

    # 4. Save new entry
    new_entry = {
        "title": title,
        "content": content,
        "tags": tag_list,
        "created": timestamp,
        "updated": timestamp,
        "hash": content_hash,
        "embedding": new_embedding,
    }

    entries.append(new_entry)
    _save(entries)

    suffix = ""

    if best_score >= _SIMILAR_THRESHOLD:
        suffix = (
            f" — Note: semantically related to '{best_title}' "
            f"(similarity {best_score:.2f}). Saved as distinct entry."
        )

    return f"Entry saved: '{title}' | Tags: {', '.join(tag_list)}{suffix}"


# ─────────────────────────────────────────────
# Tool: read_codex
# ─────────────────────────────────────────────

def read_codex(query: str = "") -> str:
    """
    Retrieve relevant entries from the Codex.
    If query is CODEX_LIST_ALL, lists all entry titles.
    Otherwise returns the most relevant entries (up to _MAX_READ_RESULTS),
    or CODEX_NO_RESULT if none meet the relevance threshold.
    """
    entries = _load()

    if not entries:
        return CODEX_NO_RESULT

    q = query.strip()

    if q == CODEX_LIST_ALL:
        lines = [
            f"{len(entries)} entr{'y' if len(entries) == 1 else 'ies'} stored\n"
        ]

        for i, e in enumerate(entries, 1):
            if not _validate_entry(e):
                continue
            date = e.get("updated") or e.get("created", "?")
            tags_str = ", ".join(e.get("tags", [])) or "—"
            lines.append(f"  {i:>2}. {e['title']}  [{date}]  tags: {tags_str}")

        return "\n".join(lines)

    query_embedding = _embed(q)

    dirty = False
    scored = []

    for entry in entries:
        if not _validate_entry(entry):
            continue
        if _ensure_embedding(entry):
            dirty = True

        score = _cosine(query_embedding, entry["embedding"])

        if score >= _READ_THRESHOLD:
            scored.append((score, entry))

    if dirty:
        _save(entries)

    scored.sort(key=lambda x: x[0], reverse=True)
    scored = scored[:_MAX_READ_RESULTS]

    if not scored:
        return CODEX_NO_RESULT

    lines = [
        f"{len(scored)} relevant entr{'y' if len(scored) == 1 else 'ies'} "
        f"for '{q}':\n"
    ]

    for score, entry in scored:
        date = entry.get("updated") or entry.get("created", "?")
        tags_str = ", ".join(entry.get("tags", [])) or "—"

        lines.append(
            f"--- {entry['title']}  [{date}]  tags: {tags_str}  "
            f"relevance: {score:.2f} ---"
        )
        lines.append(entry["content"])
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Tool: delete_codex
# ─────────────────────────────────────────────

def delete_codex(title: str) -> str:
    """
    Delete an entry by its exact title.
    If not found, suggests similar titles.
    """
    entries = _load()

    to_delete = None
    remaining = []

    for e in entries:
        if _validate_entry(e) and e.get("title", "").lower() == title.lower():
            to_delete = e
        else:
            remaining.append(e)

    if to_delete is None:
        hint = ""

        if entries:
            try:
                q_emb = _embed(title)
                dirty = False
                suggestions = []

                for e in entries:
                    if not _validate_entry(e):
                        continue
                    if _ensure_embedding(e):
                        dirty = True
                    suggestions.append((_cosine(q_emb, e["embedding"]), e["title"]))

                if dirty:
                    _save(entries)

                suggestions.sort(reverse=True)
                top = [t for _, t in suggestions[:3]]
                hint = f" Did you mean one of: {top}?"

            except Exception:
                pass

        return f"No entry found with title '{title}'.{hint}"

    _save(remaining)
    return f"Entry deleted: '{title}'"
