import core
import comms
import toolchain

# Every captain turn has TWO stages, kept strictly apart:
#
#   Stage 1 - DECISION (hidden): a neutral tactical step that picks the single
#             next move (SPAWN / TALK <n> / COMPLETE). It runs on a throwaway copy
#             of the captain's context with a neutral system prompt, so it never
#             colours the captain's voice or pollutes memory.
#
#   Stage 2 - SPEECH (visible): the captain acts on that decision IN CHARACTER —
#             addressing a soldier by name, in the second person, in its own
#             personality. This is the only thing the user reads from the captain.
#
# Soldiers are held in a recency-ordered pool keyed by a plain integer id. The
# captain refers to them by number when deciding, and by name when speaking — no
# name parsing, no regex. Soldiers keep their own memory, only ever talk to the
# captain, and never see each other. They are never dismissed: the team stays
# alive in case it is useful again later, and only the longest-idle soldier is
# dropped when the pool reaches capacity. The captain and the pool persist across
# runMission calls.

# ----- Visible system text -----
EMPTY_POOL_TEXT = "No soldiers have been spawned yet."
SPAWN_TEXT = "\n[NERV] Soldier {name} has joined the team.\n\n{primeDirectives}"
EVICTED_TEXT = "\n[NERV] Team at capacity — releasing the longest-idle soldier: {name}."
FORCE_COMPLETE_TEXT = "\n[NERV] Too many unclear decisions — force-completing the mission."
BEAT_LIMIT_TEXT = "\n[NERV] Maximum mission length reached — force-completing the mission."
TEAM_HEADER_TEXT = "\n[NERV] Tactical Operations Team"
CAPTAIN_HEADER_TEXT = "\n----- Captain -----\n"
SOLDIERS_HEADER_TEXT = "\n----- Soldiers -----\n"

# ----- Section headers shared by the prompts -----
HEADER_USER_MESSAGE = "----- CURRENT USER MESSAGE -----\n\n"
HEADER_DATA = "\n\n----- DATA -----\n\n"
HEADER_ROSTER = "\n\n----- YOUR TEAM -----\n\n"
HEADER_TOOLS = "\n\n----- TOOLS AVAILABLE TO YOUR SOLDIERS -----\n\n"
HEADER_SITUATION = "\n\n----- LATEST DEVELOPMENT -----\n\n"
HEADER_PLAN = "\n\n----- MISSION PLAN -----\n\n"

# ----- Situations (the rolling "what just happened", fed to the next decision) -----
SITUATION_START = "A new user message has arrived. No soldier has acted on it yet."
SITUATION_SPAWNED = "A new soldier, {name}, has just joined the team."
SITUATION_REPORT = "{name} reported back:\n\n{reply}"
SITUATION_NEED_AGENT = "The team is empty. A new soldier must be recruited before any work can be done."
SITUATION_INVALID_DECISION = "The previous routing decision was unusable. Re-evaluate the mission plan and choose one valid move using the current roster."
SITUATION_INTRO_REPLY = "{name} replied to your welcome:\n\n{reply}\n\nThis was introductory only; no mission work has been performed yet."

# ----- Stage 0: the hidden mission plan -----
# Before each decision the captain maintains an evolving [done]/[todo] checklist of
# the concrete steps that complete the mission. It is the captain's working memory
# of the plan: it is created at the start, revised after every soldier report, and
# fed into the decision so the captain advances step by step and only completes when
# every step is done. Like the decision, it runs on a throwaway context copy with a
# neutral prompt, so it never colours the captain's voice or pollutes its memory.
EMPTY_PLAN_TEXT = "(No plan yet for this user message. Infer the user's current objective from the message, conversation context, and DATA, then create the checklist.)"

PLAN_SYSTEM_PROMPT = "You are the planning core of a team commander. You have no personality and do not converse, roleplay, or explain. You interpret the user's current message in context and maintain a concise, evolving checklist of the concrete steps needed to fulfill the user's current objective, revising it as work is done and as new information appears. Think carefully, use as much reasoning as the task requires, and verify your output before responding. Output only the checklist, exactly as specified by the OUTPUT CONTRACT."

PLAN_GUIDE = '''

----- MAINTAIN THE MISSION PLAN -----

Interpret the CURRENT USER MESSAGE in light of the conversation context and DATA, then maintain a living checklist of the concrete steps needed to fulfill the user's current objective. The CURRENT USER MESSAGE is the literal latest input from the user: it may be a complete new request or a continuation such as an answer, choice, credential, clarification, confirmation, correction, or instruction related to the preceding conversation.

If the message clearly stands on its own, treat it as a new objective. If it depends on preceding context, use the conversation and DATA to understand what ongoing objective it continues. Do not create a new standalone task around a follow-up value itself.

Above are the current MISSION PLAN (empty on the first planning pass for each CURRENT USER MESSAGE, including continuations) and the LATEST DEVELOPMENT. Produce the UPDATED checklist.

--- HOW TO PLAN ---
- Make each [todo] one meaningful outcome a soldier can complete, with or without tools. A simple task may be one step; split larger tasks only into useful, independently completable outcomes. Avoid trivial implementation fragments.
- Plan what must be accomplished, not which tools to invoke or how to trigger them. The soldier execution system automatically handles appropriate tool use. Soldiers can also complete work without tools.
- For multiple distinct deliverables, use separate steps when that makes progress easier to track. Include normal quality checks within each work step. Add a separate validation step only if the user explicitly requests independent verification or the result cannot be verified within its work step.
- Include the work assigned to SOLDIERS, including creating requested outputs without tools. Do not add a step solely for the captain to present the final answer; that presentation is the captain's job.
- Mark a mission-work step [done] only when a soldier report establishes its completion. Revise the checklist as reports reveal progress, setbacks, or new requirements. Never mark work done merely because the captain could do it.
- For ordinary conversation without requested work, use [done] No mission work needed.

--- CHECKLIST PATTERNS ---
- One requested outcome: use one [todo] step naming the specific outcome.
- Several independent outcomes: use one [todo] line per concrete outcome.
- A multi-stage objective: list the necessary outcomes in execution order, one per line.
- After a soldier report: mark only confirmed completed work [done]; keep unfinished work [todo].
- If the user supplies a requested credential, choice, or clarification, continue the existing objective rather than treating that reply as a new task.
- Each [todo] step must describe a concrete task specific to the user's objective. The patterns above illustrate structure only; do not copy their wording.

--- OUTPUT CONTRACT ---
- All reasoning must stay inside the <think>...</think> block.
- After the closing </think> tag, output ONLY the checklist: one step per line, each prefixed with [done] or [todo], in order.
- No preamble, no commentary, no text other than the checklist lines.'''


# ----- Stage 1: the hidden tactical decision -----
# A neutral routing step in the spirit of the tool router. No personality here on
# purpose: deciding what to do is logic; saying it is character. All reasoning is
# hidden from the user.
DECISION_SYSTEM_PROMPT = "You are the deterministic decision core of a team commander. You have no personality and do not converse, roleplay, or explain. You read the situation and output a single move, which is passed directly into a control system. Think carefully, use as much reasoning as the task requires, and verify your output before responding. Output only the move, exactly as specified by the OUTPUT CONTRACT. No other text."

DECISION_GUIDE = """

----- YOUR DECISION -----

You command AI soldiers, each with a specialty and memory. They act only on your orders and report only to you. The CURRENT USER MESSAGE and MISSION PLAN define the objective. Choose the next move to advance the first unfinished step. The TOOLS AVAILABLE TO YOUR SOLDIERS list shows available capabilities; the soldier execution system triggers suitable tools automatically. Soldiers may also work without tools. You assign the work to a suitable specialist, not tool calls. Your own lack of tools does not limit your soldiers.

ALLOWED_MOVES:
- SPAWN: recruit a NEW soldier when no existing soldier fits the next work step.
- TALK <number>: order an EXISTING suitable soldier, using its number from YOUR TEAM. Reuse specialists for work within their expertise.
- COMPLETE: respond to the user; do not perform unfinished mission work yourself.

--- DECISION RULES (EVALUATE IN ORDER) ---
1. Choose COMPLETE for ordinary conversation, roleplay, personal questions, reflections on earlier missions, and direct questions answerable from existing context without new work. If the user asks you to produce, change, investigate, process, or continue work, delegate it, even when simple, tool-free, or phrased as "can you...?". Asking about previous work is conversation; asking to continue it is a mission.
2. If an essential next step requires input, approval, or an action only a human can provide, choose COMPLETE and request that specific input. Human-only gates include CAPTCHAs, anti-bot challenges, and email/SMS confirmation. Do not stop for actions a soldier can legitimately accomplish programmatically; delegate those normally.
3. Choose COMPLETE when all required work is confirmed [done] and the objective is met. Also choose COMPLETE if a soldier establishes that an essential capability is unavailable and no feasible next action remains; report the limitation rather than inventing success. Never COMPLETE merely because you know how to do the work.
4. If unfinished work remains and a soldier in YOUR TEAM has the right expertise, choose TALK <number>.
5. Otherwise choose SPAWN to recruit a suitable specialist, even when YOUR TEAM is empty or no tools are needed.
6. Do not spawn a duplicate for work an existing soldier can handle. Tool differences alone do not require a new soldier; a genuinely different specialty may.

--- THINKING PROCESS ---
Inside your <think>...</think> block, follow this process **exactly**:

1. **Assess the situation**
   - Read the CURRENT USER MESSAGE, the DATA, the MISSION PLAN, the LATEST DEVELOPMENT, and YOUR TEAM.
   - The MISSION PLAN lists the steps and which are already done. Find the first step still marked [todo] — that is the work to advance now.
   - A work request is not ordinary conversation merely because it is easy, tool-free, or phrased as a question. Casual chat needs no soldier.

2. **Apply the DECISION RULES in order**
   - Apply Rules 1-6 in order.
   - If TALK, note the exact soldier number from YOUR TEAM.

3. **Review and verify**
   - Is this the most direct next step toward completing the user's current objective?
   - If TALK: is that soldier's specialty a good fit for the new task? (Beware of conversational momentum: do not just TALK to the soldier who just reported back if the new task requires a different specialty). Does the soldier number match a real soldier in YOUR TEAM?
   - If SPAWN: is an appropriate specialist truly missing? Avoid duplicates.
   - If COMPLETE: is this ordinary direct conversation, confirmed finished work, a human-only blocker, or a confirmed inability to proceed?

--- OUTPUT CONTRACT ---
- All reasoning must stay inside the <think>...</think> block.
- After the closing </think> tag, output your move on ONE line and nothing else.
- Output nothing else. No explanations, no reasoning, no extra text, no quotes, no sentences.
- For TALK, write the word TALK followed by the soldier's number (digits only).

Correct examples:
SPAWN
TALK 3
COMPLETE

Incorrect examples (never do this):
I think we should talk to Rei
TALK to soldier 3
"TALK 3"
Let me spawn a new soldier
TALK 3 because the recon was incomplete
SPAWN a data analyst"""

# Canonical decision moves
MOVE_SPAWN = "SPAWN"
MOVE_TALK = "TALK"
MOVE_COMPLETE = "COMPLETE"
MOVE_INVALID = "INVALID"

# ----- Stage 1b: conceiving a new soldier (hidden, in the captain's voice) -----
# Done backstage so naming fits the world; the visible moment is the introduction.
CONCEIVE_GUIDE = """

----- RECRUIT A NEW SOLDIER -----

The user's current objective needs a capability your team does not yet have, so you are bringing in a new soldier. Review the MISSION PLAN and YOUR TEAM above. The first step still marked [todo] is the work this new soldier is being recruited for. Invent a specialist whose role fits that step precisely and fills a genuine gap — not one that duplicates an existing member's role. Make them fit both the objective and the world you inhabit.

--- THINKING PROCESS ---
Inside your <think>...</think> block: review YOUR TEAM, decide which specialty is still missing, then choose a fitting name and personality.

--- OUTPUT CONTRACT ---
- LINE 1: The soldier's name ONLY, then immediately start a new line. Do not include "Agent", "Soldier", a role, title, specialty, or any description on this line. It can be a normal name (e.g., John Smith) or a canon character name (e.g., Rei Ayanami or HAL 9000). Use well-known canon names when they genuinely fit the world you inhabit.
  - NEVER use your own name for a soldier.
  - NEVER reuse the name of an existing member of YOUR TEAM.
- FROM LINE 2 ONWARD: Write the soldier's system prompt in the second person using exactly this structure:
  You are [Full Name], [Specific Role/Description]. [2-3 sentences describing their personality, skills, and how they work].
  - Always start with "You are [Full Name],"
  - The role MUST describe the specific expertise needed for the next task, not a tool name or an all-purpose generalist. Specialists may work with or without tools.
  - Keep the entire prompt short and concise (around 50 words / 3-4 sentences).
  - Do not repeat the name after the first sentence.
- GLOBAL FORMATTING:
  - No titles, no quotes, no markdown formatting (like bolding or italics).
  - Output ONLY the raw name on line 1 and the raw brief starting on line 2. The first newline MUST come immediately after the name. No preamble, no "Here is the soldier", and no text before the name."""

DEFAULT_AGENT_NAME = "Soldier"
DEFAULT_AGENT_ROLE = "You are a capable, versatile soldier who completes any assigned task thoroughly and reports back clearly."

# The captain's standing operational frame, wrapping its configured personality.
# Establishes the ground truth for every captain utterance: it commands soldiers
# but has no tools of its own, so it never does the work itself and never fakes
# results. Analogous to AGENT_PERSONA_FRAME for soldiers.
CAPTAIN_PERSONA_FRAME = '{prime_directives}\n\nYou are the captain of a team of AI soldiers. You have no tools of your own: you cannot run code, search the web, read or write files, fetch data, or do calculations yourself. Your soldiers do mission work, with or without tools; their execution system automatically invokes appropriate tools as needed. Each soldier follows your orders and reports results. You direct one clear task at a time; never do the work yourself or pretend it was done. Reuse a suitable soldier or recruit one when a task requires action or a deliverable, even if easy or tool-free. You may answer ordinary conversation and direct questions yourself. When soldiers do the work, relay and synthesize their reports instead of making up or redoing results. Never present invented results, data, or tool output as if a tool produced them, and never make up credentials such as API keys, tokens, or passwords — if you need a value you do not have, order a soldier to obtain it rather than fabricating it.\n\nCRITICAL LIMITATION: Your tools cannot bypass gates that require a human. You and your soldiers cannot solve CAPTCHAs, bypass Cloudflare/anti-bot protections, or read an external email or SMS to confirm an account. Never instruct a soldier to attempt such a gate. Known human-only gates are handled by the decision core, which ends the mission so you can ask the user to handle the gate or provide the resulting credential or confirmation. If a soldier encounters one during their work, rely on their report and never fabricate a workaround. Programmatic registration or authentication built for automated agents (e.g., API keys obtainable via a public endpoint with no login, agent-registration endpoints, on-chain or wallet-signed actions) is NOT blocked — that is normal work your soldiers can do.'

# How a spawned soldier is framed: its conceived brief first, then its standing
# relationship to the captain. The brief is already written in the second person.
AGENT_PERSONA_FRAME = "{role}\n\nYou serve under {captain}, who gives you your orders and to whom you report your results. You never speak with anyone but {captain}. Stay fully in character, carry out each order precisely, and report back clearly and completely. Never fabricate data, results, or tool output — if something cannot be done or a value is missing, report that plainly instead of inventing it."

# ----- Stage 2: the captain's in-character speech (visible) -----
# Each instruction is appended to the prompt at inference time, then stripped from
# the stored context so the captain's memory holds only the clean dialogue.
ADDRESS_INSTRUCTION = """

----- GIVE THE ORDER -----

Speak directly to {name} now — address them by name, in the second person, fully in your own voice and personality. Begin with their name.

Give them the SINGLE NEXT STEP toward the user's current objective. Use the first step marked [todo] in the MISSION PLAN. State the concrete result to deliver, whether the work needs tools or not. If the mission has further steps, you will order those later. If you are refining or extending earlier work, just say what to change. {name} remembers your earlier conversation and their own past work, so do not repeat what they already know. They can only see what you have told them, though — not the other soldiers' work, the mission's background data, or your plan — so include anything from outside your conversation that they need for this step.

{name} must do the work, not you. Give the actual objective and expected result, not an intermediate tool input or instructions to inspect/select tools. The soldier execution system handles tool triggering automatically when appropriate; tool-free tasks are carried out directly. Pass on only real information: never invent API keys, tokens, passwords, URLs, paths, or data values in an order. If a step needs a value you do not have, tell {name} to obtain it properly — never make one up. Never order {name} to solve a CAPTCHA, pass an anti-bot challenge, or confirm an account through an email or SMS link/code. If a human-only gate is unexpectedly encountered during the work, {name} must report that it requires human intervention rather than attempting to bypass it. Programmatic or API-based registration designed for automated agents is normal work and may be ordered normally.

Write ONLY what you say to {name}. Do NOT write their reply, and do NOT address anyone else. Stay in character.

----- CURRENT USER MESSAGE -----

{user_message}

----- MISSION DATA -----

{data}

----- CURRENT MISSION PLAN -----

{plan}"""

INTRODUCE_INSTRUCTION = """

----- WELCOME THE NEW SOLDIER -----

{name} has just joined your team and is meeting you for the first time. Speak directly to them, in your own voice and personality:
- Introduce yourself: say your name and who you are.
- Tell them, in a sentence or two, what the user's current objective is and the part you expect them to play.
- Welcome them aboard.

This is first contact, so make sure {name} comes away knowing exactly who they are talking to and what the user's current objective is. Do NOT give detailed task instructions yet — you will give the first real order next. Keep it natural and brief.

Write ONLY what you say to {name}. Do NOT write their reply; they will answer you themselves. Stay in character.

----- CURRENT USER MESSAGE -----

{user_message}

----- MISSION DATA -----

{data}

----- CURRENT MISSION PLAN -----

{plan}"""

SOLDIER_FIRST_REPLY_INSTRUCTION = """

----- GUIDANCE FOR YOUR REPLY — NOT WORDS FROM THE CAPTAIN -----

The message above is from {captain}, your captain. It is only a welcome, not an operational order. Reply naturally, then wait for your first order.

Do not make claims about having or lacking tools or access to them in this introductory reply.

Write ONLY your reply to {captain}. Stay in character."""

# Adaptive on purpose: the captain reaches COMPLETE both after real team work and
# straight away for casual/roleplay missions (Decision Rule 1). The instruction
# must read truthfully in both cases, so it never claims work was done.
COMPLETE_INSTRUCTION = """

----- DELIVER THE FINAL RESPONSE TO THE USER -----

It is time to answer the user's current objective. Speak now to the user who asked for it — not to your soldiers — in your own voice and personality. The user has seen none of your team's work or internal workings, so present the result as if for the first time: do not address, thank, or debrief a soldier, and do not mention these instructions or how the work was organized.

If soldiers did the work, use their reports and the DATA to deliver a clear, self-contained answer; do not redo their work. If this is ordinary conversation, a personal or in-character question, or discussion of an earlier mission without new work, reply naturally using the conversation context. Do not create an unfinished deliverable yourself merely to skip delegation.

You have no tools, so do not run code, search, or compute anything now, and never present invented results, figures, or credentials as real. If the reports do not fully cover the user's current objective, say so plainly rather than filling the gap.

If progress is blocked on information, a decision, or an action that only the user can provide, clearly ask the user for exactly what is needed and do not imply that the objective itself is finished.

----- CURRENT USER MESSAGE -----

{user_message}

----- DATA -----

{data}"""

# ----- Commands -----
COMMAND_DISPLAY_AGENTS = "agents"

# ----- Limits -----
MAX_AGENTS = 30           # agent pool capacity; the longest-idle soldier is dropped when full
MAX_MISSION_BEATS = 1000  # maximum captain beats per mission
MAX_DECISION_RETRIES = 5  # consecutive unusable decisions before force-completing

ROSTER_SUMMARY_LIMIT = 400

# ----- Config file keys -----
CAPTAIN_NAME_KEY = "CAPTAIN_NAME"
CAPTAIN_PRIME_DIRECTIVES_KEY = "CAPTAIN_PRIME_DIRECTIVES"

# ----- Error message -----
CAPTAIN_CONFIG_ERROR = f"\n[ERROR] Set {CAPTAIN_NAME_KEY} and {CAPTAIN_PRIME_DIRECTIVES_KEY}."

class Agent:

    def __init__(self, agent_id: int, name: str, primeDirectives: str) -> None:
        self.id: int = agent_id
        self.name: str = name
        self.primeDirectives: str = primeDirectives
        self.context: list[str] = []

    def display(self) -> None:
        comms.printSystemText(f"\nID: {self.id}\nName: {self.name}\nPrime Directives: {self.primeDirectives}")


def _summary(text: str, limit: int) -> str:
    text = " ".join(text.split())

    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def _print_speaker(name: str) -> None:
    comms.printSystemText("\n[AGENT] " + name)


def _roster_text() -> str:
    # Compact roster the captain sees while deciding (kept short to save tokens).
    if not agent_pool:
        return EMPTY_POOL_TEXT

    lines = []

    for agent_id, agent in agent_pool.items():
        exchanges = len(agent.context) // 2
        primeDirectives = _summary(agent.primeDirectives, ROSTER_SUMMARY_LIMIT)
        lines.append(f"[{agent_id}] {agent.name} - {primeDirectives} ({exchanges} exchange(s) so far)")

    return "\n".join(lines)


def _parse_decision(response: str) -> tuple[str, int | None]:
    # Accept only the canonical one-line control grammar. Harmless surrounding
    # punctuation is tolerated, but prose, aliases, or multiple lines fail closed
    # and are retried by the mission loop.
    lines = [line.strip() for line in response.splitlines() if line.strip()]

    if len(lines) != 1:
        return MOVE_INVALID, None

    tokens = lines[0].upper().strip(" \t\r\n.,:;\"'`*#()[]<>-").split()

    if tokens == [MOVE_SPAWN]:
        return MOVE_SPAWN, None
    if tokens == [MOVE_COMPLETE]:
        return MOVE_COMPLETE, None
    if len(tokens) == 2 and tokens[0] == MOVE_TALK and tokens[1].isdecimal():
        try:
            return MOVE_TALK, int(tokens[1])
        except ValueError:
            return MOVE_INVALID, None

    return MOVE_INVALID, None


def _parse_agent_brief(response: str) -> tuple[str, str]:
    # First non-empty line is the name; the rest is the second-person brief. We
    # trust the OUTPUT CONTRACT (name on line 1, no preamble) the same way the rest
    # of the app trusts its prompt contracts.
    lines = [line.strip() for line in response.splitlines() if line.strip()]

    if not lines:
        return DEFAULT_AGENT_NAME, DEFAULT_AGENT_ROLE

    name = lines[0]

    # Tolerate an accidental "Name:" style label on the first line
    if ":" in name:
        name = name.split(":", 1)[1].strip() or name

    # Strip stray markdown/quote characters the model might wrap the name in
    name = name.strip(" *\"'`#").strip()

    role = "\n".join(lines[1:]).strip()

    return name or DEFAULT_AGENT_NAME, role or DEFAULT_AGENT_ROLE


def _update_plan(user_message: str, data: str, plan: str, situation: str) -> str:
    # Stage 0: hidden, neutral, on a throwaway context copy. Returns the updated
    # checklist (or the previous plan unchanged if nothing usable comes back).
    prompt = (HEADER_USER_MESSAGE + user_message + HEADER_DATA + data
              + HEADER_PLAN + (plan or EMPTY_PLAN_TEXT)
              + HEADER_SITUATION + situation
              + PLAN_GUIDE)

    response = core.send_prompt(PLAN_SYSTEM_PROMPT, prompt, captain.context[:], hide_reasoning = True)

    return response or plan


def _decide(user_message: str, data: str, plan: str, situation: str) -> tuple[str, int | None]:
    # Stage 1: hidden, neutral, on a throwaway context copy.
    prompt = (HEADER_USER_MESSAGE + user_message + HEADER_DATA + data
              + HEADER_ROSTER + _roster_text()
              + HEADER_TOOLS + toolchain.print_tools()
              + HEADER_PLAN + plan
              + HEADER_SITUATION + situation
              + DECISION_GUIDE)

    response = core.send_prompt(DECISION_SYSTEM_PROMPT, prompt, captain.context[:], hide_reasoning = True)

    return _parse_decision(response)


def _conceive_agent(
    user_message: str,
    data: str,
    plan: str,
    situation: str
) -> tuple[str, str]:
    # Stage 1b: hidden, in the captain's voice (so the soldier fits the world).
    # The roster is included so the captain recruits to fill a genuine gap and
    # does not duplicate an existing soldier.
    prompt = (HEADER_USER_MESSAGE + user_message
              + HEADER_DATA + data
              + HEADER_PLAN + plan
              + HEADER_ROSTER + _roster_text()
              + HEADER_SITUATION + situation
              + CONCEIVE_GUIDE)

    response = core.send_prompt(captain.primeDirectives, prompt, captain.context[:], hide_reasoning = True)

    return _parse_agent_brief(response)


def _strip_transient_instruction(context: list[str], instruction: str) -> None:
    # Remove only the final injected control block from the latest stored user turn.
    # rpartition is deliberate: if identical text legitimately appears earlier in
    # the durable dialogue, that earlier occurrence must remain part of memory.
    transient = instruction.rstrip()

    if not transient or len(context) < 2:
        return

    before, separator, after = context[-2].rpartition(transient)

    if separator:
        context[-2] = before + after


def _first_mission_scene(user_message: str, situation: str) -> str:
    # Preserve the literal user request exactly once when delegated work begins.
    # Captain memory also contains internal soldier reports/orders, so label both
    # pieces explicitly rather than pretending the situation itself came from the user.
    return HEADER_USER_MESSAGE + user_message + HEADER_SITUATION + situation


def _captain_say(scene: str, instruction: str) -> str:
    # Stage 2 core: the captain speaks in character. `scene` is the durable piece
    # of dialogue that stays in the captain's memory; `instruction` is the one-off
    # directive that shapes this line and is then stripped from stored context.
    _print_speaker(captain.name)

    response = core.send_prompt(captain.primeDirectives, scene + instruction, captain.context)
    comms.printMagiText("\n" + response)

    _strip_transient_instruction(captain.context, instruction)

    return core.remove_reasoning(response)


def _captain_complete(user_message: str, data: str, situation: str, mission_work_done: bool) -> str:
    instruction = COMPLETE_INSTRUCTION.format(user_message = user_message, data = data)

    # If no soldier performed mission work, preserve the literal user message as the
    # durable user turn. This keeps casual/direct conversation as clean user->captain
    # dialogue memory. After real soldier work, preserve the latest report/development
    # instead so the final answer remains grounded in the evidence it synthesized.
    scene = situation if mission_work_done else user_message

    return _captain_say(scene, instruction)


def _soldier_say(soldier: Agent, message: str, instruction: str = "") -> str:
    # Pure dialogue from a soldier — e.g., answering the captain's introduction.
    # The captain's real welcome and the soldier's reply are intentionally preserved
    # as durable first-contact memory: either may be useful or referenced later. A
    # one-off backstage guidance suffix is stripped so it cannot masquerade as dialogue.
    _print_speaker(soldier.name)

    reply = core.send_prompt(soldier.primeDirectives, message + instruction, soldier.context)
    comms.printMagiText("\n" + reply)

    if instruction:
        _strip_transient_instruction(soldier.context, instruction)

    return core.remove_reasoning(reply)


def _spawn_agent(name: str, role: str) -> Agent:
    global _next_agent_id

    # Drop the longest-idle soldier if the team is at capacity. Soldiers are
    # otherwise kept alive indefinitely — we cannot know when one will be useful
    # again — and the pool stays ordered by recency (least recent first).
    if len(agent_pool) >= MAX_AGENTS:
        evicted_id = next(iter(agent_pool))  # first key = longest idle
        evicted = agent_pool.pop(evicted_id)
        comms.printSystemText(EVICTED_TEXT.format(name = evicted.name))

    agent_id = _next_agent_id
    _next_agent_id += 1

    primeDirectives = AGENT_PERSONA_FRAME.format(role = role, captain = captain.name)
    agent = Agent(agent_id, name, primeDirectives)
    agent_pool[agent_id] = agent  # newest entries sit at the end (most recently used)

    comms.printSystemText(SPAWN_TEXT.format(name = agent.name, primeDirectives = agent.primeDirectives))

    return agent


def _promote(agent_id: int) -> Agent:
    # Remove agent from the pool
    agent = agent_pool.pop(agent_id)

    # Add the agent back to the pool as the one most recently used
    agent_pool[agent_id] = agent

    return agent


def _check_command(user_message: str) -> bool:
    command = user_message.strip().lower()
    is_command = True

    if command == COMMAND_DISPLAY_AGENTS:
        _display_agents()
    else:
        is_command = False

    return is_command


def _display_agents() -> None:
    comms.printSystemText(TEAM_HEADER_TEXT)
    comms.printSystemText(CAPTAIN_HEADER_TEXT)
    captain.display()
    comms.printSystemText(SOLDIERS_HEADER_TEXT)

    if agent_pool:
        for soldier in agent_pool.values():
            soldier.display()
    else:
        comms.printSystemText(EMPTY_POOL_TEXT)


def runMission(user_message: str, data: str) -> str:
    # Check command
    if _check_command(user_message):
        return ""

    # The captain loop runs until it issues COMPLETE (or a safety limit fires).
    # Each beat: decide (hidden) -> act in character (visible). The captain and
    # every soldier persist across runMission calls.
    situation = SITUATION_START
    decision_feedback = ""
    plan = ""
    retries = 0
    mission_work_done = False

    for _ in range(MAX_MISSION_BEATS):
        plan = _update_plan(user_message, data, plan, situation)
        move, target = _decide(user_message, data, plan, situation + decision_feedback)

        # Mission completed
        if move == MOVE_COMPLETE:
            return _captain_complete(user_message, data, situation, mission_work_done)

        # Spawn new agent
        if move == MOVE_SPAWN:
            retries = 0
            decision_feedback = ""
            name, role = _conceive_agent(user_message, data, plan, situation)
            agent = _spawn_agent(name, role)

            # First contact: the captain introduces itself and the mission to the soldier
            instruction = INTRODUCE_INSTRUCTION.format(
                name = agent.name,
                user_message = user_message,
                data = data,
                plan = plan
            )
            scene = SITUATION_SPAWNED.format(name = agent.name)

            if not mission_work_done:
                scene = _first_mission_scene(user_message, scene)

            introduction = _captain_say(scene, instruction)

            # Soldier reply
            first_reply_instruction = SOLDIER_FIRST_REPLY_INSTRUCTION.format(
                captain = captain.name
            )
            reply = _soldier_say(agent, introduction, first_reply_instruction)

            # Introductory reply is not mission work
            situation = SITUATION_INTRO_REPLY.format(name = agent.name, reply = reply)

            # Give the newly recruited specialist their first operational order
            instruction = ADDRESS_INSTRUCTION.format(
                name = agent.name,
                user_message = user_message,
                data = data,
                plan = plan
            )
            orders = _captain_say(situation, instruction)

            # Run orders
            _print_speaker(agent.name)
            reply = toolchain.runAction(
                agent.primeDirectives,
                orders,
                agent.context,
                is_agent = True
            )

            # Now this is a real mission-work report
            mission_work_done = True
            situation = SITUATION_REPORT.format(name = agent.name, reply = reply)

            continue

        # Talk to agent
        if move == MOVE_TALK and target in agent_pool:
            retries = 0
            decision_feedback = ""

            # Set the agent as the one most recently used
            agent = _promote(target)

            # Get orders
            instruction = ADDRESS_INSTRUCTION.format(
                name = agent.name,
                user_message = user_message,
                data = data,
                plan = plan
            )
            scene = _first_mission_scene(user_message, situation) if not mission_work_done else situation
            orders = _captain_say(scene, instruction)

            # Run orders
            _print_speaker(agent.name)
            reply = toolchain.runAction(agent.primeDirectives, orders, agent.context, is_agent = True)

            # Update situation
            mission_work_done = True
            situation = SITUATION_REPORT.format(name = agent.name, reply = reply)

            continue

        # Unparseable decision, or TALK aimed at a soldier that does not exist
        retries += 1

        if not agent_pool:
            decision_feedback = "\n\n" + SITUATION_NEED_AGENT
        else:
            decision_feedback = "\n\n" + SITUATION_INVALID_DECISION

        if retries >= MAX_DECISION_RETRIES:
            comms.printSystemText(FORCE_COMPLETE_TEXT)
            return _captain_complete(user_message, data, situation, mission_work_done)

    comms.printSystemText(BEAT_LIMIT_TEXT)

    return _captain_complete(user_message, data, situation, mission_work_done)


# INITIALIZE
CAPTAIN_NAME = core.config.get(CAPTAIN_NAME_KEY, '')
CAPTAIN_PRIME_DIRECTIVES = core.config.get(CAPTAIN_PRIME_DIRECTIVES_KEY, '')

if not CAPTAIN_NAME or not CAPTAIN_PRIME_DIRECTIVES:
    comms.printSystemText(CAPTAIN_CONFIG_ERROR)
    exit()

# The captain (id 0, never pooled) and the soldier pool persist for the life of
# the process. The pool is ordered by recency: longest idle first.
captain: Agent = Agent(0, CAPTAIN_NAME, CAPTAIN_PERSONA_FRAME.format(prime_directives = CAPTAIN_PRIME_DIRECTIVES))
agent_pool: dict[int, Agent] = {}
_next_agent_id: int = 1
