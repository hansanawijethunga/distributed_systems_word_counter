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

    def set_bulk_values(self, data):
        """Set multiple key-value pairs in Redis from a dictionary"""
        if isinstance(data, dict):
            self.client.mset(data)

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

    def update_letter_counts(self, data):
        """Update Redis with letter counts, adding to existing values if keys exist"""
        with self.client.pipeline() as pipe:
            for key, value in data.items():
                try:
                    pipe.incrby(key, value)  # Increment the existing value by the new value
                except redis.RedisError as e:
                    print(f"Error updating key {key}: {e}")
            pipe.execute()

    def update_word_list(self, words):
        if not isinstance(words, dict):
            print("Input must be a dictionary.")
            return

        if not self.client:
            print("Redis client is not initialized.")
            return

        for key, new_words in words.items():
            redis_key = f"{key}_"

            # Get the existing value from Redis
            existing_value = self.client.get(redis_key)
            existing_words = []

            if existing_value:
                existing_words = [w.strip() for w in existing_value.split(",") if w.strip()]

            # Merge without removing duplicates
            combined_words = existing_words + new_words
            combined_words = [word.strip() for word in combined_words if word.strip()]

            # Save back to Redis
            updated_value = ", ".join(combined_words)
            self.set_value(redis_key, updated_value)  # Assuming set_value is async




# Example Usage
if __name__ == "__main__":
    redis_client = RedisClient()
    redis_client1 = RedisClient(port=4380)
    redis_client.clear_all_dbs()
    redis_client1.clear_all_dbs()


    print(redis_client.get_all_keys_and_values())
