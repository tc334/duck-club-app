import mysql.connector


class DbManager:

    def __init__(self, host, port):

        self.db = mysql.connector.connect(
            host=host,
            port=port,
            user="root",
            passwd="C@rr0t01"
        )

        self.my_cursor = self.db.cursor()

        print(f"Successful connection to MySQL server at {host}:{port}")
        self.list_databases(True)

    def list_databases(self, print_on=False):
        self.my_cursor.execute("SHOW DATABASES")
        databases = self.my_cursor.fetchall()
        if print_on:
            print("********************")
            print("List of existing databases in this server:")
            for database in databases:
                print(database[0])
            print("********************")
        return databases

    def create_db(self, db_name):
        databases = self.list_databases()
        for db in databases:
            if db[0] == db_name:
                print(f"Error creating database: {db_name} already exists")
                return False
        self.my_cursor.execute(f"CREATE DATABASE {db_name}")
        return True

    def delete_db(self, db_name):
        self.my_cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")

    def select_db(self, db_name):
        self.my_cursor.execute(f"USE {db_name}")

    def list_tables(self, print_on=False):
        self.my_cursor.execute("SHOW TABLES")
        tables = self.my_cursor.fetchall()
        if print_on:
            print("*******************")
            print("List of tables in the database:")
            for table in tables:
                print(table[0])
            print("*******************")
        return tables

    def create_table(self, table_name):
        with open("database/schema/" + table_name + ".txt") as reader:
            schema = reader.read()
        self.my_cursor.execute(f"CREATE TABLE {table_name}({schema})")

    def create_from_scratch(self, db_name):
        self.delete_db(db_name)
        self.create_db(db_name)
        self.select_db(db_name)
        self.create_table("users")
        self.create_table("groupings")
        self.create_table("hunts")
        self.create_table("properties")
        self.create_table("ponds")
        self.create_table("birds")
        self.create_table("harvest")
        self.list_tables(print_on=True)
