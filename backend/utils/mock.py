import time
import re

from flask import current_app as app, Response

RE_NORMALIZE = re.compile(r'\s*data\s*:\s*({.*)')


def handle_mock_non_streaming_request():
    """
    Handle non-streaming request to the LLM endpoint API and mock its response.
    """
    return {
        'id': 'cmpl-0332ebd727cc4af19fa2d80035ab1e1f',
        'object': 'text_completion',
        'created': 1716838725,
        'model': 'mistralai/Mistral-7B-Instruct-v0.2',
        'choices': [
            {
                'index': 0,
                'message': {
                    'content': (
                        'A potential future writing project.\n\n---\n\nTitle: The Last Hope'
                        '\n\nGenre: Science Fiction, Adventure, Thriller\n\nLogline: In a dystopian future where '
                        'Earth is on the brink of destruction, a group of rebels embark on a dangerous mission to '
                        'save humanity by seeking out the last hope for survival - a mythical planet rumored to '
                        'possess the power to restore the Earth.\n'
                    )
                },
                'logprobs': None,
                'finish_reason': 'length',
                'stop_reason': None,
            }
        ],
        'usage': {
            'prompt_tokens': 7,
            'total_tokens': 107,
            'completion_tokens': 100,
        },
    }


def handle_mock_streaming_request() -> Response:
    """
    Handle streaming request to the LLM endpoint API and mock its response.
    """
    LLM_MOCK_DATA_STREAM_PATH = app.config['LLM_MOCK_DATA_STREAM_PATH']

    def stream_generator():
        with open(LLM_MOCK_DATA_STREAM_PATH, 'r') as fp:
            for chunk in fp:
                if chunk and (match := RE_NORMALIZE.match(chunk)):
                    time.sleep(0.01)
                    yield match.group(1) + '\n'

    return Response(stream_generator(), mimetype='text/event-stream')
