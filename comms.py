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
TELEGRAM_PLUGIN_SEND_WAIT_TIME = 2
TELEGRAM_PLUGIN_RECEIVE_WAIT_TIME = 5
TELEGRAM_PLUGIN_CHAR_LIMIT = 4096
TELEGRAM_PLUGIN_SAFE_CHAR_LIMIT = 4000
TELEGRAM_MESSAGE_QUEUE_LIMIT = 100
TELEGRAM_TAG = "\n[TELEGRAM] "

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_USER_ID = ""

telegram_bot_enabled: bool = False

telegram_message_queue: list[str] = []


def printMagiText(text: str) -> None:
    if telegram_bot_enabled:
        _send_telegram_bot(text)

    core.print_magi_text(text)


def printSystemText(text: str) -> None:
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

def _send_telegram_bot(text: str) -> None:
    try:
        while len(text) > 0:
            time.sleep(TELEGRAM_PLUGIN_SEND_WAIT_TIME)
            bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)

            if len(text) <= TELEGRAM_PLUGIN_CHAR_LIMIT:
                chunk = text
                text = ""
            else:
                # Look backward from the limit to find the last space
                cut_index = text.rfind(' ', 0, TELEGRAM_PLUGIN_CHAR_LIMIT)

                # If no space is found, OR the space is too far back (less than 4000),
                # force a maximum hard cut so we don't send unnecessarily short chunks.
                if cut_index == -1 or cut_index < TELEGRAM_PLUGIN_SAFE_CHAR_LIMIT:
                    chunk = text[:TELEGRAM_PLUGIN_CHAR_LIMIT]
                    text = text[TELEGRAM_PLUGIN_CHAR_LIMIT:]
                else:
                    chunk = text[:cut_index]
                    # Skip the space we just cut on, so the next chunk doesn't start with it
                    text = text[cut_index + 1:]

            # Send the chunk
            asyncio.run(bot.send(chunk))

    except Exception as e:
        print(COMMS_ERROR + str(e))


def _receive_telegram_bot() -> str:
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

    # Dequeue next message
    if telegram_message_queue:
        message = telegram_message_queue.pop(0)
        last_chunk_len = len(message)

        # If the extracted message hits the limit, it was cut off.
        # Keep popping from the queue and stitching until we get a complete thought.
        while last_chunk_len >= TELEGRAM_PLUGIN_SAFE_CHAR_LIMIT:
            # --- NETWORK RACE CONDITION FIX ---
            # If we expect another chunk but the queue is empty, Telegram is lagging.
            if len(telegram_message_queue) == 0:
                time.sleep(TELEGRAM_PLUGIN_RECEIVE_WAIT_TIME)  # Give the server 5 seconds to catch up

                try:
                    bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
                    pending_messages = asyncio.run(bot.receive())
                    telegram_message_queue.extend(pending_messages)
                except Exception as e:
                    print(COMMS_ERROR + str(e))

                # If it is STILL empty after waiting, the message actually ended there.
                if len(telegram_message_queue) == 0:
                    break
            # --------------------------------------

            # Get next chunk
            next_chunk = telegram_message_queue.pop(0)
            message += " " + next_chunk
            last_chunk_len = len(next_chunk)

    return message


def initialize_telegram_bot(token: str, user_id: str) -> None:
    global TELEGRAM_BOT_TOKEN
    global TELEGRAM_USER_ID
    global telegram_bot_enabled

    TELEGRAM_BOT_TOKEN = token
    TELEGRAM_USER_ID = user_id

    telegram_bot_enabled = True


def send_image_telegram_bot(image: Image.Image) -> None:
    time.sleep(TELEGRAM_PLUGIN_SEND_WAIT_TIME)

    try:
        bot = telegram_bot.TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID)
        asyncio.run(bot.send_image(image))

    except Exception as e:
        print(COMMS_ERROR + str(e))


