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

    def __init__(self):
        super().__init__()
        self.repo: str | None = ''
        self.username: str | None = ''
        self.app: Application = Application.builder().token(TelegramBot.TOKEN).build()
        self.chat_id: str = ''
        self.gh_token = ''
        self.lock = Lock()

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
        self.chat_id = update.effective_chat.id
        self.add_data_to_file(str(self.chat_id), 0)
        await update.message.reply_text('Hello! Thanks for chatting with me!')

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help = '/start - starts the conversation and registers the conversation ID\n'
        help += '/help - display useful information about the commands\n'
        help += '/linkghrepo param - links the bot to the repository name given as param\n'
        help += '/linkghtoken param - links the bot to the GitHub token given as param\n'
        help += '/linkghusername param - links the bot to the username given as param\n'
        help += '/auto_set_webhooks param - automatically sets webhooks for updates on ngrok\'s web interface port\n'
        help += '/createissue param1 param2 - creates an issue with param1 as title and param2 as body\n'

        await update.message.reply_text(help)

    async def link_github_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        account_token = ' '.join(context.args)
        self.gh_token = account_token
        self.add_data_to_file(account_token, 2)
        await update.message.reply_text('GitHub account token updated')

    async def link_github_repo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        repo = ' '.join(context.args)
        self.repo = repo
        self.add_data_to_file(repo, 1)
        await update.message.reply_text('Repository updated')

    async def link_github_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = ' '.join(context.args)
        self.username = username
        self.add_data_to_file(username, 3)
        await update.message.reply_text('Name updated')

    async def create_issue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        with self.lock:
            title = context.args[0]
            body = context.args[1]
            gh = Github(self.gh_token).get_user(self.username).get_repo(self.repo)

            issue = gh.create_issue(
                title=title,
                body=body
            )

            await update.message.reply_text(f'Issue created at {issue.html_url}')

    def add_data_to_file(self, data: str, pos: int):
        lines = []
        with open('src/user_data.txt', 'r') as file:
            lines = file.readlines()
            lines[pos] = data + '\n'

        with open('src/user_data.txt', 'w') as file:
            file.writelines(lines)

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
        if self.gh_token == '' or self.username == '' or self.repo == '' or self.chat_id == '':
            await update.message.reply_text(
                f'The data you have provided is incomplete.\nGitHub repo - {self.repo}\nGitHub token - {self.gh_token}'
                f'\nGitHub username - {self.username}\nChat ID - {self.chat_id}\n'
                f'If somehow the Chat ID was not saved, you won\'t receive notifications. Run the /start command again.'
                f'\nWebhooks were NOT set.')
            return

        if len(context.args) == 0:
            await update.message.reply_text('The command cannot be used without a given port.')
            return
        port = context.args[0]

        repository = Github(self.gh_token).get_user(self.username).get_repo(self.repo)

        events = ["create", "delete", "issues", "issue_comment", "commit_comment", "milestone", "label", "push",
                  "pull_request", "pull_request_review", "pull_request_review_comment", "team_add"]
        hooks = repository.get_hooks()
        for hook in hooks:
            if hook.events[0] in events and len(hook.events) == 1:
                hook.delete()  # delete previous hooks

        result = await Ngrok.get_ngrok_url(port)
        config = {
            "url": result,
            "content_type": "json"
        }
        self.push_hooks(repository, config, result + "/branch/create", ["create"])
        self.push_hooks(repository, config, result + "/branch/delete", ["delete"])
        self.push_hooks(repository, config, result + "/issues", ["issues"])
        self.push_hooks(repository, config, result + "/issue/comment", ["issue_comment"])
        self.push_hooks(repository, config, result + "/commit/comment", ["commit_comment"])
        self.push_hooks(repository, config, result + "/milestone", ["milestone"])
        self.push_hooks(repository, config, result + "/label", ["label"])
        self.push_hooks(repository, config, result + "/push", ["push"])
        self.push_hooks(repository, config, result + "/pull_request", ["pull_request"])
        self.push_hooks(repository, config, result + "/pull_request/review", ["pull_request_review"])
        self.push_hooks(repository, config, result + "/pull_request/review/comment", ["pull_request_review_comment"])
        self.push_hooks(repository, config, result + "/team_add", ["team_add"])
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

    def main_telegram(self):
        print("Starting bot")

        # Commands
        self.app.add_handler(CommandHandler('start', self.start_command))
        self.app.add_handler(CommandHandler('linkghusername', self.link_github_username_command))
        self.app.add_handler(CommandHandler('linkghrepo', self.link_github_repo_command))
        self.app.add_handler(CommandHandler('linkghtoken', self.link_github_token_command))
        self.app.add_handler(CommandHandler('createissue', self.create_issue))
        self.app.add_handler(CommandHandler('help', self.help))
        self.app.add_handler(CommandHandler('auto_set_webhooks', self.set_webhooks))

        # Messages
        self.app.add_handler(MessageHandler(filters.TEXT, self.handle_message))

        # Error
        self.app.add_error_handler(self.error)
        print(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.txt'))
        if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_data.txt')):
            with open('src/user_data.txt', 'r') as file:
                tokens = file.read().split('\n')
                self.chat_id = tokens[0]
                self.repo = tokens[1]
                self.gh_token = tokens[2]
                self.username = tokens[3]
                file.close()
        else:
            with open('src/user_data.txt', 'w') as file:
                file.write('\n\n\n\n')
                file.close()

        TelegramBot._instance = self

        print("Polling...")
        self.app.run_polling(poll_interval=0.2)
