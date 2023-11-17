import asyncio
import time
from threading import Thread, Lock

from flask import Flask, request
from miscellaneous import prettify_json
from telegram_bot import TelegramBot
import json
app: Flask = Flask(__name__)
class Server(Thread):
    def __init__(self):
        super().__init__()
        self.lock = Lock()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            self.main_server()
        except Exception as e:
            print(f"Exception in TelegramBot: {e}")

    def main_server(self):
        app.run(debug=True, port=4040, use_reloader=False)

    @staticmethod
    @app.route('/branch/create', methods=['POST'])
    async def branch_create():
        bot = TelegramBot.get_instance()
        file = open('github_update.txt', 'w')
        file.write(prettify_json(json.dumps(request.json)))
        file.close()

        await bot.send_update('A new branch has been created!')

        return 'Success', 200
