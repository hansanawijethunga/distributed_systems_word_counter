import redis

class RedisClient:
    def __init__(self, host="localhost", port=4379, db=0):
        """Initialize Redis connection"""
        self.client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)

    def set_value(self, key, value, expire=None):
        """Set a key-value pair in Redis with optional expiration time"""
        self.client.set(key, value, ex=expire)

    def get_value(self, key):
        """Get the value of a key"""
        return self.client.get(key)

    def delete_key(self, key):
        """Delete a key from Redis"""
        self.client.delete(key)

    def key_exists(self, key):
        """Check if a key exists in Redis"""
        return self.client.exists(key) > 0

    def get_all_keys_and_values(self):
        """Get all keys and their values as a dictionary"""
        keys = self.client.keys("*")  # Get all keys
        data = {}
        for key in keys:
            # Check the type of data stored and handle accordingly
            value = self.client.get(key)
            if value is None:
                # If it's a more complex type, like a list or set
                if self.client.type(key) == 'list':
                    value = self.client.lrange(key, 0, -1)
                elif self.client.type(key) == 'set':
                    value = self.client.smembers(key)
                elif self.client.type(key) == 'hash':
                    value = self.client.hgetall(key)
            data[key] = value
        return data

    def clear_db(self):
        """Clear the current database"""
        self.client.flushdb()

    def clear_all_dbs(self):
        """Clear all databases"""
        self.client.flushall()

# Example Usage
if __name__ == "__main__":
    redis_client = RedisClient()
    abc = redis_client.get_value("last_success_proposal")
    print(abc)
    if abc is None or "":
        print("no Value")
    redis_client.clear_all_dbs()
    print(redis_client.get_all_keys_and_values())  # Output: None
