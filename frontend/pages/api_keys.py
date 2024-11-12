import os
import pandas as pd
import requests
import streamlit as st
from loguru import logger as lg

from web_utils import initialize_page, change_user_id, sidebar_page_link
from env import API_GENERATE_API_KEY_URL, API_DELETE_API_KEY_URL, API_BASE_URL

PAGE_HELP = """
## 🧭 Introduction
This page allows you to create an API key for your user ID and view existing API keys.
This API key can be used to interact with the `chat/completion` API endpoint.

## 📋 User Instructions
1. **Enter User ID**: Input the user ID for which you want to generate an API key.
2. **Generate API Key**: Click the "Generate API key" button to create a new API key.
3. **Delete API Key**: Click the "Delete API key" button to remove an existing API key.
4. **View API Keys**: Existing API keys will be displayed in a table below.

## 👍 Additional Tips
* API keys can only be deleted if they have not been used yet.
* API keys that have been used can only be disabled.

"""


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

        return response.json()
    else:
        st.error("Failed to generate API key")
        return None


def delete_api_key(user_id, api_key_id):
    """
    Generates an API key for a given user ID and api_key_id.

    Args:
        user_id (int): The user ID for which to generate the API key.
        api_key_id (int): The api key id to delete.
    """
    response = requests.post(
        API_DELETE_API_KEY_URL,
        json={"user_id": str(user_id), "api_key_id": str(api_key_id)},
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code == 200:
        st.toast(response.json()["message"], icon="✅")
        st.session_state["api_key"] = " "
    elif response.status_code == 404:
        st.toast(f"⚠️ API key not found for user ID {user_id}")
    elif response.status_code == 409:
        st.toast(f"⚠️ API key is already disabled")
    else:
        st.toast(f"❌ Failed to delete API key: {response}")


def fetch_data(endpoint):
    """
    Fetches data from a given API endpoint.

    Args:
        endpoint (str): The API endpoint to fetch data from.

    Returns:
        dict: The data fetched from the API if the request is successful, None otherwise.
    """
    response = requests.get(
        f"{API_BASE_URL}/{endpoint}",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        st.error(f"Error fetching data from {endpoint}: {response.text}")
        return None
    return response.json()


def main():
    """
    The main function to initialize and run the Streamlit app.
    """
    initialize_page(title="API Keys - Hyperstack LLM Inference Toolkit")

    sidebar_page_link(PAGE_HELP)

    # Initialize session state
    if "api_key" not in st.session_state:
        st.session_state.api_key = None

    st.subheader("Generate API Key")
    input_col1, input_col2 = st.columns([1, 1])
    input_col1.text_input(
        value=st.session_state.get("user_id", 0),
        label="User ID",
        key="user_id_input",
        on_change=change_user_id,
    )

    col1, col2 = st.columns([1, 1])
    if col1.button("✅ Generate API key", type="primary", use_container_width=False):
        lg.debug("Generating API key...")
        st.session_state["api_key"] = None
        response = generate_api_key(st.session_state.get("user_id", 0))

        if response:
            st.session_state["api_key_id"] = response.get("id")

    if st.session_state.get("api_key"):
        st.text_input("API key", value=st.session_state.api_key, disabled=True)

    input_col2.text_input(
        "API key ID",
        value=st.session_state.get("api_key_id", 0),
        disabled=False,
        key="api_key_input",
    )
    if col2.button("❌ Delete API key", type="secondary", use_container_width=False):
        lg.debug("Deleting API key...")
        delete_api_key(
            st.session_state["user_id_input"], st.session_state["api_key_input"]
        )

    st.subheader("Existing API Keys")
    table_data_response = fetch_data(f"tables/api_key")
    if table_data_response:
        rows = table_data_response.get("data", [])
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
