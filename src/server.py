import asyncio
import json

from threading import Thread, Lock
from flask import Flask, request
from Database import Database
from telegram_bot import TelegramBot

app: Flask = Flask(__name__)

class Server(Thread):
    event_loop = None
    _debug = False

    def __init__(self, _debug):
        super().__init__()
        self.lock = Lock()
        Server._debug = _debug

    def run(self):
        """
        Starts the thread of the server.
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            Server.event_loop = loop
            self.main_server()
        except Exception as e:
            print(f"Exception in TelegramBot: {e}")

    def main_server(self):
        """
        Starts the server, which receives POST requests from GitHub.
        """
        app.run(debug=Server._debug, port=4040, use_reloader=False)

    @staticmethod
    @app.route('/<repo>/branch/create', methods=['POST'])
    async def branch_create(repo):
        """
        Sends a notification that a branch has been created on a certain repository.
        :param repo: repository on which the branch is created
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has created a new branch {branch_name}!', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/branch/delete', methods=['POST'])
    async def branch_delete(repo):
        """
        Sends a notification that a branch has been deleted on a certain repository.
        :param repo: repository on which the branch is deleted
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        sender = data['sender']['login']
        branch_name = data['ref']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has deleted branch {branch_name}!', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/issues', methods=['POST'])
    async def issue(repo):
        """
        Sends a notification that an issue has been created on a certain repository.
        :param repo: repository on which the issue was created
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        sender = data['sender']['login']
        action = data['action']
        title = data['issue']['title']
        number = data['issue']['number']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {sender} has {action} issue #{number} "{title}"', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/issue/comment', methods=['POST'])
    async def issue_comment(repo):
        """
        Sends a notification that a comment has been left on an issue in a certain repository.
        :param repo: repository on which the issue comment was created
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']
        issue_title = data['issue']['title']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {commenter} commented on issue "{issue_title}": {comment}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/commit/comment', methods=['POST'])
    async def commit_comment(repo):
        """
        Sends a notification that a comment has been left on a commit in a certain repository.
        :param repo: repository on which the commit comment was left
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment = data['comment']['body']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'User {commenter} commented on a commit: {comment}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/milestone', methods=['POST'])
    async def milestone(repo):
        """
        Sends a notification that a milestone has been created in a certain repository.
        :param repo: repository on which the milestone was created
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        action = data['action']
        milestone_title = data['milestone']['title']
        creator = data['milestone']['creator']['login']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Milestone "{milestone_title}" was {action} by {creator}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request', methods=['POST'])
    async def pull_request(repo):
        """
        Sends a notification that a pull request has been made on a certain repository.
        :param repo: repository on which pull request was made
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        action = data['action']
        pr_title = data['pull_request']['title']
        sender = data['sender']['login']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Pull request "{pr_title}" was {action} by {sender}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/label', methods=['POST'])
    async def label(repo):
        """
        Sends a notification that a label has been created on a certain repository.
        :param repo: repository on which label was created
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        action = data['action']
        label_name = data['label']['name']
        repo_name = data['repository']['name']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Label "{label_name}" was {action} in repository {repo_name}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/push', methods=['POST'])
    async def push(repo):
        """
        Sends a notification that a push has been made on a certain repository.
        :param repo: repository on which push was made
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        pusher = data['pusher']['name']
        ref = data['ref']
        branch = str(ref).split('/')[2]

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(bot.send_update(f'Push event by {pusher} on {branch} ({ref})', chat_id),
                                             bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request/review', methods=['POST'])
    async def pull_request_review(repo):
        """
        Sends a notification that a review has been made for a pull request made on a certain repository.
        :param repo: repository on which the review of a pull request was made
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        reviewer = data['review']['user']['login']
        review_state = data['review']['state']
        pr_title = data['pull_request']['title']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Review {review_state} by {reviewer} on pull request "{pr_title}"', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/pull_request/review/comment', methods=['POST'])
    async def pull_request_review_comment(repo):
        """
        Sends a notification that a comment has been left on a review for a pull request made on a certain repository.
        :param repo: repository on which the comment on a review for a pull request has been left
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        commenter = data['comment']['user']['login']
        comment_body = data['comment']['body']
        pr_title = data['pull_request']['title']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Comment by {commenter} on pull request "{pr_title}": {comment_body}', chat_id),
                bot.event_loop)

        return 'Success', 200

    @staticmethod
    @app.route('/<repo>/team_add', methods=['POST'])
    async def team_add(repo):
        """
        Sends a notification that a new team member has been added to a certain GitHub repository.
        :param repo: repository to which a new member was added
        :return: a success response
        """
        bot: TelegramBot = TelegramBot.instance
        js = json.dumps(request.json)

        data = json.loads(js)
        team_name = data['team']['name']
        repo_name = data['repository']['name']

        db: Database = bot.db
        chat_id_list: list = db.get_chats_by_repo(repo)
        for chat_id in chat_id_list:
            asyncio.run_coroutine_threadsafe(
                bot.send_update(f'Team "{team_name}" added to repository {repo_name}', chat_id),
                bot.event_loop)

        return 'Success', 200
