import core
import plugin

NERV_SQUAD_TEXT = "\n\n----- NERV Squad -----\n"
ISSUE_ORDERS_PROMPT_1 = """\n\nAnalyze the user's prompt provided in the MISSION section.

Describe all tasks at a high level, focusing on goals and outcomes without specifying methods, tools, or actions like browsing, coding, or running programs—let the agents determine how to achieve them.

First, compose a mission summary.

Then, structure the mission into three independent tasks by assigning each to one of your agents (scaling the detail level to the mission's complexity and describing the task in third person).

Use the DATA section only if it provides useful information for the MISSION.

AGENTS:\n\n"""
ISSUE_ORDERS_PROMPT_2 = "\n\nThe list of agents above shows the order of assignment: first task goes to the first agent, second task to the second agent, and third task to the third agent."
SQUAD_ORDERS_TEXT = "----- Squad orders -----\n\n"
SQUAD_RESPONSE_TEXT = "\n\n----- Squad response -----\n\n"
AGENT_RESPONSE_TEXT_1 = "\n\n----- "
AGENT_RESPONSE_TEXT_2 = "'s response -----\n\n"
EVALUATE_TASK_PROMPT_1 = "\n\n----- Evaluation -----\n\nBased on all the above, has "
EVALUATE_TASK_PROMPT_2 = " fully accomplished their assigned orders for this stage? For tasks involving tools (e.g., browsing web pages or executing Python code), accept explanations that claim to have performed the action (e.g., 'I browsed the web page', 'I executed the Python code'), even if no actual function call or tool output is evident, as long as a summary, result, or relevant details are provided. Respond ONLY with YES or NO."
ISSUE_NEW_ORDERS_PROMPT_1 = "\n\n----- Action -----\n\nProvide new, detailed instructions for "
ISSUE_NEW_ORDERS_PROMPT_2 = ". These instructions should clearly state what is missing or needs correction. Crucially, instruct the agent to provide a new, complete, and self-contained response that incorporates your feedback and comprehensively addresses all aspects of their original task. Address the agent directly by their name using the second person, according to your personality."
GET_ORDERS_PROMPT_1 = "\n\n----- Action -----\n\nNow, based on this plan, address ONLY "
GET_ORDERS_PROMPT_2 = " directly by their name using the second person, according to your personality. Remind them to focus exclusively on their assigned task. If this is not the last task, remind them not to solve or expand on subsequent tasks."
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

    def __init__(self, name, primeDirectives):
        self.name = name
        self.primeDirectives = primeDirectives
        self.context = []


    def executeOrders(self, squad_orders, squad_response = ""):
        if self.name == CAPTAIN_NAME:
            return EXECUTE_ORDERS_ERROR_TEXT

        orders_completed = False
        
        # Use a copy of the captain's context
        captain_context = captain.context[:]

        # Get orders from the captain
        printAgentTag(captain)
        prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + GET_ORDERS_PROMPT_1 + self.name + GET_ORDERS_PROMPT_2
        orders = core.send_prompt(captain.primeDirectives, prompt, captain_context)
        plugin.printMagiText("\n" + orders)

        while not orders_completed:
            printAgentTag(self)

            # Remove extended reasoning
            orders = core.remove_reasoning(orders)

            # Add squad orders, squad response and captain's tag
            orders = squad_orders + "\n\n" + squad_response + "\n\n" + captain.tag() + orders

            # Execute orders
            response = plugin.runAction(self.primeDirectives, orders, self.context)

            # Get feedback from the captain
            prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + AGENT_RESPONSE_TEXT_1 + self.name + AGENT_RESPONSE_TEXT_2 + response + EVALUATE_TASK_PROMPT_1 + self.name + EVALUATE_TASK_PROMPT_2

            orders_completed = core.binary_question(captain.primeDirectives, prompt, captain_context)

            if not orders_completed:
               printAgentTag(captain)
               prompt = SQUAD_ORDERS_TEXT + squad_orders + SQUAD_RESPONSE_TEXT + squad_response + AGENT_RESPONSE_TEXT_1 + self.name + AGENT_RESPONSE_TEXT_2 + response + ISSUE_NEW_ORDERS_PROMPT_1 + self.name + ISSUE_NEW_ORDERS_PROMPT_2
               orders = core.send_prompt(captain.primeDirectives, prompt, captain_context)
               plugin.printMagiText("\n" + orders)

        # Add agent tag
        response = self.tag() + response

        return response


    def issueOrders(self, mission):
        if self.name != CAPTAIN_NAME:
            return ISSUE_ORDERS_ERROR_TEXT

        printAgentTag(self)

        prompt = mission + ISSUE_ORDERS_PROMPT_1 + SOLDIER_1_NAME + "\n" + SOLDIER_2_NAME + "\n" + SOLDIER_3_NAME + ISSUE_ORDERS_PROMPT_2
        response = core.send_prompt(self.primeDirectives, prompt, self.context)

        plugin.printMagiText("\n" + response)

        # Remove extended reasoning
        response = core.remove_reasoning(response)

        return response


    def tag(self):
        return "[" + self.name + "] "


    def display(self):
        plugin.printSystemText("Name: " + self.name + "\nPrime Directives: " + self.primeDirectives + "\n")


def displayNervSquad():
    plugin.printSystemText(NERV_SQUAD_TEXT)

    captain.display()
    
    for soldier in soldiers:
        soldier.display()


def runSquadOrders(squad_orders):
    squad_response = ""

    for soldier in soldiers:
        response = soldier.executeOrders(squad_orders, squad_response)
        squad_response += "\n\n" + response

    return squad_response.strip()


def printAgentTag(agent):
    plugin.printSystemText("\n[AGENT] " + agent.name)


# INITIALIZE AGENTS
CAPTAIN_NAME = core.config.get(CAPTAIN_NAME_KEY, '')
CAPTAIN_PRIME_DIRECTIVES = core.config.get(CAPTAIN_PRIME_DIRECTIVES_KEY, '')
SOLDIER_1_NAME = core.config.get(SOLDIER_1_NAME_KEY, '')
SOLDIER_1_PRIME_DIRECTIVES = core.config.get(SOLDIER_1_PRIME_DIRECTIVES_KEY, '')
SOLDIER_2_NAME = core.config.get(SOLDIER_2_NAME_KEY, '')
SOLDIER_2_PRIME_DIRECTIVES = core.config.get(SOLDIER_2_PRIME_DIRECTIVES_KEY, '')
SOLDIER_3_NAME = core.config.get(SOLDIER_3_NAME_KEY, '')
SOLDIER_3_PRIME_DIRECTIVES = core.config.get(SOLDIER_3_PRIME_DIRECTIVES_KEY, '')

captain = Agent(CAPTAIN_NAME, CAPTAIN_PRIME_DIRECTIVES)
soldiers = []
soldiers.append(Agent(SOLDIER_1_NAME, SOLDIER_1_PRIME_DIRECTIVES))
soldiers.append(Agent(SOLDIER_2_NAME, SOLDIER_2_PRIME_DIRECTIVES))
soldiers.append(Agent(SOLDIER_3_NAME, SOLDIER_3_PRIME_DIRECTIVES))


