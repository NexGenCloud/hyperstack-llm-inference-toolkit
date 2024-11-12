import os

if os.getenv("API_HOST") is None:
    API_BASE_URL = None
    API_GENERATE_API_KEY_URL = None
    API_CHAT_COMPLETIONS_URL = None
else:
    API_BASE_URL = f'{os.getenv("API_HOST")}/api/v1'
    API_GENERATE_API_KEY_URL = f"{API_BASE_URL}/generate_api_key"
    API_DELETE_API_KEY_URL = f"{API_BASE_URL}/delete_api_key"
    API_CHAT_COMPLETIONS_URL = f"{API_BASE_URL}/chat/completions"
