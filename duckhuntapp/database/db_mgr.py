import mysql.connector
from .tables.schema import schema
from .tables.table import Table


class DbManager:

    def __init__(self):
        self.db = None
        self.my_cursor = None
        self.schema = None
        self.tables = None

    def init_app(self, host, port, user_name, password):

        print(f"host:{host}, port:{port}, user_name:{user_name}, p{password}")

        self.db = mysql.connector.connect(
            host=host,
            port=port,
            user=user_name,
            passwd=password
        )

        # connect to MySQL server
        self.my_cursor = self.db.cursor()
        print(f"Successful connection to MySQL server at {host}:{port}")
        self.list_databases(True)

        # load schema from local file
        self.schema = schema
        self.tables = {}
        for key in self.schema:
            self.tables[key] = Table(self.schema[key])

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

    def compare_db(self):
        # check to see if the currently selected database matches the schema loaded from local file
        tables_db = self.list_tables()
        tables_local = [key for key in self.tables]
        tables_local.sort()
        if len(tables_db) == len(tables_local):
            for idx in range(len(tables_local)):
                if tables_db[idx][0] != tables_local[idx]:
                    print(f"Mismatch: {tables_db[idx][0]} vs {tables_local[idx]}")
                    return False
        else:
            print("table lengths don't match")
            return False
        # if you made it here that means the table names match. now compare columns in each table
        for idx_table in range(len(tables_local)):
            cols_db = self.list_columns(tables_local[idx_table])
            cols_db.sort()
            cols_local = self.tables[tables_local[idx_table]].get_names_list()
            if not cols_db == cols_local:
                print(f"Table {tables_local[idx_table]} does not have matching columns")
                return False
        # if you made it here, there is a full match
        return True

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

    def list_columns(self, table_name, print_on=False):
        self.my_cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = self.my_cursor.fetchall()
        if print_on:
            print("**********************")
            print(f"List of columns in table {table_name}")
            for col in columns:
                print(col[0])
            print("**********************")
        return [col[0] for col in columns]

    def create_table(self, table_name):
        self.my_cursor.execute(f"CREATE TABLE {table_name}({self.tables[table_name].get_schema_string()})")

    def create_from_scratch(self, db_name):
        self.delete_db(db_name)
        self.create_db(db_name)
        self.select_db(db_name)
        for key in self.tables:
            self.create_table(key)
        print(f"Created database {db_name}")
        self.list_tables(print_on=True)

    def connect_to_existing(self, db_name):
        self.select_db(db_name)
        print(f"Selected database {db_name}")
        if self.compare_db():
            print(f"{db_name} matches the local schema file")

    def add_row(self, table_name, row_data_dict):
        col_names, insert_tuple = self.tables[table_name].get_add_row(row_data_dict)

        # format the strings for the command
        value_types = len(insert_tuple) * "%s, "
        my_sql_insert_query = f"INSERT INTO {table_name} ({col_names}) VALUES ({value_types[:-2]}) "

        try:
            self.my_cursor.execute(my_sql_insert_query, insert_tuple)
            self.db.commit()
        except mysql.connector.Error as error:
            print("Failed to add record to table: {}".format(error))

    def read_all(self, table_name):
        s = f"SELECT * FROM {table_name}"
        try:
            self.my_cursor.execute(s)
            results_tuple = self.my_cursor.fetchall()
        except mysql.connector.Error as error:
            print("Failed to read all from table: {}".format(error))
            return None
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
        results_lod = []  # list of dictionaries (in other words, json)
        names_all = [a_dict["name"] for a_dict in self.tables[table_name].table_cols]
        for row in results_tuple:
            results_lod.append({name: row[col] for col, name in enumerate(names_all)})
        return results_lod

    def read_custom(self, custom_query):
        try:
            self.my_cursor.execute(custom_query)
            results = self.my_cursor.fetchall()
        except mysql.connector.Error as error:
            print("Failed to execute custom query: {}".format(error))
            return None
        return results

    def update_row(self, table_name, update_dict):
        set_str = ""
        data_list = []
        for key in update_dict:
            if not key == "id":
                set_str = set_str + key + "=%s,"
                data_list.append(update_dict[key])
        # id goes at the end b/c it's associated with the WHERE
        data_list.append(update_dict["id"])

        my_sql_insert_query = f"UPDATE {table_name} SET {set_str} WHERE id=%s"

        try:
            self.my_cursor.execute(my_sql_insert_query, tuple(data_list))
            self.db.commit()
        except mysql.connector.Error as error:
            print("Failed to update record: {}".format(error))

    def del_row(self, table_name, row_id):
        sql_delete_query = f"DELETE from {table_name} where id = {row_id}"
        try:
            self.my_cursor.execute(sql_delete_query)
            self.db.commit()
            print('number of rows deleted', self.my_cursor.rowcount)

        except mysql.connector.Error as error:
            print("Failed to delete record from table: {}".format(error))