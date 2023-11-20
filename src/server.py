import asyncio
import time
from threading import Thread, Lock

from flask import Flask, request
from miscellaneous import prettify_json
from telegram_bot import TelegramBot
import json

app: Flask = Flask(__name__)

class Server(Thread):
    _event_loop = None

    def __init__(self):
        super().__init__()
        self.lock = Lock()

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            Server._event_loop = loop
            self.main_server()
        except Exception as e:
            print(f"Exception in TelegramBot: {e}")

    def main_server(self):
        app.run(debug=True, port=4040, use_reloader=False)

    @staticmethod
    def get_event_loop():
        return Server._event_loop

    @staticmethod
    @app.route('/webhook/create', methods=['POST'])
    async def create_webhook():
        print('WEBHOOK CREATED')

    @staticmethod
    @app.route('/branch/create', methods=['POST'])
    async def branch_create():
        bot: TelegramBot = TelegramBot.get_instance()
        file = open('github_update.txt', 'w')
        js = json.dumps(request.json)
        file.write(prettify_json(js))
        file.close()

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        # await asyncio.sleep(0.1)

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {sender} has created a new branch {branch_name}!'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/issue', methods=['POST'])
    async def issue():
        bot: TelegramBot = TelegramBot.get_instance()
        file = open('issue_updates.txt', 'w')
        js = json.dumps(request.json)
        file.write(prettify_json(js))
        file.close()

        data = json.loads(js)
        sender = data['sender']['login']
        action = data['action']
        title = data['issue']['title']
        number = data['issue']['number']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {sender} has {action} issue #{number} "{title}"'), bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    def stop_server():
        for task in asyncio.all_tasks():
            task.cancel()
        Server._event_loop.stop()
