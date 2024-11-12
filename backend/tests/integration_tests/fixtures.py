import openai
import requests
import pytest
import os

from .utils import AIModel, API_GENERATE_API_KEY_URL, API_BASE_URL


MODEL_NAME = AIModel.MISTRALAI


@pytest.fixture(scope="module")
def api_client():
    response = requests.post(
        API_GENERATE_API_KEY_URL,
        json={"user_id": "0", "allowed_rpm": 45},
        headers={"Authorization": f'Bearer {os.getenv("ADMIN_API_KEY")}'},
    )
    if response.status_code != 200:
        raise Exception("Failed to generate API key")

    return openai.AsyncOpenAI(
        base_url=API_BASE_URL,
        api_key=response.json()["api_key"],
    )
