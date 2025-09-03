import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        password=os.getenv("REDIS_PASSWORD"),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    print("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    redis_client = None

def set_data(key, data, expiration_secs=3600):
    """Stores data in Redis with an expiration time."""
    if redis_client:
        try:
            redis_client.set(key, json.dumps(data), ex=expiration_secs)
        except redis.exceptions.RedisError as e:
            print(f"Error setting data in Redis: {e}")

def get_data(key):
    """Retrieves data from Redis."""
    if redis_client:
        try:
            data = redis_client.get(key)
            return json.loads(data) if data else None
        except redis.exceptions.RedisError as e:
            print(f"Error getting data from Redis: {e}")
    return None
