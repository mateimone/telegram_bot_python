import argparse

from telegram_bot import TelegramBot
from server import Server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Example script')
    parser.add_argument('myarg', help='A positional argument')

    args = parser.parse_args()
    debug = args.myarg

    bot = TelegramBot()
    bot.start()

    server = Server(debug)
    server.start()

    server.join()
    bot.join()