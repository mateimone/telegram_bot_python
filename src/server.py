import asyncio
import json
import os

from threading import Thread, Lock
from flask import Flask, request
from miscellaneous import prettify_json
from Database import Database
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
    def get_chats_by_repo(repo: str, db: Database):
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM user_data WHERE repo = ?', (repo,))

        data_list = cursor.fetchall()
        chat_id_list = [data[0] for data in data_list]
        conn.close()

        return chat_id_list

    @staticmethod
    def get_event_loop():
        return Server._event_loop

    @staticmethod
    @app.route('/<repo>/branch/create', methods=['POST'])
    async def branch_create(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('branch_creation.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has created a new branch {branch_name}!', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/branch/delete', methods=['POST'])
    async def branch_delete(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('branch_deletion.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has deleted branch {branch_name}!', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/issues', methods=['POST'])
    async def issue(repo):
        print('here')
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('issue_updates.txt', js)

        data = json.loads(js)
        sender = data['sender']['login']
        action = data['action']
        title = data['issue']['title']
        number = data['issue']['number']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has {action} issue #{number} "{title}"', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/issue/comment', methods=['POST'])
    async def issue_comment(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('issue_comments.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']
        issue_title = data['issue']['title']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {commenter} commented on issue "{issue_title}": {comment}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/commit/comment', methods=['POST'])
    async def commit_comment(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('commit_comments.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {commenter} commented on a commit: {comment}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/milestone', methods=['POST'])
    async def milestone(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('milestones.txt', js)

        data = json.loads(js)
        action = data['action']
        milestone_title = data['milestone']['title']
        creator = data['milestone']['creator']['login']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Milestone "{milestone_title}" was {action} by {creator}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request', methods=['POST'])
    async def pull_request(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_requests.txt', js)

        data = json.loads(js)
        action = data['action']
        pr_title = data['pull_request']['title']
        sender = data['sender']['login']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Pull request "{pr_title}" was {action} by {sender}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/label', methods=['POST'])
    async def label(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('label_events.txt', js)

        data = json.loads(js)
        action = data['action']
        label_name = data['label']['name']
        repo_name = data['repository']['name']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Label "{label_name}" was {action} in repository {repo_name}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/push', methods=['POST'])
    async def push(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('push_events.txt', js)

        data = json.loads(js)
        pusher = data['pusher']['name']
        ref = data['ref']
        branch = str(ref).split('/')[2]

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(bot.send_update(f'Push event by {pusher} on {branch} ({ref})', chat_id),
                                             bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request/review', methods=['POST'])
    async def pull_request_review(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_request_review_events.txt', js)

        data = json.loads(js)
        reviewer = data['review']['user']['login']
        review_state = data['review']['state']
        pr_title = data['pull_request']['title']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Review {review_state} by {reviewer} on pull request "{pr_title}"', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request/review/comment', methods=['POST'])
    async def pull_request_review_comment(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('pull_request_review_comment_events.txt', js)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment_body = data['comment']['body']
        pr_title = data['pull_request']['title']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Comment by {commenter} on pull request "{pr_title}": {comment_body}', chat_id),
                bot.get_event_loop())

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/team_add', methods=['POST'])
    async def team_add(repo):
        bot: TelegramBot = TelegramBot.get_instance()
        js = json.dumps(request.json)
        Server.write_to_file('team_add_events.txt', js)

        data = json.loads(js)
        team_name = data['team']['name']
        repo_name = data['repository']['name']

        db: Database = bot.db
        chat_id_list: list = Server.get_chats_by_repo(repo, db)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Team "{team_name}" added to repository {repo_name}', chat_id),
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
