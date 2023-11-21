import asyncio
import json
import os

from threading import Thread, Lock
from flask import Flask, request
from miscellaneous import prettify_json
from telegram_bot import TelegramBot

app: Flask = Flask(__name__)

class Server(Thread):
    _event_loop = None
    _debug = False

    def __init__(self, _debug):
        super().__init__()
        self.lock = Lock()
        Server._debug = _debug

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            Server._event_loop = loop
            self.main_server()
        except Exception as e:
            print(f"Exception in TelegramBot: {e}")

    def main_server(self):
        dir_name = "src/update_data"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)

        app.run(debug=Server._debug, port=4040, use_reloader=False)

    @staticmethod
    def get_event_loop():
        return Server._event_loop

    @staticmethod
    @app.route('/branch/create', methods=['POST'])
    async def branch_create():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('branch_creation.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {sender} has created a new branch {branch_name}!'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/branch/delete', methods=['POST'])
    async def branch_delete():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('branch_deletion.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {sender} has deleted branch {branch_name}!'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/issues', methods=['POST'])
    async def issue():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('issue_updates.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        action = data['action']
        title = data['issue']['title']
        number = data['issue']['number']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {sender} has {action} issue #{number} "{title}"'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/issue/comment', methods=['POST'])
    async def issue_comment():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('issue_comments.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']
        issue_title = data['issue']['title']

        asyncio.run_coroutine_threadsafe(
            bot.send_update(f'User {commenter} commented on issue "{issue_title}": {comment}'),
            bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/commit/comment', methods=['POST'])
    async def commit_comment():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('commit_comments.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'User {commenter} commented on a commit: {comment}'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/milestone', methods=['POST'])
    async def milestone():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('milestones.txt', js)

        data = json.loads(js)
        action = data['action']
        milestone_title = data['milestone']['title']
        creator = data['milestone']['creator']['login']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'Milestone "{milestone_title}" was {action} by {creator}'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/pull_request', methods=['POST'])
    async def pull_request():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_requests.txt', js)

        data = json.loads(js)
        action = data['action']
        pr_title = data['pull_request']['title']
        sender = data['sender']['login']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'Pull request "{pr_title}" was {action} by {sender}'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/label', methods=['POST'])
    async def label():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('label_events.txt', js)

        data = json.loads(js)
        action = data['action']
        label_name = data['label']['name']
        repo_name = data['repository']['name']

        asyncio.run_coroutine_threadsafe(
            bot.send_update(f'Label "{label_name}" was {action} in repository {repo_name}'),
            bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/push', methods=['POST'])
    async def push():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('push_events.txt', js)

        data = json.loads(js)
        pusher = data['pusher']['name']
        ref = data['ref']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'Push event by {pusher} on {ref}'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/pull_request/review', methods=['POST'])
    async def pull_request_review():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_request_review_events.txt', js)

        data = json.loads(js)
        reviewer = data['review']['user']['login']
        review_state = data['review']['state']
        pr_title = data['pull_request']['title']

        asyncio.run_coroutine_threadsafe(
            bot.send_update(f'Review {review_state} by {reviewer} on pull request "{pr_title}"'),
            bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/pull_request/review/comment', methods=['POST'])
    async def pull_request_review_comment():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_request_review_comment_events.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment_body = data['comment']['body']
        pr_title = data['pull_request']['title']

        asyncio.run_coroutine_threadsafe(
            bot.send_update(f'Comment by {commenter} on pull request "{pr_title}": {comment_body}'),
            bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/team_add', methods=['POST'])
    async def team_add():
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('team_add_events.txt', js)

        data = json.loads(js)
        team_name = data['team']['name']
        repo_name = data['repository']['name']

        asyncio.run_coroutine_threadsafe(bot.send_update(f'Team "{team_name}" added to repository {repo_name}'),
                                         bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    def write_to_file(path: str, js: str):
        if Server._debug:
            file = open(f'src/update_data/{path}', 'w')
            file.write(prettify_json(js))
            file.close()

    @staticmethod
    def stop_server():
        for task in asyncio.all_tasks():
            task.cancel()
        Server._event_loop.stop()
