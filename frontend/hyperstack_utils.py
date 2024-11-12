# flake8: noqa
import datetime
import hmac
import json
import os

import requests
import streamlit as st

from loguru import logger as lg


def get_password() -> str:
    try:
        password = st.secrets["password"]
    except (FileNotFoundError, KeyError):
        password = os.environ.get("APP_PASSWORD")

    if password is None:
        raise ValueError(
            "Password not found in Streamlit secrets or environment variable (APP_PASSWORD)."
        )

    return password


def get_hyperstack_api_key() -> str:
    try:
        key = st.secrets["hyperstack_api_key"]
    except (FileNotFoundError, KeyError):
        key = os.environ.get("HYPERSTACK_API_KEY")

    if key is None:
        raise ValueError("Hyperstack API key must be specified")

    return key


def check_password():
    """
    Returns `True` if the user had the correct password.
    """

    def password_entered():
        """
        Checks whether a password entered by the user is correct.
        """
        if hmac.compare_digest(st.session_state["password"], get_password()):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password.
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False


def get_resources_list(api_url, endpoint, query_param_dict=None, headers=None):
    # hacky code to get resources list
    # todo: improve by making it more robust (handle trailing/starting slashes etc.)

    url = os.path.join(api_url, endpoint)
    query_param_str = ""
    if query_param_dict:
        for key, value in query_param_dict.items():
            query_param_str += f"{key}={value}&"
        query_param_str = query_param_str[:-1]
        url = url + f"?{query_param_str}"

    lg.debug(f"Getting resources from API: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching {endpoint}: {response.status_code} - {response.text}")
        return None


class HyperstackClient:

    DEFAULT_API_BASE_URL = "https://infrahub-api.nexgencloud.com/v1"

    def __init__(
        self,
        api_base_url: str = DEFAULT_API_BASE_URL,
        environment_name: str = "",
        api_key: str = "",
    ):
        self.api_base_url = api_base_url
        self.environment_name = environment_name

        self.api_key = api_key or os.environ.get("HYPERSTACK_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Hyperstack API key not provided, please provide it as an argument or set as environment variable"
            )

        self.headers = {"api_key": self.api_key}

    def deploy_vm(
        self,
        vm_name: str = "",
        user_data: str = "",
        key_name: str = "",
        flavor: str = "n1-RTX-A6000x1",
        image_name: str = "Ubuntu Server 22.04 LTS R535 CUDA 12.2",
        assign_floating_ip: bool = False,
        labels=None,
    ):
        if not vm_name:
            vm_name = f'vm-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
            lg.debug(f"VM name not provided, using default name: {vm_name}")

        # VM Creation payload
        data = {
            "name": vm_name,
            "environment_name": self.environment_name,
            "image_name": image_name,
            "flavor_name": flavor,
            "key_name": key_name,
            "assign_floating_ip": assign_floating_ip,
            "count": 1,
            "user_data": user_data,
            "labels": labels or [],
        }
        lg.debug("Deploying VM with:")
        data_to_print = data.copy()
        data_to_print["user_data"] = "[TRUNCATED FOR LOGGING]"
        lg.debug(json.dumps(data_to_print, indent=4))

        # Create the VM
        create_response = requests.post(
            self.api_base_url + "/virtual-machines", headers=self.headers, json=data
        )

        if create_response.status_code == 200:
            lg.debug("VM creation successful")
        else:
            lg.error(
                f"VM creation failed: status code: {create_response.status_code}, "
                f"text: \n  {create_response.text}"
            )
        return create_response

    def get_keypairs(self):
        url = f"{self.api_base_url}/core/keypairs"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            return response_json["keypairs"]
        else:
            lg.error(
                f"Error fetching key pairs: {response.status_code} - {response.text}"
            )
            return None

    def get_environments(self):
        url = f"{self.api_base_url}/core/environments"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            response_json = response.json()
            return response_json["environments"]
        else:
            lg.error(
                f"Error fetching environments: {response.status_code} - {response.text}"
            )
            return None

    def get_flavors(self):
        url = f"{self.api_base_url}/core/flavors"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            data = response_json["data"]
            flavors_nested_list = [item["flavors"] for item in data]
            flavors = [item for sublist in flavors_nested_list for item in sublist]
            return flavors
        else:
            lg.error(
                f"Error fetching flavors: {response.status_code} - {response.text}"
            )
            return None

    def get_images(self):
        url = f"{self.api_base_url}/core/images"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            response_json = response.json()
            images_data = response_json["images"]
            images_nested_list = [item["images"] for item in images_data]
            images = [item for sublist in images_nested_list for item in sublist]

            return images
        else:
            lg.error(f"Error fetching images: {response.status_code} - {response.text}")
            return None
