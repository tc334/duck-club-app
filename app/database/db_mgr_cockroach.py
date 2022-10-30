import datetime
import random
import time
import csv

import psycopg2
import uuid
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from werkzeug.security import generate_password_hash
from typing import Callable

from .tables.schema import schema, secondary_indices, sequences, enums
from .tables.table import Table

STARTUP_KEY = "starting"


def get_index_str(d):
    s = f"CREATE INDEX {d['name']} ON {d['table']} ("
    for item in d['columns']:
        s = s + item + ", "
    s = s[:-2] + ")"
    # print(f"get_index_str:{s}")
    return s


def get_sequence_str(d):
    return f"CREATE SEQUENCE {d}"


def get_enum_str(d):
    ret_val = f"CREATE TYPE enum_{d['name']} AS ENUM{d['values']}"
    return ret_val


def reconnect(f: Callable):
    def wrapper(storage, *args, **kwargs):
        if not storage.connected():
            print(f"DB not connected when {f} called. Attempting to connect")
            if storage.connect():
                storage.select_db_without_execute()
                print(f"Successful reconnection inside reconnect wrapper")
            else:
                print(f"DB connection failed inside reconnect wrapper")

        try:
            return f(storage, *args, **kwargs)
        except psycopg2.Error as e:
            print(f"Error occurred during execute: {e}")
            print(f"pgerror={e.pgerror}, pgcode={e.pgcode}")
            print(f"Closing db connection in response to error")
            storage.close()
            return None

    return wrapper


class DbManagerCockroach:

    def __init__(self):
        self.tables = None

        self.db_url = None
        self.db_name = None
        self.admin_email = None
        self.cache = None

        self.conn = None

    def init_app(self, db_url, admin_email=None, cache=None):
        # capture inputs in member variables
        self.db_url = db_url
        self.admin_email = admin_email
        if cache:
            self.cache = cache

        # load schema from local file
        self.tables = {}
        for key in schema:
            self.tables[key] = Table(schema[key])

        # trying to stagger wsgi workers
        time.sleep(round(random.random()*5))

        # initial server connection
        if self.connect():
            self.print_version()
            self.list_databases(print_on=True)

    # ***********************************************************************************
    # The following functions are DB connection maintenance
    def connected(self):
        return self.conn and self.conn.closed == 0

    def connect(self):
        print(f"Zulu:connect")

        try:
            self.close()
            self.conn = psycopg2.connect(self.db_url)
            return True

        except psycopg2.Error as e:
            print(f"Error connecting to Cockroach DB: {e}")
            return False

    def close(self):
        if self.connected():
            try:
                self.conn.close()
            except Exception:
                pass

        self.conn = None
    # ***********************************************************************************

    #@retry(stop=stop_after_attempt(2), wait=wait_exponential(),
    #       retry=retry_if_exception_type(psycopg2.OperationalError))
    @reconnect
    def execute(self, sql_str, value_tuple=None, expecting_return=False):
        with self.conn:
            with self.conn.cursor() as cur:
                if value_tuple:
                    cur.execute(sql_str, value_tuple)
                else:
                    cur.execute(sql_str)
                if expecting_return:
                    ret_val = cur.fetchall()

        # if self.cache:
        #     self.cache.increment()

        if expecting_return:
            return ret_val
        else:
            return True

    # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    # The methods in this section are intended to be called by an external user
    def dumb(self):
        self.execute(f"SELECT foo FROM bar")

    def print_version(self):
        rows = self.execute("SELECT version()", expecting_return=True)
        if rows:
            for i, row in enumerate(rows):
                print(f"row{i}:{row}")

    def list_databases(self, print_on=False):
        results = self.execute("SELECT datname FROM pg_database", expecting_return=True)
        databases = [item[0] for item in results]
        if print_on:
            print("********************")
            print("List of existing databases in this server:")
            if databases:
                for database in databases:
                    print(database)
            else:
                print("Database listing read error")
            print("********************")
        return databases

    def create_db(self, db_name):
        databases = self.list_databases()
        for db in databases:
            if db[0] == db_name:
                print(f"Error creating database: {db_name} already exists")
                return False
        return self.execute(f"CREATE DATABASE {db_name}")

    def delete_db(self, db_name):
        return self.execute(f"DROP DATABASE IF EXISTS {db_name}")

    def select_db_without_execute(self):
        # this command selects the desired DB without having to go through the execute method in this class, which would
        # get wrapped by the reconnect method and lead to an infinite loop. Instead, we just use the raw SQL without all
        # of the wrapping. This is only intended to be called by reconnect.
        print(f"select_db_without_execute to db name: {self.db_name}")
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(f"USE {self.db_name}")

    def select_db(self, db_name, b_build=False):
        self.db_name = db_name  # saving this for later, when select_db_without_execute will need it
        if db_name not in self.list_databases():
            # the requested DB doesn't exist, so create it
            self.create_db(db_name)
            b_build = True

        if self.execute(f"USE {db_name}"):
            if b_build:
                # newly created DB needs to be built out too
                # this is to prevent multiple wsgi workers from trying to create a DB
                if self.cache:
                    if not self.cache.get_plain(STARTUP_KEY):
                        # nobody else has started up, so this worker will do it & try to suspend others
                        self.cache.add_plain(STARTUP_KEY, "True", expiration_sec=30)
                        return self.build()
                    else:
                        # another node appears to be building this DB now, so skip
                        pass
                else:
                    return self.build()
            else:
                # self.list_tables(print_on=True)
                # self.compare_db()
                return True
        else:
            print(f"Cockroach method select_db failed")
            return False

    def build(self):
        for item in sequences:
            self.execute(get_sequence_str(item))
        for item in enums:
            self.execute(get_enum_str(item))
        for key in self.tables:
            self.create_table(key)
        for item in secondary_indices:
            self.execute(get_index_str(item))
        print(f"Just built-out table schema in database")
        self.list_tables(print_on=True)
        # populate one administrator in the DB
        admin = {
            'first_name': 'TBD',  # admin can go update this through web app
            'last_name': 'TBD',  # admin can go update this through web app
            'email': self.admin_email,
            'public_id': str(uuid.uuid4()),
            'password_hash': generate_password_hash('password', method='sha256'),
            'level': 'administrator',
            'status': 'active',
            'confirmed': 'true',
            'confirmed_on': datetime.datetime.now()
        }
        # self.add_row('users', admin)
        # self.populate_basic_tables()
        return True

    def create_table(self, table_name):
        print(f"Creating table: {table_name}")
        self.execute(f"CREATE TABLE {table_name}({self.tables[table_name].get_schema_string()})")

    def list_tables(self, print_on=False):
        tables = self.execute("SELECT tablename "
                              "FROM pg_catalog.pg_tables "
                              "WHERE schemaname != 'pg_catalog' "
                              "AND schemaname != 'information_schema' "
                              "AND schemaname != 'crdb_internal' "
                              "AND schemaname != 'pg_extension'",
                              expecting_return=True)
        if print_on:
            print("*******************")
            print("List of tables in the database:")
            if tables:
                for table in tables:
                    print(table[0])
            else:
                print("Error reading tables")
            print("*******************")
        # cleanup the output before I return it
        if tables:
            ret_val = [table[0] for table in tables]
            ret_val.sort()
            return ret_val
        else:
            return False

    def write_table_to_csv(self, table_name):
        foo = self.execute(f"SELECT * FROM {table_name}", expecting_return=True)
        with open(f"db_{table_name}.csv", 'w', newline='') as f:
            write = csv.writer(f)
            write.writerows(foo)
        print("write complete")

    def import_from_csv(self, table_name):
        with open(f"db_{table_name}.csv") as f:
            foo = csv.reader(f, delimiter=',')
            values_list = []

            for row in foo:
                for idx, col in enumerate(row):
                    if len(col) < 1:
                        row[idx] = None
                if table_name == "hunts":
                    values = tuple(row + [None, None, None])
                else:
                    values = tuple(row)
                values_list.append(values)

        # print(f"Charlie:{values_list}")
        import psycopg2.extras as extras
        query = f"INSERT INTO {table_name} VALUES %s"
        cursor = self.conn.cursor()
        try:
            extras.execute_values(cursor, query, values_list)
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return 1
        print("execute_values() done")
        cursor.close()

    def import_from_csv_groupings(self):
        table_name = "groupings"
        with open(f"db_{table_name}.csv") as f:
            foo = csv.reader(f, delimiter=',')
            values_list = []
            values_list_participants = []

            for row in foo:
                values = (
                    row[0],   # id
                    row[1],   # hunt_id
                    row[2],   # pond_id
                    row[11],  # harvest_update_time
                    row[12],  # num_hunters
                    row[13],  # num_ducks
                    row[14]   # num_non
                )
                values_list.append(values)

                for slot in range(1, 5):
                    idx_type = slot + 2
                    idx_id = idx_type + 4
                    if row[idx_type] == "member":
                        values_participant = (
                            "member",     # type
                            row[0],       # grouping_id
                            row[idx_id],  # user_id
                        )
                        values_list_participants.append(values_participant)

        # print(f"Charlie:{values_list}")
        import psycopg2.extras as extras
        # Move groupings data
        query = f"INSERT INTO {table_name}(" \
                f"id, " \
                f"hunt_id, " \
                f"pond_id, " \
                f"harvest_update_time, " \
                f"num_hunters, " \
                f"num_ducks, " \
                f"num_non) "\
                f"VALUES %s"
        cursor = self.conn.cursor()
        try:
            extras.execute_values(cursor, query, values_list)
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return 1

        # Move participants data
        query = f"INSERT INTO participants(" \
                f"type, " \
                f"grouping_id, " \
                f"user_id) "\
                f"VALUES %s"
        cursor = self.conn.cursor()
        try:
            extras.execute_values(cursor, query, values_list_participants)
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            self.conn.rollback()
            cursor.close()
            return 1
        print("execute_values() done")
        cursor.close()

    def add_row(self, table_name, row_data_dict):
        col_names, insert_tuple = self.tables[table_name].get_add_row(row_data_dict)

        # format the strings for the command
        value_types = len(insert_tuple) * "%s, "
        my_sql_insert_query = f"INSERT INTO {table_name} ({col_names}) VALUES ({value_types[:-2]}) RETURNING id"

        id = self.execute(my_sql_insert_query, value_tuple=insert_tuple, expecting_return=True)
        if id and len(id) == 1:
            return id[0][0]
        else:
            return id

    def read_custom(self, custom_query):
        return self.execute(custom_query, expecting_return=True)

    def list_columns(self, table_name, print_on=False):
        columns = self.execute(f"SHOW COLUMNS FROM {table_name}", expecting_return=True)
        if print_on:
            print("**********************")
            print(f"List of columns in table {table_name}")
            if columns:
                for col in columns:
                    print(col[0])
            else:
                print(f"Error looking up columns of table {table_name}")
            print("**********************")
        return [col[0] for col in columns]

    def compare_db(self):
        print("Comparing current DB to schema")
        # check to see if the currently selected database matches the schema loaded from local file
        tables_db = self.list_tables()
        # error check. empty list and None/False are different.
        if not tables_db:
            return False
        # if the db has no tables, build it
        if len(tables_db) == 0:
            if not self.build():
                # stop execution of this function if the build fails. Continue otherwise
                return False
            tables_db = self.list_tables()
        tables_local = [key for key in self.tables]
        tables_local.sort()
        if len(tables_db) == len(tables_local):
            for idx in range(len(tables_local)):
                if tables_db[idx] != tables_local[idx]:
                    print(f"Mismatch: {tables_db[idx]} vs {tables_local[idx]}")
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
        print("Local schema and remote DB have matching schema")
        return True

    def read_all(self, table_name, post_fix=""):
        results_tuple = self.execute(f"SELECT * FROM {table_name} {post_fix}", expecting_return=True)
        if results_tuple:
            # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
            results_lod = []  # list of dictionaries (in other words, json)
            names_all = [a_dict["name"] for a_dict in self.tables[table_name].table_cols]
            for row in results_tuple:
                results_lod.append({name: row[col] for col, name in enumerate(names_all)})
            return results_lod
        else:
            return False

    def update_row(self, table_name, id_value, update_dict, id_field="id"):
        set_str = ""
        data_list = []
        for key in update_dict:
            if not key == "id":
                set_str = set_str + key + "=%s,"
                if update_dict[key] is None:
                    data_list.append(None)
                else:
                    data_list.append(str(update_dict[key]))
        # id goes at the end b/c it's associated with the WHERE
        data_list.append(id_value)

        my_sql_insert_query = f"UPDATE {table_name} SET {set_str[:-1]} WHERE {id_field}=%s"

        if self.execute(my_sql_insert_query, value_tuple=tuple(data_list)):
            return True
        else:
            return False

    def update_custom(self, my_sql_insert_query):
        return self.execute(my_sql_insert_query)

    def del_row(self, table_name, row_id, id_field="id"):
        sql_delete_query = f"DELETE FROM {table_name} WHERE {id_field} = '{row_id}'"
        return self.execute(sql_delete_query)

    def nuke_and_rebuild(self, db_name):
        print("Starting nuke & rebuild")
        self.delete_db(db_name)
        print("Delete Complete")
        self.select_db(db_name)
        print("Select Complete")

    def sql_to_dict(self, result, table_name=None, names=None):
        # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema (or override via input)
        if names is None:
            names = [a_dict["name"] for a_dict in self.tables[table_name].table_cols]  # all names
        results_dict = {name: result[0][col] for col, name in enumerate(names)}
        return results_dict

    # convert list(len=#rows) of tuples(len=#cols) to dictionary using keys from schema
    # if you pass the optional table-name parame in, it will automatically overwrite names_all with all columns of the
    # table
    def format_dict(self, names_all, results_tuple, table_name=None):
        results_lod = []  # list of dictionaries (in other words, json)
        if table_name is not None:
            names_all = [a_dict["name"] for a_dict in self.tables[table_name].table_cols]
        for row in results_tuple:
            results_lod.append({name: row[col] for col, name in enumerate(names_all)})
        return results_lod
    # $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

    def populate_basic_tables(self):
        self.add_row("properties", {'name': 'Oak Meadows', 'region': 'Southern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Oak Meadows'")[0][0]
        self.add_row("ponds", {'name': 'Appelt', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Benelli', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Castle', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Lodge', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Middle', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Remington', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Road', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Swale', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Winchester', 'property_id': property_id})

        self.add_row("properties", {'name': 'Harrison', 'region': 'Southern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Harrison'")[0][0]
        self.add_row("ponds", {'name': 'Blue Wing', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Green Wing', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Shoveler', 'property_id': property_id})

        self.add_row("properties", {'name': 'Hughson Lakes', 'region': 'Southern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Hughson Lakes'")[0][0]
        self.add_row("ponds", {'name': 'Andi', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Herlin', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Stu', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Thunder', 'property_id': property_id})

        self.add_row("properties", {'name': 'Radley', 'region': 'Northern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Radley'")[0][0]
        self.add_row("ponds", {'name': 'Gadwall', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Mallard', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Pintail', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Wigeon', 'property_id': property_id})

        self.add_row("properties", {'name': 'Blue Creek', 'region': 'Northern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Blue Creek'")[0][0]
        self.add_row("ponds", {'name': 'Brooks', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Crawfish North', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Crawfish East', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Crawfish West', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Forrest West', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Forrest Middle', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Forrest East', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Hunter NW', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Hunter NE', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Hunter M', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Hunter SE', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Hunter SW', 'property_id': property_id})

        self.add_row("properties", {'name': 'Northern', 'region': 'Northern'})
        property_id = self.read_custom("SELECT id FROM properties WHERE name='Northern'")[0][0]
        self.add_row("ponds", {'name': 'Bree', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Bo', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Nelly', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Northern Roost', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Southern Roost', 'property_id': property_id})
        self.add_row("ponds", {'name': 'Toby', 'property_id': property_id})

        self.add_row("birds", {'name': 'Blue Winged Teal', 'type': 'duck'})
        self.add_row("birds", {'name': 'Green Winged Teal', 'type': 'duck'})
        self.add_row("birds", {'name': 'Pintail', 'type': 'duck'})
        self.add_row("birds", {'name': 'Wigeon', 'type': 'duck'})
        self.add_row("birds", {'name': 'Gadwall', 'type': 'duck'})
        self.add_row("birds", {'name': 'Mallard', 'type': 'duck'})
        self.add_row("birds", {'name': 'Northern Shoveler', 'type': 'duck'})
        self.add_row("birds", {'name': 'Wood', 'type': 'duck'})
        self.add_row("birds", {'name': 'Mottled', 'type': 'duck'})
        self.add_row("birds", {'name': 'Ruddy', 'type': 'duck'})
        self.add_row("birds", {'name': 'Red Head', 'type': 'duck'})
        self.add_row("birds", {'name': 'Canvasback', 'type': 'duck'})
        self.add_row("birds", {'name': 'Lesser Scaup', 'type': 'duck'})
        self.add_row("birds", {'name': 'Greater Scaup', 'type': 'duck'})
        self.add_row("birds", {'name': 'Snow Goose', 'type': 'goose'})
        self.add_row("birds", {'name': 'Speckled Belly', 'type': 'goose'})
        self.add_row("birds", {'name': 'Sand Hill', 'type': 'crane'})
        self.add_row("birds", {'name': 'Blue Goose', 'type': 'goose'})
        self.add_row("birds", {'name': 'Canadian', 'type': 'goose'})

        return True
