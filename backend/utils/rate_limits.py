import time
import logging
import functools

from flask import request, jsonify

from tables.api_key import APIKey
from utils.db import db
from utils.redis import get_redis_client
from utils.rest import get_api_key

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """
    Exception class for rate limit exceeded errors.
    """
    def __init__(self, allowed_rpm):
        self.allowed_rpm = allowed_rpm
        super().__init__()


class APIKeyRateLimitManager:
    """
    A class to manage requests rate limits for an API key.
    """
    def __init__(self, api_key: APIKey):
        self.api_key_obj = api_key
        self.client = get_redis_client()

    def make_key(self):
        current_time = int(time.time())
        return f"rate_limit:{self.api_key_obj.api_key}:{current_time // 60}"

    def increment_usage(self):
        key = self.make_key()
        lock = self.client.lock(f"lock:{key}", timeout=10)
        if lock.acquire(blocking=True):
            try:
                self.client.incr(key)
                self.client.expire(key, 60 * 60 * 24)
            finally:
                lock.release()

    def should_allow(self):
        key = self.make_key()
        count = self.client.get(key)
        return int(count or 0) < self.api_key_obj.allowed_rpm


def ensure_api_key_rate_limits(func):
    """
    Decorator to ensure that the API key rate limits are enforced.

    Raises RateLimitExceeded exception if the api key rate limit is exceeded.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # try to retrieve api key from request headers
        api_key = db.session.query(APIKey).filter_by(api_key=get_api_key(request)).first()
        if api_key:
            manager = APIKeyRateLimitManager(api_key=api_key)
            if manager.should_allow():
                manager.increment_usage()
                return func(*args, **kwargs)
            else:
                raise RateLimitExceeded(api_key.allowed_rpm)
        else:
            logger.warning("[ensure_api_key_rate_limits] API Key is missing.")
            return func(*args, **kwargs)
    return wrapper


def rate_limit_error_handler(error):
    """
    Error handler for RateLimitExceeded exception.
    """
    response = jsonify({
        "error": "rate_limit_exceeded",
        "message": f"Rate limit exceeded: allowed {error.allowed_rpm} requests per minute.",
        "allowed_rpm": error.allowed_rpm
    })
    response.status_code = 429
    return response
