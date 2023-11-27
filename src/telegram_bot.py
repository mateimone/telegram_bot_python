import asyncio
import os
import sqlite3
from typing import Final, List

from telegram import Update
from telegram.ext import ContextTypes
from github import Github, Repository
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from threading import Thread, Lock
from ngrok_process import Ngrok
from Database import Database


class TelegramBot(Thread):
    TOKEN: Final = ""
    BOT_USERNAME: Final = "@matei_github_bot"
    _instance = None
    _event_loop = None
    _lock = Lock()
    _db = None

    def __init__(self):
        super().__init__()
        # self.repo: str | None = ''
        # self.username: str | None = ''
        self.app: Application = Application.builder().token(TelegramBot.TOKEN).build()
        self.chat_id: str = ''
        # self.gh_token = ''
        self.lock = Lock()
        # self.gh_api_repo: Repository = None
        TelegramBot._db = Database('src/user_data.db')
        TelegramBot._db.setup_db()

    @staticmethod
    def get_db():
        return TelegramBot._db

    @staticmethod
    def get_instance():
        return TelegramBot._instance

    @staticmethod
    def get_event_loop():
        return TelegramBot._event_loop

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            TelegramBot._event_loop = loop

            self.main_telegram()
        except Exception as e:
            print(f"Exception in TelegramBot: {e}")

    # Commands
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # self.chat_id = update.effective_chat.id
        chat_id = update.effective_chat.id
        # self.add_data_to_file(str(chat_id), 0)
        db: Database = TelegramBot._db
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(f'INSERT OR IGNORE INTO user_data (chat_id) VALUES (?)', (chat_id, ))
        conn.commit()
        conn.close()
        self.chat_id = chat_id
        await update.message.reply_text('Hello! Thanks for chatting with me!')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help = '/start - starts the conversation and registers the conversation ID\n'
        help += '/help - display useful information about the commands\n'
        help += '/linkghrepo param - links the bot to the repository name given as param\n'
        help += '/linkghtoken param - links the bot to the GitHub token given as param\n'
        help += '/linkghusername param - links the bot to the username given as param\n'
        help += '/autosetwebhooks param - automatically sets webhooks for updates on ngrok\'s web interface port\n'
        help += '/createissue param1 param2 - creates an issue with param1 as title and param2 as body\n'
        help += ('/createbranch param1 _param2 - creates a branch with param1 as name with \'main\' as source branch, '
                 'unless _param2 is filled with a correct branch name\n')
        help += '/deletebranch param1 - deletes the branch given as param1\n'
        help += '/listbranches - print all existing branches\n'
        help += '/linktogithub - returns a link to the README.md file of the bot\n'
        await update.message.reply_text(help)

    def update_row_with_id(self, value, column_name, chat_id):
        # TelegramBot._db.insert(self.chat_id, self.repo, self.gh_token, self.username)
        db: Database = TelegramBot._db
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE user_data SET {column_name} = ? WHERE chat_id = ?', (value, chat_id))
        conn.commit()
        conn.close()

    def fetch_resource_with_id(self, chat_id, column=None):
        db: Database = TelegramBot._db
        conn = db.connect()
        cursor = conn.cursor()
        if column is None:
            cursor.execute('SELECT * FROM user_data WHERE chat_id = ?', (chat_id, ))
        else:
            cursor.execute(f'SELECT {column} FROM user_data WHERE chat_id = ?', (chat_id, ))
        row = cursor.fetchone()
        conn.close()

        return row

    async def link_github_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        gh_token = ' '.join(context.args)
        # self.gh_token = account_token
        # self.add_data_to_file(gh_token, 2)
        # complete = self.data_incomplete()
        # if complete:
        self.update_row_with_id(gh_token, 'token', chat_id)
        await update.message.reply_text('GitHub account token updated')

    async def link_github_repo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        repo = ' '.join(context.args)
        # self.repo = repo
        # self.add_data_to_file(repo, 1)
        # complete = self.data_incomplete()
        # if complete:
        self.update_row_with_id(repo, 'repo', chat_id)
        await update.message.reply_text('Repository updated')

    async def link_github_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = ' '.join(context.args)
        # self.username = username
        # self.add_data_to_file(username, 3)
        # complete = self.data_incomplete()
        # if complete:
        self.update_row_with_id(username, 'username', chat_id)
        await update.message.reply_text('Name updated')

    # def add_data_to_file(self, data: str, pos: int):
    #     lines = []
    #     with open('src/user_data.txt', 'r') as file:
    #         lines = file.readlines()
    #         lines[pos] = data + '\n'
    #
    #     with open('src/user_data.txt', 'w') as file:
    #         file.writelines(lines)

    # def data_incomplete(self, chat_id) -> bool:
    #     """
    #     Whenever this is called, it also updates the GitHub repository API
    #     :return:
    #     """
    #     if self.gh_token == '' or self.username == '' or self.repo == '' or self.chat_id == '':
    #         return False
    #     if self.gh_api_repo is None:
    #         self.gh_api_repo = Github(self.gh_token).get_user(self.username).get_repo(self.repo)

        return True

    async def create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            data = await self.get_user_data(update)
            incomplete = await self.check_incomplete_row(update, data)
            if incomplete:
                return

            if len(context.args) < 2:
                await update.message.reply_text('Please provide a title and body for the issue.')
                return
            title = context.args[0]
            body = ' '.join(context.args[1:])

            github_api_repo = await self.get_api_repo(data)

            issue = github_api_repo.create_issue(
                title=title,
                body=body
            )

    async def create_branch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            data = await self.get_user_data(update)
            incomplete = await self.check_incomplete_row(update, data)
            if incomplete:
                return

            name = context.args[0]
            source_branch = 'main'
            if len(context.args) == 2:
                source_branch = context.args[1]

            github_api_repo = await self.get_api_repo(data)

            branch_exists = any(branch.name == source_branch for branch in github_api_repo.get_branches())
            new_branch_exists = any(branch.name == name for branch in github_api_repo.get_branches())

            if new_branch_exists:
                await update.message.reply_text(f"Branch {name} already exists!")
                return
            if branch_exists:
                sha = github_api_repo.get_branch(source_branch).commit.sha
                gitref: Repository.GitRef = github_api_repo.create_git_ref(ref=f"refs/heads/{name}", sha=sha)
            else:
                await update.message.reply_text("Source branch not found!")

    async def list_branches(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            data = await self.get_user_data(update)
            incomplete = await self.check_incomplete_row(update, data)
            if incomplete:
                return

            github_api_repo = await self.get_api_repo(data)

            branches = github_api_repo.get_branches()
            branch_names = [branch.name for branch in branches]
            await update.message.reply_text(f'Branches: {", ".join(branch_names)}')

    async def delete_branch(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            data = await self.get_user_data(update)
            incomplete = await self.check_incomplete_row(update, data)
            if incomplete:
                return

            if len(context.args) != 1:
                await update.message.reply_text('Please provide the name of the branch to be deleted.')
                return

            github_api_repo = await self.get_api_repo(data)

            branch_name = context.args[0]
            branch_exists = any(branch.name == branch_name for branch in github_api_repo.get_branches())
            if not branch_exists:
                await update.message.reply_text('Provided branch does not exist!')
                return
            ref = github_api_repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()

    async def set_webhooks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            data = await self.get_user_data(update)
            incomplete = await self.check_incomplete_row(update, data)
            if incomplete:
                return

            if len(context.args) == 0:
                await update.message.reply_text('The command cannot be used without a given port.')
                return

            port = context.args[0]

            events = ["create", "delete", "issues", "issue_comment", "commit_comment", "milestone", "label", "push",
                      "pull_request", "pull_request_review", "pull_request_review_comment", "team_add"]

            github_api_repo = await self.get_api_repo(data)
            repo = data[1]

            hooks = github_api_repo.get_hooks()
            for hook in hooks:
                if hook.events[0] in events and len(hook.events) == 1:
                    hook.delete()  # delete previous hooks

            result = await Ngrok.get_ngrok_url(port)
            config = {
                "url": result,
                "content_type": "json"
            }
            self.push_hooks(github_api_repo, config, result + f"/branch/create?repo={repo}", ["create"])
            self.push_hooks(github_api_repo, config, result + f"/branch/delete?repo={repo}", ["delete"])
            self.push_hooks(github_api_repo, config, result + f"/issues?repo={repo}", ["issues"])
            self.push_hooks(github_api_repo, config, result + f"/issue/comment?repo={repo}", ["issue_comment"])
            self.push_hooks(github_api_repo, config, result + f"/commit/comment?repo={repo}", ["commit_comment"])
            self.push_hooks(github_api_repo, config, result + f"/milestone?repo={repo}", ["milestone"])
            self.push_hooks(github_api_repo, config, result + f"/label?repo={repo}", ["label"])
            self.push_hooks(github_api_repo, config, result + f"/push?repo={repo}", ["push"])
            self.push_hooks(github_api_repo, config, result + f"/pull_request?repo={repo}", ["pull_request"])
            self.push_hooks(github_api_repo, config, result + f"/pull_request/review?repo={repo}", ["pull_request_review"])
            self.push_hooks(github_api_repo, config, result + f"/pull_request/review/comment?repo={repo}",
                            ["pull_request_review_comment"])
            self.push_hooks(github_api_repo, config, result + f"/team_add?repo={repo}", ["team_add"])
            await update.message.reply_text('Webhooks set! To see a list of notifications you might receive, '
                                            'visit https://github.com/mateimone/telegram_bot_python/blob/main/README.md. '
                                            'Make sure that the port is correct, otherwise run the method again with the '
                                            'correct port')

    def push_hooks(self, repository: Repository, config: dict[str, str], path: str, events: List[str]):
        config["url"] = path
        print("PUSHED")
        repository.create_hook(
            name='web',
            config=config,
            events=events,
            active=True
        )

    async def check_incomplete_row(self, update: Update, data):
        if data and any(cell is None for cell in data):
            await self.incomplete_reply(update, data)
            return True
        return False

    async def incomplete_reply(self, update: Update, data):
        if data is None:
            await update.message.reply_text(
                f'It seems the Chat ID was not saved. This should be fixed now, please re-run the command'
            )
        else:
            await update.message.reply_text(
                f'The data you have provided is incomplete.\nGitHub repo - {data[1]}\nGitHub token - {data[2]}'
                f'\nGitHub username - {data[3]}\nChat ID - {data[0]}\n'
                f'\nWebhooks were NOT set.')

    async def get_api_repo(self, data):
        repo, token, username = data[1], data[2], data[3]
        github_api_repo = Github(token).get_user(username).get_repo(repo)
        return github_api_repo

    async def get_user_data(self, update):
        chat_id = update.effective_chat.id
        data = self.fetch_resource_with_id(chat_id)
        return data

    async def link_to_github(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f'This is a link to the README.md file of this project.\n'
            f'https://github.com/mateimone/telegram_bot_python/blob/main/README.md')

    async def send_update(self, message: str):
        print(self.chat_id)
        if self.chat_id:
            await self.app.bot.send_message(chat_id=self.chat_id, text=message)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(update.message.text)
        await update.message.reply_text('Please use one of the commands. Type "/" to see all existing commands.')

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Update {update} caused error {context.error}")

    def main_telegram(self):
        print("Starting bot\n")

        # Commands
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('linkghusername', self.link_github_username_command))
        self.app.add_handler(CommandHandler('linkghrepo', self.link_github_repo_command))
        self.app.add_handler(CommandHandler('linkghtoken', self.link_github_token_command))
        self.app.add_handler(CommandHandler('createissue', self.create_issue))
        self.app.add_handler(CommandHandler('createbranch', self.create_branch))
        self.app.add_handler(CommandHandler('listbranches', self.list_branches))
        self.app.add_handler(CommandHandler('deletebranch', self.delete_branch))
        self.app.add_handler(CommandHandler('help', self.help))
        self.app.add_handler(CommandHandler('autosetwebhooks', self.set_webhooks))
        self.app.add_handler(CommandHandler('linktogithub', self.link_to_github))

        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))

        # Error
        self.app.add_error_handler(self.error)

        # if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.txt')):
        #     with open('src/user_data.txt', 'r') as file:
        #         tokens = file.read().split('\n')
        #         # self.chat_id = tokens[0]
        #         # self.repo = tokens[1]
        #         # self.gh_token = tokens[2]
        #         # self.username = tokens[3]
        #         file.close()
        # else:
        #     with open('src/user_data.txt', 'w') as file:
        #         file.write('\n\n\n\n')
        #         file.close()

        TelegramBot._instance = self

        print("Polling...")
        self.app.run_polling(poll_interval=0.2)
