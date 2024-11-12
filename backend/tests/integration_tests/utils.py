import os


API_BASE_URL = f'{os.getenv("API_HOST")}/api/v1'
API_GENERATE_API_KEY_URL = f"{API_BASE_URL}/generate_api_key"

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")


class AIModel:
    MISTRALAI = "mistralai/Mistral-7B-Instruct-v0.2"
    PERPLEXITY = "perplexity/Perplexity-7B-Instruct-v0.2"

    @classmethod
    def all(cls):
        return [cls.MISTRALAI, cls.PERPLEXITY]


def make_test_llm_config():
    return {
        AIModel.MISTRALAI: "http://mock-mistralai/complete",
        AIModel.PERPLEXITY: "http://mock-perplexity/complete",
    }
