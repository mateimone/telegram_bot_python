from ngrok_process import Ngrok
from telegram_bot import TelegramBot
from server import Server


if __name__ == "__main__":
    bot = TelegramBot()
    bot.start()

    server = Server()
    server.start()

    server.join()

    ngrok = Ngrok()
    bot.join()