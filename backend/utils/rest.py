import logging
from functools import wraps
import os

import requests
from flask import request, jsonify
from marshmallow import ValidationError

from utils.db import db
from tables.api_key import APIKey


logger = logging.getLogger(__name__)


def validate_request(schema_cls, **schema_kwargs):
    """
    A decorator to validate the request data using a marshmallow schema.
    """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            json_data = request.get_json()
            try:
                if schema_kwargs:
                    schema_instance = schema_cls(**schema_kwargs)
                else:
                    schema_instance = schema_cls()

                validated_data = schema_instance.load(json_data)
            except ValidationError as err:
                return jsonify({"errors": err.messages}), 400
            return func(validated_data, *args, **kwargs)

        return decorated_function

    return decorator


def get_api_key(request):
    """
    Get the API key from the request Authorization headers.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header := request.headers.get("Authorization"):
        return auth_header.split("Bearer ")[1].strip()


def ensure_api_key(include_api_key=False):
    """
    A decorator to validate the API key in the request Authorization headers.
    """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            error_response = jsonify({"error": "Invalid API key."}), 401

            api_key = get_api_key(request)
            if not api_key:
                return error_response

            key = db.session.query(APIKey).filter_by(api_key=api_key).first()
            if not key:
                return error_response

            if include_api_key:
                return func(key, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        return decorated_function

    return decorator


def ensure_admin_api_key():
    """
    A decorator to validate the Admin API key in the request Authorization headers.
    """

    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            error_response = jsonify({"error": "Invalid Admin API key."}), 401

            api_key = get_api_key(request)
            if not api_key:
                return error_response

            admin_api_key_correct = api_key == os.environ.get("ADMIN_API_KEY")
            if not admin_api_key_correct:
                return error_response

            return func(*args, **kwargs)

        return decorated_function

    return decorator


def get_public_ip() -> str:
    public_ip = None
    try:
        response = requests.get("https://httpbin.org/ip")
        response.raise_for_status()
        response_json = response.json()
    except (requests.RequestException, ValueError) as e:
        logger.error(f"An error occurred: {e}")
    else:
        public_ip = response_json.get("origin")
    return public_ip or "0.0.0.0/0"
