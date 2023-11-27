import asyncio
from typing import Final, List

from telegram import Update
from telegram.ext import ContextTypes
from github import Github, Repository
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from threading import Thread, Lock
from ngrok_process import Ngrok
from Database import Database


class TelegramBot(Thread):
    TOKEN: Final = "6538498832:AAH5SRJZFMIRiubbILNernBsmjDcr8LpW1I"
    BOT_USERNAME: Final = "@matei_github_bot"
    _instance = None
    _event_loop = None
    _lock = Lock()

    def __init__(self):
        super().__init__()
        self.app: Application = Application.builder().token(TelegramBot.TOKEN).build()
        self.lock = Lock()
        self.db = Database('src/user_data.db')
        self.db.setup_db()

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

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        db: Database = self.db
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(f'INSERT OR IGNORE INTO user_data (chat_id) VALUES (?)', (chat_id, ))
        conn.commit()
        conn.close()
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

    async def update_row_with_id(self, value, column_name, chat_id, update: Update):
        data = await self.db.fetch_resource_with_id(chat_id)
        if data is None:
            await self.incomplete_reply(update, data)
            return False
        db: Database = self.db
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE user_data SET {column_name} = ? WHERE chat_id = ?', (value, chat_id))
        conn.commit()
        conn.close()

        return True

    async def link_github_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        gh_token = ' '.join(context.args)

        exists = await self.update_row_with_id(gh_token, 'token', chat_id, update)
        if exists:
            await update.message.reply_text('GitHub account token updated')

    async def link_github_repo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        repo = ' '.join(context.args)

        exists = await self.update_row_with_id(repo, 'repo', chat_id, update)
        if exists:
            await update.message.reply_text('Repository updated')

    async def link_github_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        username = ' '.join(context.args)

        exists = await self.update_row_with_id(username, 'username', chat_id, update)
        if exists:
            await update.message.reply_text('Name updated')

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

            if len(context.args) < 1:
                await update.message.reply_text('Please provide at least one name of a branch to be deleted.')
                return

            github_api_repo = await self.get_api_repo(data)

            for branch_name in context.args:
                branch_exists = any(branch.name == branch_name for branch in github_api_repo.get_branches())
                if not branch_exists:
                    await update.message.reply_text(f'Branch {branch_name} does not exist!')
                    continue
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
            self.push_hooks(github_api_repo, config, result + f"/{repo}/branch/create", ["create"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/branch/delete", ["delete"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/issues", ["issues"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/issue/comment", ["issue_comment"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/commit/comment", ["commit_comment"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/milestone", ["milestone"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/label", ["label"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/push", ["push"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/pull_request", ["pull_request"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/pull_request/review", ["pull_request_review"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/pull_request/review/comment",
                            ["pull_request_review_comment"])
            self.push_hooks(github_api_repo, config, result + f"/{repo}/team_add", ["team_add"])
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
            chat_id = update.effective_chat.id
            db = self.db
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute(f'INSERT OR IGNORE INTO user_data (chat_id) VALUES (?)', (chat_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(
                f'It seems the Chat ID was not saved. This should be fixed now, please re-run the command.'
            )
        else:
            await update.message.reply_text(
                f'The data you have provided is incomplete.\nGitHub repo - {data[1]}\nGitHub token - {data[2]}'
                f'\nGitHub username - {data[3]}\nChat ID - {data[0]}\n'
                f'\nRemember to run the /autosetwebhooks command after setting these parameters if your project '
                f'doesn\'t have webhooks already.')

    async def get_api_repo(self, data):
        repo, token, username = data[1], data[2], data[3]
        github_api_repo = Github(token).get_user(username).get_repo(repo)
        return github_api_repo

    async def get_user_data(self, update):
        chat_id = update.effective_chat.id
        data = await self.db.fetch_resource_with_id(chat_id)
        return data

    async def link_to_github(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f'This is a link to the README.md file of this project.\n'
            f'https://github.com/mateimone/telegram_bot_python/blob/main/README.md')

    async def send_update(self, message: str, chat_id: str):
        print(chat_id)
        await self.app.bot.send_message(chat_id, message)

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

        TelegramBot._instance = self

        print("Polling...")
        self.app.run_polling(poll_interval=0.2)
