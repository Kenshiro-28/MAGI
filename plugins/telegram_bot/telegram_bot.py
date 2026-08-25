import asyncio

from telegram import Bot
from telegram.error import BadRequest, Forbidden, NetworkError


TIMEOUT = 10
SEND_RETRY_DELAYS = (5, 10, 30, 60, 120, 240, 480)
MAX_RETRIES = len(SEND_RETRY_DELAYS) + 1

FORBIDDEN_ERROR = "[ERROR] The user has removed or blocked the Telegram bot."
TELEGRAM_PLUGIN_ERROR = "[ERROR] Telegram plugin exception: "


class TelegramBot:

    def __init__(self, token: str, user: str) -> None:
        self.bot = Bot(token)
        self.user = str(user)

    async def send(self, text: str) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                async with self.bot:
                    await self.bot.send_message(
                        chat_id=self.user,
                        text=text,
                    )
                return True

            except BadRequest as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except NetworkError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(SEND_RETRY_DELAYS[attempt])
                    continue

                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except Forbidden:
                print(FORBIDDEN_ERROR)

            except Exception as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))

            break

        return False

    async def send_image(self, path: str) -> bool:
        for attempt in range(MAX_RETRIES):
            try:
                async with self.bot:
                    with open(path, "rb") as image_file:
                        await self.bot.send_document(
                            chat_id=self.user,
                            document=image_file,
                        )

                return True

            except BadRequest as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except NetworkError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(SEND_RETRY_DELAYS[attempt])
                    continue

                print(TELEGRAM_PLUGIN_ERROR + str(e))

            except Forbidden:
                print(FORBIDDEN_ERROR)

            except Exception as e:
                print(TELEGRAM_PLUGIN_ERROR + str(e))

            break

        return False

    async def receive(self) -> list[str]:
        message_list: list[str] = []

        try:
            async with self.bot:
                updates = await self.bot.get_updates(timeout=TIMEOUT)

                for update in updates:
                    message = update.message

                    if (
                        message
                        and message.text
                        and message.from_user
                        and str(message.from_user.id) == self.user
                    ):
                        message_list.append(message.text)

                # Advance the Telegram update offset so processed
                # updates are not returned by the next Bot instance.
                if updates:
                    await self.bot.get_updates(
                        offset=updates[-1].update_id + 1,
                        timeout=0,
                    )

        except Forbidden:
            print(FORBIDDEN_ERROR)

        except Exception as e:
            print(TELEGRAM_PLUGIN_ERROR + str(e))

        return message_list

