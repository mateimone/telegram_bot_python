import argparse

from telegram_bot import TelegramBot
from server import Server

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--myarg', type=str, default=False, help='Debug argument')

    args = parser.parse_args()
    debug = True if args.myarg == 'True' else False

    bot = TelegramBot()
    bot.start()

    server = Server(debug)
    server.start()

    server.join()
    bot.join()