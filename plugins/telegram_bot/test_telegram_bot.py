from telegram_bot import TelegramBot
import asyncio
from PIL import Image

SLEEP_TIME = 3

token = "BOT_TOKEN"
user = "USER_ID"

image_path = "image.png"

async def runTasks():
	messageList = []

	try:
		bot = TelegramBot(token, user) 
		
		# Receive message
		messageList = await bot.receive()
		await asyncio.sleep(SLEEP_TIME)
		
		# Send message		
		await bot.send("MAGI test")
		await asyncio.sleep(SLEEP_TIME)
		
		# Send image
		image = Image.open(image_path)
		await bot.send_image(image)	
		await asyncio.sleep(SLEEP_TIME)		
		
	except Exception as e:
		print("[ERROR] Telegram Bot exception: " + str(e))
    
	return messageList
    
    
for i in range(2):
	messageList = asyncio.run(runTasks())
	print("New message: " + " ".join(messageList))	

