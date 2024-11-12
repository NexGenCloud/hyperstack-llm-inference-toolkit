import json
import os
import requests
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

from env import API_CHAT_COMPLETIONS_URL, API_GENERATE_API_KEY_URL, API_BASE_URL
from web_utils import (
    get_model_name_selection,
    initialize_page,
    change_user_id,
    sidebar_page_link,
)


PAGE_HELP = """
## 🧭 Introduction
This page allows you to interact with one of your deployed LLMs model. 

## 📋 User Instructions
1. **Select a Model**: Choose a model from the sidebar to chat with.
2. **Enter Your Message**: Type your message in the chat input box at the bottom of the page.
3. **Configure Assistant**: Click the "Configure Assistant" button in the sidebar to change advanced settings such as temperature, max tokens, and presence penalty.
7. **Chat with Assistant**: Once you've selected a model and entered your message, click the ">" button to start chatting with the assistant.

## 👍 Additional Tips
* You can stream the response from the API by checking the "Stream results" checkbox in the configure assistant dialog.
* You can reset all previous conversations by clicking on the "Reset messages" button in the sidebar.
* By default, the `User_ID = 0` (default user) is used for interacting with the API.
"""

DEFAULT_ASSISTANT_CONFIGS = {
    "system_prompt": "",
    "temperature": 0.7,
    "max_tokens": 512,
    "presence_penalty": 0.7,
    "frequency_penalty": 0.6,
    "stream": True,
}


def show_code(code):
    """
    Displays a code block with the given code.

    Args:
        code (str): The code to display.
    """
    with stylable_container(
        "codeblock",
        """
            code {
                white-space: pre-wrap !important;
            }
            """,
    ):
        st.code(code)


def get_all_active_models_names():
    """
    Fetches all active model names from the API.

    Returns:
        list: A list of active model names if the request is successful, None otherwise.
    """
    url = f"{API_BASE_URL}/models?active=1"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        st.error(f"Error fetching models: {response.text}")
        return None
    return [data["name"] for data in response.json()]


def get_models_to_show():
    """
    Gets the list of models to show in the UI.

    Returns:
        list: A list of model names to show.
    """
    models_names = get_all_active_models_names()
    if "model_name" in st.session_state:
        model_name = st.session_state.model_name
        if model_name not in models_names:
            st.error(f"Model {model_name} is not supported")
            return models_names

        models_to_show = models_names
    else:
        models_to_show = models_names

    return models_to_show


def generate_api_key(user_id):
    """
    Generates an API key for a given user ID.

    Args:
        user_id (int): The user ID for which to generate the API key.
    """
    response = requests.post(
        API_GENERATE_API_KEY_URL,
        json={"user_id": str(user_id)},
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code == 200:
        st.session_state["api_key"] = response.json()["api_key"]
        st.toast("API key generated", icon="✅")
        return response.json()["api_key"]
    else:
        st.error("Failed to generate API key")
        return None


def stream_response(response):
    """
    Streams the response from the API.

    Args:
        response (requests.Response): The response object from the API.
    """
    content = ""
    message_placeholder = st.empty()
    try:
        for chunk in response.iter_lines():
            if chunk:
                delta = json.loads(chunk.decode("utf-8").strip())["choices"][0]["delta"]
                if part := delta.get("content"):
                    content += part
                    message_placeholder.markdown(content)
        # append message to messages state
        st.session_state.messages.append({"role": "assistant", "content": content})
    except requests.exceptions.ChunkedEncodingError:
        st.error("Something went wrong. Please 'Reset messages' to continue.")


@st.dialog("Configure assistant", width="large")
def configure_assistant_dialog(default_configs=None):
    """
    Displays a dialog to change advanced settings of an assistant
    """

    global DEFAULT_ASSISTANT_CONFIGS
    if not default_configs:
        default_configs = DEFAULT_ASSISTANT_CONFIGS

    assistant_configs = st.session_state.get("assistant_configs", {})
    system_prompt = st.text_area(
        label="System prompt",
        value=assistant_configs.get("system_prompt", default_configs["system_prompt"]),
    )
    temperature = st.slider(
        label="Temperature",
        min_value=0.0,
        max_value=2.0,
        value=assistant_configs.get("temperature", default_configs["temperature"]),
        step=0.1,
    )
    max_tokens = st.number_input(
        label="Max tokens",
        min_value=1,
        max_value=99999,
        value=assistant_configs.get("max_tokens", default_configs["max_tokens"]),
    )
    presence_penalty = st.slider(
        label="Presence penalty",
        min_value=-2.0,
        max_value=2.0,
        value=assistant_configs.get(
            "presence_penalty",
            default_configs["presence_penalty"],
        ),
        step=0.1,
    )
    frequency_penalty = st.slider(
        label="Frequency penalty",
        min_value=-2.0,
        max_value=2.0,
        value=assistant_configs.get(
            "frequency_penalty",
            default_configs["frequency_penalty"],
        ),
        step=0.1,
    )
    stream = st.checkbox("Stream results", value=True)
    if st.button("Confirm", type="primary"):
        new_assistant_configs = {
            "system_prompt": system_prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty,
            "stream": stream,
        }
        st.session_state.assistant_configs = new_assistant_configs
        st.rerun()


def main():
    """
    The main function to initialize and run the Streamlit app.
    """
    initialize_page(title="Playground - Hyperstack LLM Inference Toolkit")
    st.sidebar.divider()
    st.sidebar.subheader("Settings")

    # API key sidebar
    if "api_key" not in st.session_state:
        st.session_state.api_key = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Get or create API key
    if not st.session_state.get("api_key"):
        api_key_generated = generate_api_key(0)
        st.session_state["api_key"] = api_key_generated

    # Model selection sidebar
    with st.sidebar:
        models = get_all_active_models_names()
        model_name = get_model_name_selection(models)

    api_key = st.sidebar.text_input(
        "API key", value=st.session_state.get("api_key", ""), type="password"
    )

    # Configure assistant
    if st.sidebar.button(
        "Configure Assistant", type="primary", use_container_width=True
    ):
        configure_assistant_dialog()
    assistant_configs = st.session_state.get(
        "assistant_configs", DEFAULT_ASSISTANT_CONFIGS
    )

    # Reset messages sidebar
    if st.sidebar.button("Reset messages", use_container_width=True):
        st.session_state.messages = []

    # Show help button
    sidebar_page_link(PAGE_HELP)

    col1, col2, col3 = st.columns([1, 1, 4])

    ui_button_type = (
        "primary" if st.session_state.get("UI_enabled", True) else "secondary"
    )
    if col1.button("🖥️ User interface", use_container_width=True, type=ui_button_type):
        st.session_state["UI_enabled"] = True
        st.session_state["API_enabled"] = False
        st.rerun()
    api_button_type = (
        "primary" if st.session_state.get("API_enabled", False) else "secondary"
    )
    if col2.button("👨‍💻 API", use_container_width=True, type=api_button_type):
        st.session_state["UI_enabled"] = False
        st.session_state["API_enabled"] = True
        st.rerun()
    st.divider()

    if st.session_state.get("UI_enabled", True):
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Enter your message"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                messages = [
                    {"role": "system", "content": assistant_configs["system_prompt"]}
                ] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                data = {
                    "model": model_name,
                    "messages": messages,
                    "stream": assistant_configs["stream"],
                    "raw_stream_response": False,
                    "temperature": assistant_configs["temperature"],
                    "max_tokens": assistant_configs["max_tokens"],
                    "presence_penalty": assistant_configs["presence_penalty"],
                    "frequency_penalty": assistant_configs["frequency_penalty"],
                }
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                # Make API call
                response = requests.post(
                    API_CHAT_COMPLETIONS_URL,
                    headers=headers,
                    json=data,
                    stream=data["stream"],
                )

                if response.status_code != 200:
                    response_json = response.text
                    st.error(f"Error from API: {response_json}")
                    return

                if data["stream"]:
                    stream_response(response)
                else:
                    response_json = response.json()
                    content = response_json["choices"][0]["message"]["content"]
                    st.markdown(content)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": content}
                    )

    if st.session_state.get("API_enabled", False):
        api_url = "http://app:5001/api/v1/chat/completions"

        example_messages = [{"role": "user", "content": "Hi, how are you?"}]
        data = {
            "model": model_name,
            "temperature": assistant_configs["temperature"],
            "max_tokens": assistant_configs["max_tokens"],
            "presence_penalty": assistant_configs["presence_penalty"],
            "frequency_penalty": assistant_configs["frequency_penalty"],
            "messages": example_messages,
        }
        api_key = st.session_state.get("api_key")
        st.session_state["api_data"] = data
        example_api_call = (
            f"curl -X POST {api_url} \\\n"
            '-H "Content-Type: application/json" \\\n'
            f'-H "Authorization: Bearer {api_key}" \\\n'
            f"-d '{json.dumps(data, indent=4)}'"
        )
        # Text input for API call
        st.subheader("API call example")
        st.code(example_api_call)

        col1, col2, col3 = st.columns([1, 1, 3])
        with col1.popover("More info", use_container_width=True):
            st.markdown(
                """
            Replace `app` above with:
            * `localhost` (local deployment)
            * `[public-ip-of-proxy-vm]` (cloud deployment)

            To find the public IP of your proxy VM, follow the following instructions:
            1. Go to the [Hyperstack Console > Virtual Machines](https://console.hyperstack.cloud/virtual-machines)
            2. Find the Public IP next to the proxy VM (e.g. `38.80.123.227`)
            """
            )

        # Button to call chat completion API
        if col2.button(
            "Call chat completion API", type="primary", use_container_width=True
        ):
            try:
                # Extract API call data from text area
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                with st.spinner("Calling chat completion API..."):
                    # Make API call
                    response = requests.post(
                        API_CHAT_COMPLETIONS_URL,
                        headers=headers,
                        json=st.session_state.get("api_data"),
                    )

                if response.status_code == 200:

                    st.toast("API call successful", icon="✅")
                    st.subheader("API call response")
                    show_code(json.dumps(response.json(), indent=4))
                else:
                    st.error(
                        f"Failed to call chat completion API"
                        f" (status: {response.status_code}): {response.text}"
                    )
                    try:
                        st.json(response.json())
                    except ValueError:
                        pass
            except Exception as e:
                st.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
