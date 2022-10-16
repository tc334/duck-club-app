from app.database.db_mgr_cockroach import DbManagerCockroach
from app.cache.redis_manager import RedisManager
import json

full_url = "postgresql://home:5Y-1Wz9qKCOjLgEG9CR34g@free-tier14.aws-us-east-1.cockroachlabs.cloud:26257/defaultdb?" \
           "sslmode=verify-full&sslrootcert=app/certs/root.crt&options=--cluster%3Dsugar-puffin-4134"

print("start")
db = DbManagerCockroach()
db.init_app(full_url, "tegan.counts@gmail.com")

# Create fresh DB from schema
db_name = "duck_club_app_debug_2"
db.delete_db(db_name)
db.select_db(db_name)

# **********************************************************************************************************************
# Load from local
tables_1 = ["birds", "hunts", "users", "properties", "ponds"]
for t in tables_1:
    db.import_from_csv(t)

db.import_from_csv_groupings()

tables_2 = ["harvest"]
for t in tables_2:
    db.import_from_csv(t)
# **********************************************************************************************************************



# **********************************************************************************************************************
# update sequences
db.read_custom(f"SELECT setval('seq_birds_id',     21, false);")
db.read_custom(f"SELECT setval('seq_hunts_id',      9, false);")
db.read_custom(f"SELECT setval('seq_users_id',     29, false);")
db.read_custom(f"SELECT setval('seq_properties_id', 7, false);")
db.read_custom(f"SELECT setval('seq_ponds_id',     42, false);")
db.read_custom(f"SELECT setval('seq_groupings_id', 89, false);")
# **********************************************************************************************************************

db.close()
print("close")
