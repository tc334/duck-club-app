import redis
import sys
import json
import functools

DISABLE_REDIS = False
PRE_PREFIX = "foo"


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

    def connect(self):
        try:
            self.r = redis.Redis(host=self.host,
                                 port=self.port,
                                 username=self.username,
                                 password=self.password)
            print(f"RedisManager ping response: {self.r.ping()}")
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
            # except:
            #     e = sys.exc_info()[0]
            #     print(f"Non-redis error during execution of RedisManager method {func}, with args {args}: {e}")
            #     return []  # this mimics the return value when there wasn't a key in the redis DB
        return wrapper

    @transaction_wrapper
    def increment(self):
        if not DISABLE_REDIS:
            self.r.incr(f"{PRE_PREFIX}:db_count")

    @transaction_wrapper
    def wipe_cache(self):
        # self.r.flushall()  # old way
        keys = self.r.keys(f"{PRE_PREFIX}:*")
        if keys:
            # print(f"Redis debug. Deleting keys={keys}")
            self.r.delete(*keys)
        print("RedisManager just flushed all keys from all databases")

    @transaction_wrapper
    def add(self, prefix, data_in, expiration_sec):
        if type(data_in) is dict:
            # special case where there isn't a list; there is just one dictionary
            self.r.setex(f"{PRE_PREFIX}:{prefix}:count", expiration_sec, -1)
            self.r.setex(f"{PRE_PREFIX}:{prefix}", expiration_sec, json.dumps(data_in, default=str))
            return
        if type(data_in) in (int, str, float):
            # special case where there isn't a list; there is just one value
            self.r.setex(f"{PRE_PREFIX}:{prefix}:count", expiration_sec, -2)
            self.r.setex(f"{PRE_PREFIX}:{prefix}", expiration_sec, data_in)
            return
        # nominal case: input is a list of dictionaries
        self.r.setex(f"{PRE_PREFIX}:{prefix}:count", expiration_sec, len(data_in))
        for i, e in enumerate(data_in):
            self.r.setex(f"{PRE_PREFIX}:{prefix}:{i}", expiration_sec, json.dumps(e, default=str))

    @transaction_wrapper
    def get(self, prefix):
        # no data in redis for this prefix yet
        count = self.r.get(f"{PRE_PREFIX}:{prefix}:count")
        if count is None:
            print(f"Cache miss on prefix: {prefix}")
            return []
        count = int(count)
        # special case for just a single dictionary, not a list of dictionaries
        if count == -1:
            temp = self.r.get(f"{PRE_PREFIX}:{prefix}")
            if not temp:
                # this indicates a cache miss
                return []
            print(f"Cache hit! Prefix={prefix}")
            return json.loads(temp)
        # special case for just a single value
        if count == -2:
            print(f"Cache hit! Prefix={prefix}")
            return self.r.get(f"{PRE_PREFIX}:{prefix}")
        # nominal
        list_of_dicts = []
        # print(f"Redis debug. count={count}. prefix={prefix}")
        for i in range(count):
            temp = self.r.get(f"{PRE_PREFIX}:{prefix}:{i}")
            if temp:
                list_of_dicts.append(json.loads(temp))
            else:
                # getting here means that one of the expected entries is missing. Perhaps evicted.
                # Distrust this whole prefix now. Purge it.
                self.delete(f"{PRE_PREFIX}:{prefix}")
                return []
        print(f"Cache hit! Prefix={prefix}")
        return list_of_dicts

    @transaction_wrapper
    def delete(self, prefix):
        keys = self.r.keys(f"{PRE_PREFIX}:{prefix}:*")
        if keys:
            # print(f"Redis debug. Deleting keys={keys}")
            self.r.delete(*keys)

    @transaction_wrapper
    def set_add(self, set_name, value):
        self.r.sadd(f"{PRE_PREFIX}:{set_name}", value)

    @transaction_wrapper
    def set_pop(self, set_name):
        return self.r.spop(f"{PRE_PREFIX}:{set_name}")

    @transaction_wrapper
    def get_plain(self, key):
        return self.r.get(f"{PRE_PREFIX}:{key}")

    @transaction_wrapper
    def add_plain(self, key, value, expiration_sec=None):
        if expiration_sec is None:
            self.r.set(f"{PRE_PREFIX}:{key}", value)
        else:
            self.r.setex(f"{PRE_PREFIX}:{key}", expiration_sec, value)
        return True
