import os
from dotenv import load_dotenv
import redis
from psycopg2.pool import ThreadedConnectionPool
from rq import Worker, Queue, Connection

load_dotenv()

redis_url = os.getenv("REDIS_URL")
db_url = os.getenv("COCKROACH_URL")

#redis_conn = redis.from_url(redis_url)
redis_conn = redis.Redis()

min_conn = 1
max_conn = 5
pool = ThreadedConnectionPool(min_conn, max_conn, db_url)


def process_data(sql_str):
    print(sql_str)
    # my_conn = pool.getconn()
    # with my_conn:
    #     with my_conn.cursor() as cur:
    #         cur.execute(sql_str)
    # pool.putconn(my_conn)


if __name__ == "__main__":
    with Connection(redis_conn):
        print("Setting up Redis")
        queue = Queue(connection=redis_conn)
        worker = Worker(queues=[queue], connection=redis_conn)
        worker.work(with_scheduler=True)
