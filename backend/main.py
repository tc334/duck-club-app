import database.db_mgr

db_name = "duck_hunt_one"

db_mgr = database.db_mgr.DbManager("127.0.0.1", "3306")

db_mgr.create_from_scratch(db_name)
