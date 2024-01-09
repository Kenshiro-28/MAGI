import core
import plugin

NERV_SQUAD_TEXT = "\n\n----- NERV Squad -----\n"
EXECUTE_ORDERS_PROMPT = "\nExecute only the orders specifically assigned to "
ISSUE_ORDERS_PROMPT_1 = "Give individual orders to each of your soldiers."
ISSUE_ORDERS_PROMPT_2 = "\nSOLDIERS:\n"
ISSUE_ORDERS_ERROR_TEXT = "Only the captain can issue orders."

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


	def executeOrders(self, orders, ai_mode):
		prompt = orders + EXECUTE_ORDERS_PROMPT + self.name + "."
		
		response = self.tag() + plugin.runAction(self.primeDirectives, prompt, self.context, ai_mode)
		
		return response


	def issueOrders(self, mission, ai_mode):
		printAgentTag(self, ai_mode)
	
		if self.name == CAPTAIN_NAME:
			prompt = ISSUE_ORDERS_PROMPT_1 + mission + ISSUE_ORDERS_PROMPT_2 + SOLDIER_1_NAME + "\n" + SOLDIER_2_NAME + "\n" + SOLDIER_3_NAME
			response = core.send_prompt(self.primeDirectives, prompt, self.context)
			plugin.printMagiText("\n" + response, ai_mode)
		else:
			response = ISSUE_ORDERS_ERROR_TEXT

		response = self.tag() + response

		return response
		

	def tag(self):
		return "[" + self.name + "] "


	def display(self, ai_mode):
		plugin.printSystemText("Name: " + self.name + "\nPrime Directives: " + self.primeDirectives + "\n", ai_mode)


def displayNervSquad(ai_mode):
	plugin.printSystemText(NERV_SQUAD_TEXT, ai_mode)

	captain.display(ai_mode)
	
	for soldier in soldiers:
		soldier.display(ai_mode)


def runSquadOrders(orders, ai_mode):
	team_response = ""

	for soldier in soldiers:
		printAgentTag(soldier, ai_mode)
		response = soldier.executeOrders(orders + team_response, ai_mode)
		team_response += "\n" + response

	return team_response


def printAgentTag(agent, ai_mode):
	plugin.printSystemText("\n[AGENT] " + agent.name, ai_mode)


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


