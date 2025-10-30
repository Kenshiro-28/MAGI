from plugins.telegram_bot import telegram_bot
from PIL import Image
import time
import asyncio
import core

# COMMS
MESSAGE_RECEIVED_TEXT_1 = "了解。「"
MESSAGE_RECEIVED_TEXT_2 = "」"
COMMS_ERROR = "\n[ERROR] Comms error: "

# TELEGRAM PLUGIN
TELEGRAM_PLUGIN_SEND_WAIT_TIME = 1
TELEGRAM_PLUGIN_RECEIVE_WAIT_TIME = 5
TELEGRAM_PLUGIN_CHAR_LIMIT = 4096
TELEGRAM_MESSAGE_QUEUE_LIMIT = 100
TELEGRAM_TAG = "\n[TELEGRAM] "

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_USER_ID = ""

telegram_bot_enabled = False

telegram_message_queue = []


def printMagiText(text: str):
    if telegram_bot_enabled:
        _send_telegram_bot(text)

    core.print_magi_text(text)


def printSystemText(text: str):
    if telegram_bot_enabled:
        _send_telegram_bot(text)

    core.print_system_text(text)


def userInput() -> str:
    if telegram_bot_enabled:
        message = _receive_telegram_bot()

        if message:
            core.print_system_text(TELEGRAM_TAG + message)
            _send_telegram_bot(MESSAGE_RECEIVED_TEXT_1 + message + MESSAGE_RECEIVED_TEXT_2)
    else:
        message = core.user_input()

    return message


# TELEGRAM PLUGIN OPERATIONS

def _send_telegram_bot(text):
    for i in range(0, len(text), TELEGRAM_PLUGIN_CHAR_LIMIT):
        message = text[i:i + TELEGRAM_PLUGIN_CHAR_LIMIT]

        time.sleep(TELEGRAM_PLUGIN_SEND_WAIT_TIME)

        try:
            bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
            asyncio.run(bot.send(message))

        except Exception as e:
            print(COMMS_ERROR + str(e))


def _receive_telegram_bot():
    global telegram_message_queue

    message = ""

    try:
        if len(telegram_message_queue) == 0:
            time.sleep(TELEGRAM_PLUGIN_RECEIVE_WAIT_TIME)

            bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)

            # Fetch pending messages
            message_list = asyncio.run(bot.receive())

            # Append pending messages to message queue
            telegram_message_queue.extend(message_list)

    except Exception as e:
        print(COMMS_ERROR + str(e))

    # If the message queue exceeds the limit, delete the oldest messages
    if len(telegram_message_queue) > TELEGRAM_MESSAGE_QUEUE_LIMIT:
        telegram_message_queue = telegram_message_queue[-TELEGRAM_MESSAGE_QUEUE_LIMIT:]

    # Dequeue oldest message
    if telegram_message_queue:
        message = telegram_message_queue.pop(0)

    return message


def initialize_telegram_bot(token: str, user_id: str):
    global TELEGRAM_BOT_TOKEN
    global TELEGRAM_USER_ID
    global telegram_bot_enabled

    TELEGRAM_BOT_TOKEN = token
    TELEGRAM_USER_ID = user_id

    telegram_bot_enabled = True


def send_image_telegram_bot(image: Image.Image):
    time.sleep(TELEGRAM_PLUGIN_SEND_WAIT_TIME)

    try:
        bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
        asyncio.run(bot.send_image(image))

    except Exception as e:
        print(COMMS_ERROR + str(e))


