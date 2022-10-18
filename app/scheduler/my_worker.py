import os
import sys

from dotenv import load_dotenv
import redis
from psycopg2.pool import ThreadedConnectionPool
from rq import Worker, Queue, Connection
from urllib.parse import urlparse

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


def execute_sql(sql_str):
    print(f"RQ Worker Executing SQL command: {sql_str}")
    my_conn = pool.getconn()
    with my_conn:
        with my_conn.cursor() as cur:
            cur.execute(sql_str)
    pool.putconn(my_conn)


if __name__ == "__main__":
    if redis_conn is not None:
        with Connection(redis_conn):
            print("Setting up Redis")
            queue = Queue(connection=redis_conn)
            worker = Worker(queues=[queue], connection=redis_conn)
            worker.work(with_scheduler=True)
    else:
        print("Error in worker. Redis connection not established")
