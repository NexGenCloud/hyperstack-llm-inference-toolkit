import argparse

import openai
import requests

# Configure the OpenAI client with our custom URL
openai.base_url = 'http://localhost:5001/api/v1/'


def generate_api_key(selected_model_name):
    user_id = 0
    response = requests.post(
        'http://localhost:5001/api/v1/generate_api_key',
        json={
            'user_id': str(user_id),
            'model_name': selected_model_name,
        },
    )
    if response.status_code == 200:
        api_key = response.json()['api_key']
        print('API key generated')
        return api_key
    else:
        print(response)
        print('Failed to generate API key')
        return None


def sample_chat_completion_api(selected_model_name):
    print(f'Selected model: {selected_model_name}')
    api_key = generate_api_key(selected_model_name)
    if api_key:
        openai.api_key = api_key
        try:
            messages = [
                {'role': 'user', 'content': 'Tell me a thrilling story with a happy ending.'},
            ]
            response = openai.chat.completions.create(
                model=selected_model_name,
                messages=messages,
                max_tokens=100,
                temperature=0.7,
                n=2,
                stop=['lived happily ever after.'],
                presence_penalty=0.6,
                frequency_penalty=0.4,
                stream=False,
                user='example_user',
                # top_p=0.9,
                # seed=50,
                # response_format='json',
                # parallel_tool_calls=False,
                # logit_bias={},
                # logprobs=None,
                # functions=[],
                # function_call='auto',
                # tool_choice='none',
                # tools=[],
                # top_logprobs=None
            )
            print(response)
        except openai.OpenAIError as e:
            print(f'Error: {e}')


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--model_name', type=str, default='mistralai/Mistral-7B-Instruct-v0.2')
    args = args.parse_args()

    sample_chat_completion_api(args.model_name)
