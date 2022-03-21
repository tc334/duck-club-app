from database.db_mgr import DbManager

db_name = "duck_hunt_one"

db_mgr = DbManager("127.0.0.1", "3306")

db_mgr.create_from_scratch(db_name)
#db_mgr.connect_to_existing(db_name)

# Add rows to each table
db_mgr.add_row("birds", {"name": "Mallard", "type": "duck"})
db_mgr.add_row("birds", {"name": "Pintail", "type": "duck"})

db_mgr.add_row("properties", {"name": "Harrison"})
db_mgr.add_row("properties", {"name": "Blue Creek"})
db_mgr.add_row("properties", {"name": "Radley"})

db_mgr.add_row("ponds", {"name": "Green Wing", "property_id": 1, "status": "open"})
db_mgr.add_row("ponds", {"name": "Forrest West", "property_id": 2})

db_mgr.add_row("users", {"first_name": "Tegan", "last_name": "Counts", "level": "administrator"})
db_mgr.add_row("users", {"first_name": "Craig", "last_name": "Jones", "level": "manager"})
db_mgr.add_row("users", {"first_name": "Aaron", "last_name": "Pyle"})
db_mgr.add_row("users", {"first_name": "Todd", "last_name": "Steele", "level": "owner"})
db_mgr.add_row("users", {"first_name": "Hunter", "last_name": "Steele", "level": "owner"})
db_mgr.add_row("users", {"first_name": "Forrest", "last_name": "Steele", "level": "owner"})

db_mgr.add_row("hunts", {"hunt_date": "2022-03-21"})

db_mgr.add_row("groupings", {
    "hunt_id": 1,  # 2022-03-21
    "pond_id": 2,  # Forrest West
    "slot1_type": "member",
    "slot1_id": 4,  # Todd
    "slot2_type": "member",
    "slot2_id": 5,  # Hunter
    "slot3_type": "member",
    "slot3_id": 6  # Forrest
})
db_mgr.add_row("groupings", {
    "hunt_id": 1,  # 2022-03-21
    "pond_id": 1,  # Green Wing
    "slot1_type": "member",
    "slot1_id": 1,  # Tegan
    "slot2_type": "member",
    "slot2_id": 2,  # Craig
    "slot3_type": "member",
    "slot3_id": 3  # Aaron
})

db_mgr.add_row("harvest", {"group_id": 1, "count": 2, "bird_id": 1})  # Steele group shot 2 Mallards
db_mgr.add_row("harvest", {"group_id": 1, "count": 3, "bird_id": 2})  # Steele group shot 3 Pintail
db_mgr.add_row("harvest", {"group_id": 2, "count": 4, "bird_id": 1})  # Counts group shot 4 Mallards
db_mgr.add_row("harvest", {"group_id": 2, "count": 1, "bird_id": 2})  # Counts group shot 1 Pintail

# Get all entries from a table (properties)
print(db_mgr.read_all("ponds"))

# Delete 1 row from a table
db_mgr.del_row("harvest", 4)  # Counts group shot 1 Pintail

# Update 1 row from 1 table
db_mgr.update_row("harvest", {"id": 1, "count": 6})
