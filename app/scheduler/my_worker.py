import os
import sys

import datetime as dt

from dotenv import load_dotenv
import redis
from psycopg2.pool import ThreadedConnectionPool
from rq import Worker, Queue, Connection
from urllib.parse import urlparse
from app.cache.redis_manager import PRE_PREFIX

load_dotenv()

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# REDIS
url = urlparse(os.getenv("REDIS_URL"))
redis_ipaddr = url.hostname
redis_port = url.port
redis_user = url.username
redis_password = url.password

try:
    redis_conn = redis.Redis(host=redis_ipaddr,
                             port=redis_port,
                             username=redis_user,
                             password=redis_password,
                             health_check_interval=10,
                             retry_on_timeout=True,
                             socket_keepalive=True)
    print(f"RedisManager ping response: {redis_conn.ping()}")
    print(f"RedisManager connected to {redis_ipaddr}:{redis_port}")

except redis.ConnectionError as e:
    print(f"RedisManager connection error: {e}")
    redis_conn = None

except:
    e = sys.exc_info()[0]
    print(f"Unknown Redis connection error: {e}")
    redis_conn = None
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# POSTGRESQL
db_url = os.getenv("COCKROACH_URL_TEST")
min_conn = 1
max_conn = 3
pool = ThreadedConnectionPool(min_conn, max_conn, db_url)
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


def execute_auto_progress(sql_str, hunt_id):
    print(f"RQ Worker Executing SQL command: {sql_str}")
    now = dt.datetime.now()
    print(f"The current time is {now.strftime('%Y-%m-%d %H:%M:%S')}")
    my_conn = pool.getconn()
    with my_conn:
        with my_conn.cursor() as cur:
            if type(sql_str) == tuple:
                for s in sql_str:
                    cur.execute(s)
            else:
                cur.execute(sql_str)
    pool.putconn(my_conn)

    # clear caches that are invalidated by a hunt status change
    prefixes = ["echo", "nov", "sierra", "tango"]
    for prefix in prefixes:
        for k in redis_conn.scan_iter(f"{PRE_PREFIX}:{prefix}*"):
            redis_conn.delete(k)

    # counting of hunters is supposed to happen when transitioning to hunt_open or hunt_closed
    redis_conn.sadd(f"{PRE_PREFIX}:hunts_needing_update", hunt_id)


if __name__ == "__main__":
    if redis_conn is not None:
        with Connection(redis_conn):
            print("Setting up Redis")
            queue = Queue(connection=redis_conn)
            worker = Worker(queues=[queue], connection=redis_conn)
            worker.work(with_scheduler=True)
    else:
        print("Error in worker. Redis connection not established")
