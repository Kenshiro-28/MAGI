from telegram_bot import TelegramBot
import asyncio

token = "BOT_TOKEN"
user = "USER_ID"

async def runTasks():
	messageList = []

	try:
		bot = TelegramBot(token, user) 
		messageList = await bot.receive()
		await asyncio.sleep(5)
		await bot.send("MAGI test")
		await asyncio.sleep(5)		
		
	except Exception as e:
		print("[ERROR] Telegram Bot exception: " + str(e))
    
	return messageList
    
    
for i in range(2):
	messageList = asyncio.run(runTasks())
	print("New message: " + " ".join(messageList))	

