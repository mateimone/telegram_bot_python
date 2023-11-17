import asyncio
from typing import Final
from telegram import Update
from telegram.ext import ContextTypes
from github import Github
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from threading import Thread, Lock

class TelegramBot(Thread):
    TOKEN: Final = "6855973254:AAFTLCJXcyjVwQ4R-lZSAcB1Fl5xpf_QhtM"
    BOT_USERNAME: Final = "@matei_github_bot"
    _instance = None
    _lock = Lock()

    def __init__(self, gh_token=None, repo=None, username=None, chat_id=None):
        super().__init__()
        self.repo: str | None = repo
        self.username: str | None = username
        self.app: Application = Application.builder().token(TelegramBot.TOKEN).build()
        self.chat_id = chat_id
        self.gh_token = gh_token
        self.github_account: Github | None = Github(gh_token) if gh_token is not None else None
        self.lock = Lock()
        TelegramBot._instance = self

    @staticmethod
    def get_instance():
        return TelegramBot._instance

    # # TODO: make it a singleton
    # def __new__(cls, *args, **kwargs):
    #     # with cls._lock:
    #     if cls._instance is None:
    #         cls._instance = super(TelegramBot, cls).__new__(cls)
    #     # time.sleep(0.5)
    #
    #     return cls._instance

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

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
        self.github_account = Github(account_token)
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
        with open('shared_file.txt', 'w') as file:
            file.write(f"{self.gh_token}\n{self.repo}\n{self.username}\n{self.chat_id}")
        await update.message.reply_text('Saved GitHub data to file')

    async def create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            title = context.args[0]
            body = context.args[1]
            issue = self.github_account.get_user(self.username).get_repo(self.repo).create_issue(
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

    def main_telegram(self):
        print("Starting bot")
        bot = TelegramBot()

        # Commands
        bot.app.add_handler(CommandHandler('start', bot.start_command))
        bot.app.add_handler(CommandHandler('linkghusername', bot.link_github_username_command))
        bot.app.add_handler(CommandHandler('linkghrepo', bot.link_github_repo_command))
        bot.app.add_handler(CommandHandler('linkghtoken', bot.link_github_token_command))
        bot.app.add_handler(CommandHandler('createissue', bot.create_issue))
        bot.app.add_handler(CommandHandler('help', bot.help))
        bot.app.add_handler(CommandHandler('save', bot.save_to_file))

        # Messages
        bot.app.add_handler(MessageHandler(filters.TEXT, bot.handle_message))

        # Error
        bot.app.add_error_handler(bot.error)

        print("Polling...")
        bot.app.run_polling(poll_interval=0.2)
