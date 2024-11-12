import json
import re
import time
import typing

import requests
from flask import abort, Response, jsonify, stream_with_context
from sqlalchemy.orm import Session

from tables.metrics import Metric, MetricSchema

RE_NORMALIZE = re.compile(r'\s*data\s*:\s*({.*)')


def handle_non_streaming_request(
    session: Session,
    api_key_id: int,
    endpoint: str,
    start_time: int,
    chat_completion_payload: typing.Dict[str, typing.Any],
) -> Response:
    """
    This function is responsible for handling non-streaming requests from the LLM endpoint API. This function is
    called when the `stream` parameter in the request is set to `False`. The function will update the metrics and
    return the response from the LLM endpoint API.
    """
    response = None
    try:
        response = requests.post(endpoint, json=chat_completion_payload)
        response.raise_for_status()
        json_response = response.json()
    except json.JSONDecodeError:
        abort(
            500,
            description=f'Failed to decode response from LLM endpoint API ({endpoint}): {response.text}',
        )
    except requests.exceptions.RequestException as e:
        abort(
            response.status_code if (response is not None and 400 <= response.status_code < 500) else 500,
            description=f'Failed to receive response from LLM endpoint API ({endpoint}): '
                        f'{e} {response.json() if response is not None else ""}',
        )

    update_metrics(
        session=session,
        usage_data=json_response.get('usage', {}),
        api_key_id=str(api_key_id),
        input_data=chat_completion_payload,
        response_choices=json_response['choices'],
        start_time=start_time
    )
    return jsonify(json_response)


def handle_streaming_request(
    session: Session,
    api_key_id: int,
    endpoint: str,
    start_time: int,
    chat_completion_payload: typing.Dict[str, typing.Any],
    raw: bool,
) -> Response:
    """
    This function is responsible for making sure a streaming response is returned to the client. How this is made
    possible is that we return `StreamingResponse` object which is a subclass of `Response` and can be used to stream
    data back to the client. We use the `stream_generator` function to generate the data that will be streamed back to
    the client. This function is an async generator that yields data as it is received from the LLM endpoint API.
    Finally, metrics are updated to account for the data that was streamed back to the client and an important point to
    note here is that the last response sent back by the LLM endpoint API is used to update the metrics as that
    contains usage data.
    """

    def stream_generator():
        choices = []
        last_response = {}
        response = None

        try:
            # Make a GET request to the external API with streaming enabled
            response = requests.post(endpoint, json=chat_completion_payload, stream=True)
            response.raise_for_status()  # Raise an error for bad status codes
            for chunk in response.iter_content(chunk_size=None):
                chunk = chunk.decode('utf-8')
                if chunk and (match := RE_NORMALIZE.match(chunk)):
                    try:
                        parsed_chunk = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        abort(
                            500,
                            description=f'Failed to decode response from LLM endpoint API ({response.url}): {chunk}',
                        )
                    if parsed_chunk and parsed_chunk['choices']:
                        if raw:
                            yield chunk
                        else:
                            yield match.group(1) + '\n'
                        last_response = parsed_chunk
                        choices.extend(last_response['choices'])
        except requests.exceptions.RequestException as e:
            abort(
                response.status_code if (response is not None and 400 <= response.status_code < 500) else 500,
                description=f'Failed to receive response from LLM endpoint API ({endpoint}): '
                            f'{e} {response.json() if response is not None else ""}',
            )

        # Once streaming is done, update the metrics
        update_metrics(
            session=session,
            usage_data=last_response.get('usage', {}),
            api_key_id=str(api_key_id),
            input_data=chat_completion_payload,
            response_choices=choices,
            start_time=start_time
        )

    return Response(
        stream_with_context(stream_generator()), mimetype='text/event-stream'
    )


def update_metrics(
    session: Session,
    usage_data: typing.Dict[str, typing.Any],
    api_key_id: str,
    input_data: typing.Dict[str, typing.Any],
    response_choices: list,
    start_time: float
):
    """
    Update the metrics table with the data from the completion request.
    """
    metric_payload = {
        'api_key_id': api_key_id,
        'input': json.dumps(input_data, indent=2),
        'created': int(start_time),
        'model': input_data['model'],
        'choices': str(response_choices),
        'prompt_tokens': usage_data.get('prompt_tokens', -999),
        'total_tokens': usage_data.get('total_tokens', -999),
        'completion_tokens': usage_data.get('completion_tokens', -999),
        'duration': time.time() - start_time,
    }
    metric_schema = MetricSchema(
        only=tuple(metric_payload.keys()),
    )
    metric_data = metric_schema.dump(metric_payload)
    Metric.create(session, **metric_data)
