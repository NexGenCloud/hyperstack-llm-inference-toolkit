import typing
import os
import json
import logging

logger = logging.getLogger(__name__)


def parse_json_from_env(key_name, default=None) -> typing.Dict[str, typing.Any]:
    """Parse JSON config string to a dictionary."""
    try:
        return json.loads(os.getenv(key_name))
    except (json.JSONDecodeError, TypeError):
        logger.exception(f'Failed to parse JSON config string for: {key_name}')
        return default
