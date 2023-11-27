import sqlite3
class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def connect(self):
        return sqlite3.connect(self.db_name)

    def setup_db(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_data
                        (chat_id TEXT PRIMARY KEY,
                        repo TEXT,
                        token TEXT,
                        username TEXT)''')

        conn.commit()
        conn.close()

    def insert(self, chat_id, repo, gh_token, username):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT INFO chat_info (chat_id, repo, token, username) VALUES (?, ?, ?, ?)",
                       (chat_id, repo, gh_token, username))
        conn.commit()
        conn.close()

    def get_by_repo(self, repo):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM user_data WHERE repo = {repo}')
        rows = cursor.fetchall()

        return rows

    async def fetch_resource_with_id(self, chat_id, column=None):
        conn = self.connect()
        cursor = conn.cursor()
        if column is None:
            cursor.execute('SELECT * FROM user_data WHERE chat_id = ?', (chat_id, ))
        else:
            cursor.execute(f'SELECT {column} FROM user_data WHERE chat_id = ?', (chat_id, ))
        row = cursor.fetchone()
        conn.close()

        return row