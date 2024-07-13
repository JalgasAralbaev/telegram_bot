import sqlite3


class Database:
    def __init__(self, path_to_db="main.db"):
        self.path_to_db = path_to_db

    @property
    def connection(self):
        return sqlite3.connect(self.path_to_db)

    def execute(self, sql: str, parameters: tuple = None, fetchone=False, fetchall=False, commit=False):
        if not parameters:
            parameters = ()
        connection = self.connection
        connection.set_trace_callback(logger)
        cursor = connection.cursor()
        data = None
        cursor.execute(sql, parameters)

        if commit:
            connection.commit()
        if fetchall:
            data = cursor.fetchall()
        if fetchone:
            data = cursor.fetchone()
        connection.close()
        return data

    def create_table_users(self):
        sql = """
        CREATE TABLE Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name varchar(255) NOT NULL,
            mahalla varchar(255) NOT NULL,
            img varchar(255) NOT NULL,
            vote INTEGER NOT NULL
            );
        """

        self.execute(sql, commit=True)

    def create_table_voters(self):
        sql = """
        CREATE TABLE Voters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name varchar(255) NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL
            );
        """

        self.execute(sql, commit=True)

    def create_table_channel1(self):
        sql = """
        CREATE TABLE channel1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name varchar(255) NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL
            );
        """

        self.execute(sql, commit=True)

    def create_table_channel2(self):
        sql = """
        CREATE TABLE channel2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name varchar(255) NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL
            );
        """

        self.execute(sql, commit=True)

    def create_table_channel3(self):
        sql = """
        CREATE TABLE channel3 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name varchar(255) NOT NULL,
            telegram_id INTEGER UNIQUE NOT NULL
            );
        """

        self.execute(sql, commit=True)



    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join([
            f"{item} = ?" for item in parameters
        ])
        return sql, tuple(parameters.values())

    def add_user(self, full_name: str, mahalla: str, img: str):
        # SQL_EXAMPLE = "INSERT INTO Users(id, full_name) VALUES(1, 'John', 'John@gmail.com')"

        sql = """
        INSERT INTO Users(full_name, mahalla, img, vote) VALUES(?, ?, ?, 0)
        """
        self.execute(sql, parameters=(full_name, mahalla, img), commit=True)

    def add_voter(self, full_name: str, telegram_id: int):
        # SQL_EXAMPLE = "INSERT INTO Users(id, full_name) VALUES(1, 'John', 'John@gmail.com')"

        sql = """
        INSERT INTO Voters(full_name, telegram_id) VALUES(?, ?)
        """
        self.execute(sql, parameters=(full_name, telegram_id), commit=True)

    def add_subscriber(self, channel: str, full_name: str, telegram_id: int):
        # SQL_EXAMPLE = "INSERT INTO Users(id, full_name) VALUES(1, 'John', 'John@gmail.com')"

        sql = f"""
        INSERT INTO {channel} (full_name, telegram_id) VALUES(?, ?)
        """
        self.execute(sql, parameters=(full_name, telegram_id), commit=True)

    def check_voter(self, telegram_id: int):
        sql = """
        SELECT EXISTS (
        SELECT 1
        FROM Voters
        WHERE telegram_id = ?)
        """
        return self.execute(sql, parameters=(telegram_id,), fetchone=True)

    def check_subscribe(self, channel, telegram_id: int):
        sql = f"""
        SELECT EXISTS (
        SELECT 1
        FROM {channel}
        WHERE telegram_id = ?)
        """
        return self.execute(sql, parameters=(telegram_id,), fetchone=True)

    def delete_subscriber(self, channel: str, telegram_id: int):
        # SQL_EXAMPLE = "INSERT INTO Users(id, full_name) VALUES(1, 'John', 'John@gmail.com')"

        sql = f"""
        DELETE FROM {channel} WHERE telegram_id = ?
        """
        self.execute(sql, parameters=(telegram_id,), commit=True)

    def select_all_users(self, page):
        sql = """
        SELECT * FROM Users ORDER BY id LIMIT 10 OFFSET ?
        """
        return self.execute(sql, (page,), fetchall=True)

    def get_rank(self):
        return self.execute("SELECT id, full_name, vote, RANK() OVER (ORDER BY vote DESC) AS Rank FROM Users", fetchall=True)

    def select_allow_users(self):
        return self.execute("SELECT * FROM Users ORDER BY vote DESC;", fetchall=True)

    def select_user(self, ident: int):
        sql = """
        SELECT * FROM Users WHERE id = ?
        """
        return self.execute(sql, (ident,), fetchone=True)

    # def select_user(self, **kwargs):
    #     # SQL_EXAMPLE = "SELECT * FROM Users where id=1 AND Name='John'"
    #     sql = "SELECT * FROM Users WHERE "
    #     sql, parameters = self.format_args(sql, kwargs)
    #
    #     return self.execute(sql, parameters=parameters, fetchone=True)

    def count_users(self):
        return self.execute("SELECT COUNT(*) FROM Users;", fetchone=True)

    def update_user_vote(self, ident: int):
        # SQL_EXAMPLE = "UPDATE Users SET email=mail@gmail.com WHERE id=12345"

        sql = f"""
        UPDATE Users SET vote = vote + 1 WHERE id=?
        """
        return self.execute(sql, parameters=(ident,), commit=True)

    def delete_users(self, channel):
        self.execute(f"DELETE FROM {channel} WHERE TRUE", commit=True)


def logger(statement):
    print(f"""
_____________________________________________________        
Executing: 
{statement}
_____________________________________________________
""")

