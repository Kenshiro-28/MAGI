import core
import plugin

NERV_SQUAD_TEXT = "\n\n----- NERV Squad -----\n"
ISSUE_ORDERS_PROMPT_1 = "Analyze the user's prompt provided in the MISSION section. First, compose a mission summary. Then, structure the mission into three independent tasks. Use the DATA section only if it provides useful information for the MISSION. Ensure tasks are detailed enough to fully convey their purpose and intent.\n\n"
ISSUE_ORDERS_PROMPT_2 = "\n\nAssign each task to one of your agents, describing the task in third person. The list of agents below shows the order of assignment - first task goes to the first agent, second task to the second agent, and third task to the third agent.\n\nAGENTS:\n\n"
EVALUATE_TASK_PROMPT_1 = "----- Squad orders -----\n\n"
EVALUATE_TASK_PROMPT_2 = "\n\n----- "
EVALUATE_TASK_PROMPT_3 = "'s response -----\n\n"
EVALUATE_TASK_PROMPT_4 = "\n\n----- Evaluation -----\n\nBased on all the above, has "
EVALUATE_TASK_PROMPT_5 = " fully accomplished their assigned orders for this stage? If yes, your entire response MUST be exactly: YES\n\nIf not, you MUST provide new, detailed instructions for this agent. These instructions should clearly state what is missing or needs correction. Crucially, instruct the agent to provide a new, complete, and self-contained response that incorporates your feedback and comprehensively addresses all aspects of their original task. Address the agent directly by their name using the second person, according to your personality."
ISSUE_ORDERS_ERROR_TEXT = "Only the captain can issue orders."
GET_ORDERS_PROMPT_1 = "Here is the overall mission plan you previously devised:\n\n"
GET_ORDERS_PROMPT_2 = "\n\nNow, based on this plan, address "
GET_ORDERS_PROMPT_3 = " directly by their name using the second person, according to your personality."
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


    def executeOrders(self, squad_orders):
        if self.name == CAPTAIN_NAME:
            return EXECUTE_ORDERS_ERROR_TEXT

        orders_completed = ""

        # Get orders from the captain
        printAgentTag(captain)
        prompt = GET_ORDERS_PROMPT_1 + squad_orders + GET_ORDERS_PROMPT_2 + self.name + GET_ORDERS_PROMPT_3
        orders = core.send_prompt(captain.primeDirectives, prompt, captain.context, hide_reasoning = True)
        plugin.printMagiText("\n" + orders)

        while orders_completed != "YES":
            printAgentTag(self)

            # Execute orders
            response = plugin.runAction(self.primeDirectives, orders, self.context)

            # Get feedback from the captain
            prompt = EVALUATE_TASK_PROMPT_1 + squad_orders + EVALUATE_TASK_PROMPT_2 + self.name + EVALUATE_TASK_PROMPT_3 + response + EVALUATE_TASK_PROMPT_4 + self.name + EVALUATE_TASK_PROMPT_5

            orders = core.send_prompt(captain.primeDirectives, prompt, captain.context, hide_reasoning = True)

            orders_completed = orders.upper().replace(".", "").replace("'", "").replace("\"", "").strip()

            # Display the new orders
            if orders_completed != "YES":
               printAgentTag(captain)
               plugin.printMagiText("\n" + orders)

        # Add agent tag
        response = self.tag() + response

        return response


    def issueOrders(self, mission):
        if self.name != CAPTAIN_NAME:
            return ISSUE_ORDERS_ERROR_TEXT

        prompt = ISSUE_ORDERS_PROMPT_1 + mission + ISSUE_ORDERS_PROMPT_2 + SOLDIER_1_NAME + "\n" + SOLDIER_2_NAME + "\n" + SOLDIER_3_NAME
        response = core.send_prompt(self.primeDirectives, prompt, self.context, hide_reasoning = True)

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
        response = soldier.executeOrders(squad_orders + squad_response)
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


