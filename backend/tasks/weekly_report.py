from backend.clients.telegram.telegram import TelegramClient
from backend.settings import settings


# TODO: Implement daily report logic
def weekly_report(chat_id: int) -> None:
    telegram = TelegramClient(settings.bot_token)
    message = "Weekly report generated."
    telegram.send_message(chat_id, message=message)
