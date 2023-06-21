from telegram import Bot
from telegram.error import Forbidden, NetworkError
import asyncio

TIMEOUT = 5
FORBIDDEN_ERROR = "[ERROR] The user has removed or blocked the Telegram bot."

class TelegramBot:

	def __init__(self, token, user):
		self.bot = Bot(token)
		self.user = user


	async def send(self, text):
		try:
			await self.getUpdateId()
			await self.bot.send_message(self.user, text)
		except NetworkError:
			await asyncio.sleep(TIMEOUT)
		except Forbidden:
			print(FORBIDDEN_ERROR)


	async def receive(self):
		messageList = []
	
		update_id = await self.getUpdateId()

		# Get the pending messages
		while update_id != None:
			try:
				next_update_id = update_id
			
				# Request updates after the last update_id
				updates = await self.bot.get_updates(offset = update_id, timeout = TIMEOUT)

				for update in updates:
					# Bot can receive updates without messages and not all messages contain text
					if update.message and update.message.text and str(update.message.from_user.id) == self.user:
						messageList.append(update.message.text + "\n")

					next_update_id = update.update_id + 1
				
				if next_update_id == update_id:
					break
				else:
					update_id = next_update_id

			except NetworkError:
				await asyncio.sleep(TIMEOUT)

			except Forbidden:
				# The user has removed or blocked the bot.
				update_id += 1

		return messageList
		

	async def getUpdateId(self):
		# Get the first pending update_id, this is so we can skip over it in case
		# we get a "Forbidden" exception.
		try:
			update_id = (await self.bot.get_updates())[0].update_id
		except IndexError:
			update_id = None
			
		return update_id			


