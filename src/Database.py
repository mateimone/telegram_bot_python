import sqlite3


class Database:
    def __init__(self, db_name):
        self.db_name = db_name

    def connect(self):
        return sqlite3.connect(self.db_name)

    def setup_db(self):
        """
        Creates the user_data database if it doesn't exist already
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_data
                        (chat_id TEXT PRIMARY KEY,
                        repo TEXT,
                        token TEXT,
                        username TEXT)''')

        conn.commit()
        conn.close()

    async def fetch_resource_with_id(self, chat_id, column=None):
        """
        Returns the whole entry with a given id if column is not specified.
        Returns only the cell of the entry with the given id and the specified column, otherwise.
        :param chat_id: the chat id of the user
        :param column: either None or the name of a column in the database
        :return: either the whole entry or just a single cell of it
        """
        conn = self.connect()
        cursor = conn.cursor()
        if column is None:
            cursor.execute('SELECT * FROM user_data WHERE chat_id = ?', (chat_id, ))
        else:
            cursor.execute(f'SELECT {column} FROM user_data WHERE chat_id = ?', (chat_id, ))
        row = cursor.fetchone()
        conn.close()

        return row

    def get_chats_by_repo(self, repo: str):
        """
        Get the chat id of every user with the given repo.
        Useful when sending updates to all users watching a repository.
        :param repo: the repository which had an event update
        :return: the list of chat ids
        """
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT chat_id FROM user_data WHERE repo = ?', (repo,))

        data_list = cursor.fetchall()
        chat_id_list = [data[0] for data in data_list]
        conn.close()

        return chat_id_list

    async def update_row_with_id(self, value, column_name, chat_id, data):
        """
        Updates a certain cell of the entry with a given id in a database.
        :param value: value to be put in the cell
        :param column_name: the name of the cell that is updated
        :param chat_id: the id of the chat and of the corresponding entry
        :param data: user data
        :return: True if the update was successful, False otherwise
        """
        if data is None:
            return False

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE user_data SET {column_name} = ? WHERE chat_id = ?', (value, chat_id))
        conn.commit()
        conn.close()

        return True
