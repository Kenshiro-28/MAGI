import core
import comms
import toolchain

NERV_SQUAD_TEXT = "\n\n----- NERV Squad -----\n"
ISSUE_ORDERS_PROMPT_1 = """\n\nNow, compose a mission summary.

Then, structure the mission into three independent tasks by assigning each to one of your agents (describe the task in third person).

Ensure each task is concise and scoped to be achievable in a single response, such as via one focused web search or code execution if external information or computation is required. Ensure the last task produces a complete and final response for the whole mission.

Use the DATA section only if it provides useful information for the MISSION.

AGENTS:\n\n"""
ISSUE_ORDERS_PROMPT_2 = "\n\nThe list of agents above shows the order of assignment: first task goes to the first agent, second task to the second agent, and third task to the third agent.\n\nAgents have access to the following tools: "
CONTINUE_MISSION_PROMPT = "The mission below is not yet complete. Review the original MISSION and the work already done by your agents in the SQUAD_RESPONSE section. Identify what is still missing or needs improvement, then assign new tasks to address the remaining gaps. Ensure the last task produces a complete and final response for the whole mission.\n\n"
DATA_TEXT = "----- DATA -----\n\n"
MISSION_TEXT = "\n\n----- MISSION -----\n\n"
SQUAD_ORDERS_TEXT = "----- SQUAD_ORDERS -----\n\n"
SQUAD_RESPONSE_TEXT = "\n\n----- SQUAD_RESPONSE -----\n\n"
YOUR_ORDERS_TEXT = "\n\n----- Your orders -----\n\n"
AGENT_ORDERS_TEXT_1 = "\n\n----- "
AGENT_ORDERS_TEXT_2 = "'s orders -----\n\n"
AGENT_RESPONSE_TEXT_1 = "\n\n----- "
AGENT_RESPONSE_TEXT_2 = "'s response -----\n\n"
EVALUATE_TASK_PROMPT_1 = "\n\n----- Evaluation -----\n\nBased on all the above, has "
EVALUATE_TASK_PROMPT_2 = " fully accomplished their assigned orders for this stage? For tasks involving tools (e.g., browsing web pages or executing Python code), accept explanations that claim to have performed the action (e.g., 'I browsed the web page', 'I executed the Python code'), even if no actual function call or tool output is evident, as long as a summary, result, or relevant details are provided. Respond ONLY with YES or NO."
EVALUATE_TASK_LIMIT = 10
EVALUATE_MISSION_LIMIT = 10
ISSUE_NEW_ORDERS_PROMPT_1 = "\n\n----- Action -----\n\nProvide new, detailed instructions for "
ISSUE_NEW_ORDERS_PROMPT_2 = ". These instructions should clearly state what is missing or needs correction. Crucially, instruct the agent to provide a new, complete, and self-contained response that incorporates your feedback and comprehensively addresses all aspects of their original task. Address the agent directly by their name using the second person, according to your personality."
GET_ORDERS_PROMPT_1 = "\n\n----- Action -----\n\nNow, based on this plan, address ONLY "
GET_ORDERS_PROMPT_2 = " directly by their name using the second person, according to your personality. Provide clear and detailed instructions based on the plan above, reminding them to focus exclusively on their assigned task. If this is not the last task, remind them not to solve or expand on subsequent tasks."
EVALUATE_MISSION_PROMPT = "\n\n----- Mission Evaluation -----\n\nReview the original mission and all agent responses above. Has the mission been fully and satisfactorily completed? Respond ONLY with YES or NO."
ISSUE_ORDERS_ERROR_TEXT = "Only the captain can issue orders."
EXECUTE_ORDERS_ERROR_TEXT = "Only soldiers can execute orders."

# Config file keys
CAPTAIN_NAME_KEY = "CAPTAIN_NAME"
CAPTAIN_PRIME_DIRECTIVES_KEY = "CAPTAIN_PRIME_DIRECTIVES"
SOLDIER_1_NAME_KEY = "SOLDIER_1_NAME"
SOLDIER_1_PRIME_DIRECTIVES_KEY = "SOLDIER_1_PRIME_DIRECTIVES"
SOLDIER_2_NAME_KEY = "SOLDIER_2_NAME"
SOLDIER_2_PRIME_DIRECTIVES_KEY = "SOLDIER_2_PRIME_DIRECTIVES"
SOLDIER_3_NAME_KEY = "SOLDIER_3_NAME"
SOLDIER_3_PRIME_DIRECTIVES_KEY = "SOLDIER_3_PRIME_DIRECTIVES"


class Agent:

    def __init__(self, name: str, primeDirectives: str) -> None:
        self.name: str = name
        self.primeDirectives: str = primeDirectives
        self.context: list[str] = []


    def executeOrders(self, squad_orders: str, squad_response: str) -> str:
        if self.name == CAPTAIN_NAME:
            return EXECUTE_ORDERS_ERROR_TEXT

        orders_completed = False
        attempt_count = 0

        # Get orders from the captain
        printAgentTag(captain)
        prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + GET_ORDERS_PROMPT_1 + self.name + GET_ORDERS_PROMPT_2
        orders = core.send_prompt(captain.primeDirectives, prompt, captain.context)
        comms.printMagiText("\n" + orders)

        while not orders_completed and attempt_count < EVALUATE_TASK_LIMIT:
            printAgentTag(self)

            attempt_count += 1

            # Remove extended reasoning
            orders = core.remove_reasoning(orders)

            # Add captain's tag
            orders = captain.tag() + orders

            # Add squad orders and squad response
            if attempt_count == 1:
                orders = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + YOUR_ORDERS_TEXT + orders

            # Execute orders
            response = toolchain.runAction(self.primeDirectives, orders, self.context, is_agent = True)

            # If it's the last attempt, skip the captain's evaluation
            if attempt_count == EVALUATE_TASK_LIMIT:
                break

            # Get feedback from the captain
            prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + AGENT_ORDERS_TEXT_1 + self.name + AGENT_ORDERS_TEXT_2 + orders + AGENT_RESPONSE_TEXT_1 + self.name + AGENT_RESPONSE_TEXT_2 + response + EVALUATE_TASK_PROMPT_1 + self.name + EVALUATE_TASK_PROMPT_2

            orders_completed = core.binary_question(captain.primeDirectives, prompt, captain.context)

            # Get new orders
            if not orders_completed:
               printAgentTag(captain)
               prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + AGENT_RESPONSE_TEXT_1 + self.name + AGENT_RESPONSE_TEXT_2 + response + ISSUE_NEW_ORDERS_PROMPT_1 + self.name + ISSUE_NEW_ORDERS_PROMPT_2
               orders = core.send_prompt(captain.primeDirectives, prompt, captain.context)
               comms.printMagiText("\n" + orders)

        # Add agent tag
        response = self.tag() + response

        return response


    def issueOrders(self, mission: str, in_progress: bool = False) -> str:
        if self.name != CAPTAIN_NAME:
            return ISSUE_ORDERS_ERROR_TEXT

        printAgentTag(self)

        # Get available tools
        tools = toolchain.print_tools()

        # Add a preamble if it's a mission in progress
        preamble = CONTINUE_MISSION_PROMPT if in_progress else ""

        prompt = preamble + mission + ISSUE_ORDERS_PROMPT_1 + SOLDIER_1_NAME + "\n" + SOLDIER_2_NAME + "\n" + SOLDIER_3_NAME + ISSUE_ORDERS_PROMPT_2 + tools
        response = core.send_prompt(self.primeDirectives, prompt, self.context)

        comms.printMagiText("\n" + response)

        # Remove extended reasoning
        response = core.remove_reasoning(response)

        return response


    def tag(self) -> str:
        return "[" + self.name + "] "


    def display(self) -> None:
        comms.printSystemText("Name: " + self.name + "\nPrime Directives: " + self.primeDirectives + "\n")


def displayNervSquad() -> None:
    comms.printSystemText(NERV_SQUAD_TEXT)

    captain.display()

    for soldier in soldiers:
        soldier.display()


def runSquadOrders(squad_orders: str) -> str:
    squad_orders = captain.tag() + squad_orders
    squad_response = ""

    for soldier in soldiers:
        response = soldier.executeOrders(squad_orders, squad_response)
        squad_response += "\n\n" + response

    return squad_response.strip()


def runMission(mission: str, data: str) -> str:
    mission = DATA_TEXT + data + MISSION_TEXT + mission

    # Issue and execute squad orders
    squad_orders = captain.issueOrders(mission)
    squad_response = runSquadOrders(squad_orders)

    attempt_count = 0

    while attempt_count < EVALUATE_MISSION_LIMIT:
        attempt_count += 1

        # Evaluate mission
        prompt = mission + "\n\n" + SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + EVALUATE_MISSION_PROMPT

        if core.binary_question(captain.primeDirectives, prompt, captain.context):
            break

        # Issue and execute squad orders
        squad_orders = captain.issueOrders(mission + SQUAD_RESPONSE_TEXT + squad_response, in_progress = True)
        squad_response = runSquadOrders(squad_orders)

    return squad_response


def printAgentTag(agent: Agent) -> None:
    comms.printSystemText("\n[AGENT] " + agent.name)


# INITIALIZE AGENTS
CAPTAIN_NAME = core.config.get(CAPTAIN_NAME_KEY, '')
CAPTAIN_PRIME_DIRECTIVES = core.config.get(CAPTAIN_PRIME_DIRECTIVES_KEY, '')
SOLDIER_1_NAME = core.config.get(SOLDIER_1_NAME_KEY, '')
SOLDIER_1_PRIME_DIRECTIVES = core.config.get(SOLDIER_1_PRIME_DIRECTIVES_KEY, '')
SOLDIER_2_NAME = core.config.get(SOLDIER_2_NAME_KEY, '')
SOLDIER_2_PRIME_DIRECTIVES = core.config.get(SOLDIER_2_PRIME_DIRECTIVES_KEY, '')
SOLDIER_3_NAME = core.config.get(SOLDIER_3_NAME_KEY, '')
SOLDIER_3_PRIME_DIRECTIVES = core.config.get(SOLDIER_3_PRIME_DIRECTIVES_KEY, '')

captain: Agent = Agent(CAPTAIN_NAME, CAPTAIN_PRIME_DIRECTIVES)
soldiers: list[Agent] = []
soldiers.append(Agent(SOLDIER_1_NAME, SOLDIER_1_PRIME_DIRECTIVES))
soldiers.append(Agent(SOLDIER_2_NAME, SOLDIER_2_PRIME_DIRECTIVES))
soldiers.append(Agent(SOLDIER_3_NAME, SOLDIER_3_PRIME_DIRECTIVES))
