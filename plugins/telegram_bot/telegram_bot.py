from telegram import Bot
from telegram.error import Forbidden, NetworkError
import asyncio
from io import BytesIO

TIMEOUT = 10
MAX_RETRIES = 10
FORBIDDEN_ERROR = "[ERROR] The user has removed or blocked the Telegram bot."
TELEGRAM_PLUGIN_ERROR = "[ERROR] Telegram plugin exception: "
TELEGRAM_IMAGE_NAME = "image.png"
TELEGRAM_IMAGE_FORMAT = "PNG"


class TelegramBot:

    def __init__(self, token, user):
        self.bot = Bot(token)
        self.user = user

    async def send(self, text) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                await self.bot.send_message(self.user, text)
                return True

            except NetworkError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(TIMEOUT * (attempt + 1))
                    continue

                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except Forbidden:
                print(FORBIDDEN_ERROR)
                break

            except Exception as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))
                break

        return False


    async def send_image(self, image) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                bytes_io = BytesIO()
                bytes_io.name = TELEGRAM_IMAGE_NAME
                image.save(bytes_io, TELEGRAM_IMAGE_FORMAT)
                bytes_io.seek(0)
                await self.bot.send_photo(self.user, photo=bytes_io)
                return True

            except NetworkError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(TIMEOUT * (attempt + 1))
                    continue

                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except Forbidden:
                print(FORBIDDEN_ERROR)
                break

            except Exception as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))
                break

        return False


    async def receive(self) -> list[str]:
        messageList: list[str] = []

        # Get pending updates
        try:
            updates = await self.bot.get_updates(timeout = TIMEOUT)

            # Process messages
            for update in updates:
                if update.message and update.message.text and str(update.message.from_user.id) == self.user:
                    messageList.append(update.message.text)

            # Mark as read
            if updates:
                await self.bot.get_updates(offset = updates[-1].update_id + 1, timeout = 0)

        except Exception as e:
            print(TELEGRAM_PLUGIN_ERROR + str(e))

        return messageList

