from telegram_bot import TelegramBot
from server import Server

if __name__ == "__main__":
    bot = TelegramBot()
    bot.start()

    server = Server()
    server.start()

    bot.join()
    server.join()

    print('ready')
