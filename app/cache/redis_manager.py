import redis
import sys
import json
import functools

DISABLE_REDIS = False


class RedisManager:
    def __init__(self):
        self.r = None

        self.host = None
        self.port = None
        self.username = None
        self.password = None

    def init_app(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

        if not DISABLE_REDIS:
            self.connect()

            self.wipe_cache()

            # initialize counter for # times database is hit
            self.r.set("db_count", 0)

    def increment(self):
        if not DISABLE_REDIS:
            self.r.incr("db_count")

    def connect(self):
        try:
            self.r = redis.Redis(host=self.host,
                                 port=self.port)
            self.r.ping()
            print(f"RedisManager connected to {self.host}:{self.port}")
            return True

        except redis.ConnectionError as e:
            print(f"RedisManager connection error: {e}")
            return False

        except:
            e = sys.exc_info()[0]
            print(f"Unknown Redis connection error: {e}")
            return False

    def transaction_wrapper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if DISABLE_REDIS:
                return []
            # Before trying to execute func, check connection
            self_ish = args[0]
            if self_ish.r:
                try:
                    self_ish.r.ping()
                except redis.ConnectionError as e:
                    print(f"Caught redis connection error: {e}")
                    print(f"making one attempt to reconnect")
                    if self_ish.connect():
                        pass
                    else:
                        print("reconnect try failed. Giving up")
                        return []  # this mimics the return value when there wasn't a key in the redis DB
                except redis.RedisError as e:
                    print(f"Unknown RedisError in wrapper before func call: {e}")
                    return []  # this mimics the return value when there wasn't a key in the redis DB
            else:
                print(f"RedisManager is still 'None'")

            # Now try to execute func
            try:
                ret_val = func(*args, **kwargs)
                return ret_val
            except redis.RedisError as e:
                print(f"Error in RedisManager method {func}: {e}")
                return []  # this mimics the return value when there wasn't a key in the redis DB
            #except:
            #    e = sys.exc_info()[0]
            #    print(f"Non-redis error during execution of RedisManager method {func}, with args {args}: {e}")
            #    return []  # this mimics the return value when there wasn't a key in the redis DB
        return wrapper

    @transaction_wrapper
    def wipe_cache(self):
        self.r.flushall()
        print("RedisManager just flushed all keys from all databases")

    @transaction_wrapper
    def add(self, prefix, data_in, expiration_sec):
        expiration_sec = 30
        if type(data_in) is dict:
            # special case where there isn't a list; there is just one dictionary
            self.r.setex(f"{prefix}:count", expiration_sec, -1)
            self.r.setex(f"{prefix}", expiration_sec, json.dumps(data_in))
            return
        if type(data_in) in (int, str, float):
            # special case where there isn't a list; there is just one value
            self.r.setex(f"{prefix}:count", expiration_sec, -2)
            self.r.setex(f"{prefix}", expiration_sec, data_in)
            return
        # nominal case: input is a list of dictionaries
        self.r.setex(f"{prefix}:count", expiration_sec, len(data_in))
        for i, e in enumerate(data_in):
            self.r.setex(f"{prefix}:{i}", expiration_sec, json.dumps(e))

    @transaction_wrapper
    def get(self, prefix):
        # no data in redis for this prefix yet
        count = self.r.get(f"{prefix}:count")
        if count is None:
            return []
        count = int(count)
        # special case for just a single dictionary, not a list of dictionaries
        if count == -1:
            temp = self.r.get(prefix)
            if not temp:
                # this indicates a cache miss
                return []
            return json.loads(temp)
        # special case for just a single value
        if count == -2:
            return self.r.get(prefix)
        # nominal
        list_of_dicts = []
        print(f"debug. count={count}. prefix={prefix}")
        for i in range(count):
            list_of_dicts.append(json.loads(self.r.get(f"{prefix}:{i}")))
        print(f"Cache hit! Prefix={prefix}")
        return list_of_dicts

    @transaction_wrapper
    def delete(self, prefix):
        keys = self.r.keys(f"{prefix}:*")
        if keys:
            print(f"debug. keys={keys}")
            self.r.delete(*keys)
