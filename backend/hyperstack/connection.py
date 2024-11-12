import json
import requests
import typing
from dataclasses import dataclass


API_KEY: str | None = None


@dataclass
class Response:
    error: str | None
    response: dict[str, typing.Any] | None | requests.Response


def set_api_key(api_key: str):
    global API_KEY
    API_KEY = api_key


def call(
    method: typing.Literal['GET', 'POST', 'PUT', 'DELETE'], url: str, payload: dict | None = None,
    headers: dict | None = None, handle_special_status: bool = False, nested_obj_key: str | None = None,
) -> Response:
    # TODO: We should have a timeout in place as well
    response = error = None

    headers = headers or {}
    if not API_KEY:
        raise ValueError('API KEY must be set before making a call')

    headers['api_key'] = API_KEY

    try:
        response = requests.request(method, url, json=payload, headers=headers)
    except requests.exceptions.ConnectionError as e:
        error = f'Failed to make a {method.lower()} request to {url!r}: {e}'
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error = f'Error Code ({response.status_code!r}) for {url!r}: {e}'
        else:
            try:
                response = response.json()
            except json.JSONDecodeError:
                error = f'Failed to decode response for {url!r}'
            else:
                if handle_special_status:
                    if response['status'] is False:
                        error = response['message']
                    elif nested_obj_key:
                        response = response[nested_obj_key]

    return Response(error=error, response=response)
