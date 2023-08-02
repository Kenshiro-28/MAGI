from telegram import Bot
from telegram.error import Forbidden, NetworkError
import asyncio
from io import BytesIO

TIMEOUT = 10
FORBIDDEN_ERROR = "[ERROR] The user has removed or blocked the Telegram bot."
TELEGRAM_PLUGIN_ERROR = "[ERROR] Telegram plugin exception: "
TELEGRAM_IMAGE_NAME = "image.png"
TELEGRAM_IMAGE_FORMAT = "PNG"


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
		except Exception as e:
			print(TELEGRAM_PLUGIN_ERROR + str(e))		


	async def send_image(self, image):
		try:
			bytes_io = BytesIO()
			bytes_io.name = TELEGRAM_IMAGE_NAME
			image.save(bytes_io, TELEGRAM_IMAGE_FORMAT)
			bytes_io.seek(0)

			await self.getUpdateId()			
			await self.bot.send_photo(self.user, photo=bytes_io)
		except NetworkError:
			await asyncio.sleep(TIMEOUT)
		except Forbidden:
			print(FORBIDDEN_ERROR)
		except Exception as e:
			print(TELEGRAM_PLUGIN_ERROR + str(e))
			

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
						messageList.append(update.message.text)

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
			except Exception as e:
				print(TELEGRAM_PLUGIN_ERROR + str(e))

		return messageList
		

	async def getUpdateId(self):
		# Get the first pending update_id, this is so we can skip over it in case
		# we get a "Forbidden" exception.
		try:
			update_id = (await self.bot.get_updates())[0].update_id
		except IndexError:
			update_id = None
		except Exception as e:
			print(TELEGRAM_PLUGIN_ERROR + str(e))			
			
		return update_id			


