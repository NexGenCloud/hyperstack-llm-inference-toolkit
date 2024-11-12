import redis

from flask import current_app as app


def get_redis_client():
    """
    Returns a Redis client.
    """
    return redis.Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB']
    )


def flush_redis_db():
    """
    Flushes the Redis database.
    """
    get_redis_client().flushdb()
