import core
import plugin

NERV_SQUAD_TEXT = "\n\n----- NERV Squad -----\n"
ISSUE_ORDERS_PROMPT_1 = "Analyze the user's prompt provided in the MISSION section. First, compose a mission summary. Then, structure the mission into three independent tasks. Use the DATA section only if it provides useful information for the MISSION. Ensure tasks are detailed enough to fully convey their purpose and intent.\n\n"
ISSUE_ORDERS_PROMPT_2 = "\n\nAssign each task to one of your agents, describing the task in third person. The list of agents below shows the order of assignment - first task goes to the first agent, second task to the second agent, and third task to the third agent.\n\nAGENTS:\n\n"
ISSUE_ORDERS_ERROR_TEXT = "Only the captain can issue orders."
GET_ORDERS_PROMPT_1 = "Tell "
GET_ORDERS_PROMPT_2 = " their orders, starting with their name."
MISSION_HEADER_TEXT = "=== MISSION CONTEXT ===\n\n"
ORDERS_HEADER_TEXT = "\n\n=== ORDERS ===\n\n"
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
        if self.name != CAPTAIN_NAME:
            aux_context = captain.context[:]
            get_orders_prompt = GET_ORDERS_PROMPT_1 + self.name + GET_ORDERS_PROMPT_2
            orders = core.send_prompt(captain.primeDirectives, get_orders_prompt, aux_context, hide_reasoning = True)

            response = plugin.runAction(self.primeDirectives, orders, self.context)
        else:
            response = EXECUTE_ORDERS_ERROR_TEXT

        # Add agent tag
        response = self.tag() + response

        return response


    def issueOrders(self, mission):
        printAgentTag(self)
    
        if self.name == CAPTAIN_NAME:
            prompt = ISSUE_ORDERS_PROMPT_1 + mission + ISSUE_ORDERS_PROMPT_2 + SOLDIER_1_NAME + "\n" + SOLDIER_2_NAME + "\n" + SOLDIER_3_NAME
            response = core.send_prompt(self.primeDirectives, prompt, self.context)
            plugin.printMagiText("\n" + response)
        else:
            response = ISSUE_ORDERS_ERROR_TEXT

        # Remove extended reasoning
        response = core.remove_reasoning(response)

        # Add agent tag
        response = self.tag() + response

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
        printAgentTag(soldier)
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


