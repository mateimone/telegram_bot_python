import asyncio
import os
from typing import Final, List
from telegram import Update
from telegram.ext import ContextTypes
from github import Github, Repository
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from threading import Thread, Lock
from ngrok_process import Ngrok


class TelegramBot(Thread):
    TOKEN: Final = "6855973254:AAFTLCJXcyjVwQ4R-lZSAcB1Fl5xpf_QhtM"
    BOT_USERNAME: Final = "@matei_github_bot"
    _instance = None
    _event_loop = None
    _lock = Lock()

    def __init__(self, gh_token=None, repo=None, username=None, chat_id=None):
        super().__init__()
        self.repo: str | None = repo
        self.username: str | None = username
        self.app: Application = Application.builder().token(TelegramBot.TOKEN).build()
        self.chat_id = chat_id
        self.gh_token = gh_token
        self.lock = Lock()

    @staticmethod
    def get_instance():
        return TelegramBot._instance

    @staticmethod
    def get_event_loop():
        return TelegramBot._event_loop

    # # TODO: make it a singleton
    # def __new__(cls, *args, **kwargs):
    #     with cls._lock:
    #         if cls._instance is None:
    #             cls._instance = super(TelegramBot, cls).__new__(cls)
    #
    #     return cls._instance

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
        self.chat_id = update.effective_chat.id
        await update.message.reply_text('Hello! Thanks for chatting with me!')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('This works.')

    async def link_github_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        account_token = ' '.join(context.args)
        self.gh_token = account_token
        await update.message.reply_text('GitHub account token updated')

    async def link_github_repo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        repo = ' '.join(context.args)
        self.repo = repo
        await update.message.reply_text('Repository updated')

    async def link_github_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = ' '.join(context.args)
        self.username = username
        await update.message.reply_text('Name updated')

    async def save_to_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with open('user_data.txt', 'w') as file:
            file.write(f"{self.chat_id}\n{self.username}\n{self.repo}\n{self.gh_token}")
        await update.message.reply_text('Saved GitHub data to file')

    async def create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print("HERE")
        with self.lock:
            title = context.args[0]
            body = context.args[1]
            gh = Github(self.gh_token).get_user(self.username).get_repo(self.repo)

            issue = gh.create_issue(
                title=title,
                body=body
            )

            await update.message.reply_text(f'Issue created at {issue.html_url}')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_type: str = update.message.chat.type  # tells whether group chat or private conversation
        text: str = update.message.text

        print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')

        if message_type != 'group':
            await update.message.reply_text('Please use one of the commands. Type "/" to see all existing commands.')

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Update {update} caused error {context.error}")

    async def send_update(self, message: str):
        print(self.chat_id)
        if self.chat_id:
            await self.app.bot.send_message(chat_id=self.chat_id, text=message)

    async def set_webhooks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # try:
        # future = asyncio.run_coroutine_threadsafe(Ngrok.get_ngrok_url(), Ngrok.get_event_loop())
        port = context.args[0]
        result = await Ngrok.get_ngrok_url(port)
        # result = future.result(3)
        config = {
            "url": result,
            "content_type": "json"
        }
        repository = Github(self.gh_token).get_user(self.username).get_repo(self.repo)
        self.push_hooks(repository, config, result + "/branch/create", ["create"])
        self.push_hooks(repository, config, result + "/issue", ["issues"])

        # except concurrent.futures.TimeoutError:
        #     print("Coroutine did not complete within timeout period.")

    def push_hooks(self, repository: Repository, config: dict[str, str], path: str, events: List[str]):
        config["url"] = path
        print("PUSHED")
        repository.create_hook(
            name='web',
            config=config,
            events=events,
            active=True
        )

    # @staticmethod
    # async def close_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     # asyncio.run_coroutine_threadsafe(Ngrok.stop_ngrok(), Ngrok.get_event_loop())
    #     # asyncio.run_coroutine_threadsafe(Ngrok.get_event_loop().run_until_complete(Ngrok.terminate_ngrok()), Ngrok.get_event_loop())
    #     await Ngrok.terminate_ngrok()
    #     await update.message.reply_text('Closing bot...')
    #     for task in asyncio.all_tasks():
    #         task.cancel()
    #     TelegramBot._event_loop.stop()
    #     sys.exit(0)

    def main_telegram(self):
        print("Starting bot")

        # bot = TelegramBot()

        # Commands
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('linkghusername', self.link_github_username_command))
        self.app.add_handler(CommandHandler('linkghrepo', self.link_github_repo_command))
        self.app.add_handler(CommandHandler('linkghtoken', self.link_github_token_command))
        self.app.add_handler(CommandHandler('createissue', self.create_issue))
        self.app.add_handler(CommandHandler('help', self.help))
        self.app.add_handler(CommandHandler('save', self.save_to_file))
        # self.app.add_handler(CommandHandler('close', self.close_bot))
        self.app.add_handler(CommandHandler('auto_set_webhooks', self.set_webhooks))

        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))

        # Error
        self.app.add_error_handler(self.error)

        # print(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.txt'))

        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.txt')):
            # print("HERE")
            with open('user_data.txt', 'r') as file:
                tokens = file.read().split('\n')
                self.chat_id = tokens[0]
                self.username = tokens[1]
                self.repo = tokens[2]
                self.gh_token = tokens[3]

        # print(self.chat_id, self.username, self.repo, self.gh_token)
        TelegramBot._instance = self

        print("Polling...")
        self.app.run_polling(poll_interval=0.2)
