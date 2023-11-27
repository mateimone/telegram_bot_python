import argparse
import sqlite3

from telegram_bot import TelegramBot
from server import Server

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', type=str, default=False, help='Debug argument')

    args: argparse.Namespace = parser.parse_args()

    debug = args.debug == 'True'

    bot = TelegramBot()
    bot.start()

    server = Server(debug)
    server.start()

    server.join()
    bot.join()
