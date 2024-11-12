import os
import streamlit as st
import requests
import time

from web_utils import initialize_page, sidebar_page_link
from hyperstack_utils import (
    HyperstackClient,
    get_hyperstack_api_key,
)

from env import API_BASE_URL

PAGE_HELP = """
## 🧭 Introduction
This page allows you to view all deployed LLMs, add new models, and manage replicas for each model.

## 📋 User Instructions
1. **View Models**: See all your deployed models listed on this page.
2. **Add New Model**: Use the "Add New Model" section to deploy a new model.
3. **Manage Replicas**: For each model, you can add, edit, or delete replicas.
4. **Add Replica**: Click the "Add" button under a model to create a new replica. You can either provide an existing endpoint or deploy a new replica on Hyperstack.
5. **Delete Replica**: Click the "Delete" button next to a replica to remove it. See warning note below.
6. **Delete Model**: Click the "Delete" button next to a model to remove it. See warning note below.

## 👍 Additional Tips
* You can refresh the status of the replica by clicking on the 'Refresh' icon on the right side of the model name.
* Make sure your model name matches the model name used by the inference engine such as vLLM. For example: `NousResearch/Meta-Llama-3.1-8B-Instruct`.
* When deploying a new replica on Hyperstack, make sure to view the help (?) icon for more information.


## ⚠️ Warning
* Deleting a model or replica will only delete it from the database. Any cloud resources may still exist and incur billing costs.
"""

DOCKER_RUN_HELP = """
Define the Docker run command for the VM. Please make sure the model name (set in the previous screen) matches the model name used by the inference engine.

For example to deploy Llama 3.1 8B. The model name is `NousResearch/Meta-Llama-3.1-8B-Instruct`. The Docker run command would look like:

```
mkdir -p /home/ubuntu/data/hf
docker run -d --gpus all \\
    -v /home/ubuntu/data/hf:/root/.cache/huggingface \\
    -p 8000:8000 \\
    --ipc=host --restart always \\
    vllm/vllm-openai:latest --model \\
    "NousResearch/Meta-Llama-3.1-8B-Instruct" \\
    --gpu-memory-utilization 0.9 --max-model-len 15360 \\
    --chat-template examples/tool_chat_template_llama3.1_json.jinja
```
"""


def get_all_models():
    """
    Fetches all models from the API.

    Returns:
        list: A list of models if the request is successful, None otherwise.
    """
    response = requests.get(
        f"{API_BASE_URL}/models",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        st.error(f"Error fetching models: {response.text}")
        return None
    return response.json()


def delete_model(model_id):
    """
    Deletes a model by its ID.

    Args:
        model_id (str): The ID of the model to delete.
    """
    response = requests.delete(
        f"{API_BASE_URL}/models/{model_id}",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 204:
        st.error(f"Error deleting model: {response.text}")
    else:
        st.toast("Model Deleted", icon="✅")
        time.sleep(0.8)
        st.dialog(
            """Model is only deleted from the models table. 
            Any cloud resources may still exist and incur billing costs.
            """
        )
        st.rerun()


def add_model(model_name):
    """
    Adds a new model.

    Args:
        model_name (str): The name of the model to add.
    """
    response = requests.post(
        f"{API_BASE_URL}/models",
        json={"name": model_name},
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code == 201:
        st.toast("Model Created", icon="✅")
        st.session_state["new_model_name"] = ""
    else:
        error = (
            response.json()["message"]
            if "message" in response.json()
            else response.text
        )
        st.error(f"Error Creating model: {error}")


def fetch_replicas(model_id):
    """
    Fetches replicas for a given model.

    Args:
        model_id (str): The ID of the model.

    Returns:
        list: A list of replicas if the request is successful, None otherwise.
    """
    response = requests.get(
        f"{API_BASE_URL}/models/{model_id}/replicas",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        st.error(f"Error fetching models: {response.text}")
        return None
    return response.json()


def edit_replica(replica_id, rate_limit):
    """
    Edits a replica's rate limit.

    Args:
        replica_id (str): The ID of the replica.
        rate_limit (int): The new rate limit for the replica.
    """
    data = {
        "rate_limit": rate_limit,
    }
    response = requests.put(
        f"{API_BASE_URL}/models/replicas/{replica_id}",
        json=data,
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code == 204:
        st.toast("Replica Updated", icon="✅")
    else:
        error = (
            response.json()["message"]
            if "message" in response.json()
            else response.text
        )
        st.error(f"Error Updating Replica: {error}")


def create_replica(
    model_id,
    endpoint,
    should_create_vm=False,
    name=None,
    environment_name=None,
    image_name=None,
    flavor_name=None,
    port=None,
    run_command=None,
    key_name=None,
):
    """
    Creates a new replica for a model.

    Args:
        model_id (str): The ID of the model.
        endpoint (str): The endpoint URL for the replica.
        should_create_vm (bool): Whether to create a virtual machine for the replica.
        name (str, optional): The name of the virtual machine.
        environment_name (str, optional): The environment name for the virtual machine.
        image_name (str, optional): The image name for the virtual machine.
        flavor_name (str, optional): The flavor name for the virtual machine.
        port (int, optional): The port for the virtual machine.
        run_command (str, optional): The run command for the virtual machine.
        key_name (str, optional): The key name for the virtual machine.
    """
    data = {
        "endpoint": endpoint,
        "create_vm": should_create_vm,
    }
    if should_create_vm:
        data["endpoint"] = ""
        data["vm_creation_details"] = {
            "name": name,
            "environment_name": environment_name,
            "image_name": image_name,
            "flavor_name": flavor_name,
            "run_command": run_command,
            "key_name": key_name,
            "port": port,
            "security_rules": [
                {"port_range_min": port, "port_range_max": port},
                {"port_range_min": 22, "port_range_max": 22},
            ],
        }
    response = requests.post(
        f"{API_BASE_URL}/models/{model_id}/replicas",
        json=data,
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code == 201:
        st.toast("Replica Created", icon="✅")
        time.sleep(0.8)
        st.rerun()
    else:
        error = (
            response.json()["message"]
            if "message" in response.json()
            else response.text
        )
        st.error(f"Error Creating Replica: {error}")


def delete_replica(replica_id):
    """
    Deletes a replica by its ID.

    Args:
        replica_id (str): The ID of the replica to delete.
    """
    response = requests.delete(
        f"{API_BASE_URL}/replicas/{replica_id}",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 204:
        st.error(f"Error deleting replica: {response.text}")
    else:
        st.toast("Replica Deleted", icon="✅")
        time.sleep(0.8)
        st.rerun()


@st.dialog("Replica Error Message")
def show_replica_error_message(error_message):
    """
    Displays an error message for a replica.

    Args:
        error_message (str): The error message to display.
    """
    st.write(error_message)


def disable_new_endpoint_text_input():
    """
    Disables the text input for the new endpoint if the create VM checkbox is checked.
    """
    st.session_state["disable_new_endpoint_text_input"] = st.session_state.get(
        "create_vm_checkbox", False
    )


def model_card(item, i):
    """
    Displays a card for a model.

    Args:
        item (dict): The model data.
        i (int): The index of the model.
    """
    with st.expander(item["name"], expanded=True):
        card_cols = st.columns((7.5, 0.5, 1.5))
        card_cols[0].write(f'### {item["name"]}')
        if card_cols[1].button("**↻**", f'refresh_{item["name"]}'):
            st.rerun()
        if card_cols[2].button(
            "Delete",
            f'delete_model_{item["name"]}',
            use_container_width=True,
            type="primary",
        ):
            delete_model(item["id"])

        replicas = fetch_replicas(item["id"])
        header_cols = st.columns((0.5, 7, 0.5, 1.5))
        header_cols[0].write("###### ID")
        header_cols[1].write("###### LLM Endpoint URL")
        header_cols[2].write("###### Status")
        header_cols[3].write("###### Action")
        if replicas:
            for replica in replicas:
                cols = st.columns((0.5, 7, 0.5, 1.5))
                error_message_exists = True if replica["error_message"] else False
                endpoint = replica["endpoint"]
                if error_message_exists:
                    endpoint = "Replica is in an erroneous state."
                cols[0].write(replica["id"])
                endpoint = cols[1].text_input(
                    f'Endpoint {replica["id"]}',
                    value=endpoint,
                    label_visibility="collapsed",
                    disabled=True,
                )
                if replica["vm_status"] == "SUCCESS":
                    cols[2].button(
                        "✔️", f'success_button_{replica["id"]}', disabled=True
                    )
                elif replica["vm_status"] == "FAILED":
                    if cols[2].button("❌", f'error_button_{replica["id"]}'):
                        if error_message_exists:
                            show_replica_error_message(replica["error_message"])

                else:
                    loading_button_html = """
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <title>Loading Spinner</title>
                        <style>
                            .spinner {
                                margin: 10px auto;
                                width: 20px;
                                height: 20px;
                                border: 2px solid rgba(0, 0, 0, 0.1);
                                border-top: 2px solid #333;
                                border-radius: 50%;
                                animation: spin 1s linear infinite;
                            }
                            @keyframes spin {
                                0% {
                                    transform: rotate(0deg);
                                }
                                100% {
                                    transform: rotate(360deg);
                                }
                            }
                        </style>
                    </head>
                    <body>
                        <div class="spinner"></div>
                    </body>
                    </html>
                    """
                    cols[2].markdown(loading_button_html, unsafe_allow_html=True)
                if cols[3].button(
                    "Delete",
                    key=f'delete_{replica["id"]}',
                    type="primary",
                    use_container_width=True,
                ):
                    delete_replica(replica["id"])

        if st.button(
            "Add",
            f'add_button_{item["name"]}',
            use_container_width=True,
            type="primary",
        ):
            st.session_state["new_replica_model_id"] = item["id"]
            st.session_state["new_replica_model_name"] = item["name"]
            st.session_state[
                f'new_endpoint_{st.session_state["new_replica_model_name"]}'
            ] = ""
            st.session_state[
                f'new_replica_vm_name{st.session_state["new_replica_model_name"]}'
            ] = ""
            st.session_state[
                f'new_replica_port{st.session_state["new_replica_model_name"]}'
            ] = ""
            st.session_state[
                f'new_replica_run_command{st.session_state["new_replica_model_name"]}'
            ] = ""
            st.session_state[
                f'new_replica_key_name{st.session_state["new_replica_model_name"]}'
            ] = ""
            st.session_state["create_vm_checkbox"] = False
            st.session_state["disable_new_endpoint_text_input"] = False
            create_replica_dialog()


@st.dialog("Add New Replica", width="large")
def create_replica_dialog():
    """
    Displays a dialog to create a new replica.
    """
    api_key = get_hyperstack_api_key()
    client = HyperstackClient(api_key=api_key)

    new_endpoint = st.text_input(
        "Endpoint",
        key=f'new_endpoint_{st.session_state["new_replica_model_name"]}',
        disabled=st.session_state.get("disable_new_endpoint_text_input", False),
    )

    create_vm_checkbox = st.checkbox(
        "Deploy new replica on Hyperstack",
        on_change=disable_new_endpoint_text_input,
        key="create_vm_checkbox",
    )

    if create_vm_checkbox:

        with st.spinner("Getting Hyperstack resources..."):
            # todo: call the methods below asynchronously at the same time
            if not st.session_state.get("client_keypairs"):
                st.session_state["client_keypairs"] = st.session_state.get(
                    "client_keypairs", client.get_keypairs()
                )
            if not st.session_state.get("client_flavors"):
                st.session_state["client_flavors"] = st.session_state.get(
                    "client_flavors", client.get_flavors()
                )
            if not st.session_state.get("client_images"):
                st.session_state["client_images"] = st.session_state.get(
                    "client_images", client.get_images()
                )
            if not st.session_state.get("client_environments"):
                st.session_state["client_environments"] = st.session_state.get(
                    "client_environments", client.get_environments()
                )

        environments = st.session_state.get("client_environments")
        flavors = st.session_state.get("client_flavors")
        unique_flavor_names = sorted(list(set([flavor["name"] for flavor in flavors])))
        images = st.session_state.get("client_images")
        image_names = [img["name"] for img in images]
        unique_images = list(set(image_names))
        ubuntu_images = sorted(
            [
                img
                for img in unique_images
                if "ubuntu" in img.lower() or "LTS" in img.lower()
            ],
            reverse=True,
        )
        keypairs = st.session_state.get("client_keypairs")

        vm_name = st.text_input(
            "VM Name",
            key=f'new_replica_vm_name{st.session_state["new_replica_model_name"]}',
            help="Name of the virtual machine for the replica.",
        )
        environment_name = st.selectbox(
            "Environment Name", [env["name"] for env in environments]
        )

        flavor_name = st.selectbox(
            "Flavor Name",
            unique_flavor_names,
            help="""Select the flavor name for the VM. To find out which flavour you need for which LLM, 
              check out our [LLM GPU selector](https://gpu-selector-llm.hyperstack.cloud/?embed=true). Please note: not all flavours are available in all regions, see the [Hyperstack documentation](https://infrahub-doc.nexgencloud.com/docs/hardware/flavors) for more information.
              """,
        )
        image_name = st.selectbox(
            "Image Name",
            ubuntu_images,
            help="Select the image name for the replica. Currently, only Ubuntu images are supported.",
        )
        port = st.number_input(
            "Port",
            key=f'new_replica_port{st.session_state["new_replica_model_name"]}',
            value=8000,
            min_value=0,
            max_value=65535,
            help="Port number to use for the endpoint replica. By default, vLLM uses port 8000.",
        )
        st.pills(
            "Inference Engine",
            ["vLLM"],
            default="vLLM",
            help="Select the inference engine for the replica. Currently, only vLLM is supported.",
        )

        run_command = st.text_area(
            "Docker Run Command",
            placeholder="Enter Docker Run Command. This field can not be empty. Check the help (?) icon for more information.",
            key=f'new_replica_run_command{st.session_state["new_replica_model_name"]}',
            help=DOCKER_RUN_HELP,
        )
        run_command_warning = st.empty()
        key_name = st.selectbox(
            "Keypair Name", [keypair["name"] for keypair in keypairs]
        )
        cols = st.columns((1, 1))

        if run_command:
            if st.session_state["new_replica_model_name"] not in run_command:
                run_command_warning.error(
                    f"The model name for this replica is not present in the Docker run command. This will likely lead to issues. Expected model name: `{st.session_state['new_replica_model_name']}` in the run command. Check the help (?) icon for more information."
                )
        if cols[0].button("Create", type="primary", use_container_width=True):
            create_replica(
                st.session_state["new_replica_model_id"],
                new_endpoint,
                should_create_vm=True,
                name=vm_name,
                environment_name=environment_name,
                image_name=image_name,
                flavor_name=flavor_name,
                port=port,
                run_command=run_command,
                key_name=key_name,
            )
        if cols[1].button(
            "Cancel",
            use_container_width=True,
            key=f'cancel_button_{st.session_state["new_replica_model_name"]}',
        ):
            st.rerun()

    if not create_vm_checkbox:
        cols2 = st.columns((1, 1))
        if cols2[0].button("Create", type="primary", use_container_width=True):
            create_replica(
                st.session_state["new_replica_model_id"],
                new_endpoint,
                should_create_vm=False,
            )
        if cols2[1].button(
            "Cancel",
            use_container_width=True,
            key=f'cancel_button_{st.session_state["new_replica_model_name"]}',
        ):
            st.rerun()


def main():
    """
    The main function to initialize and run the Streamlit app.
    """
    initialize_page(title="Models - Hyperstack LLM Inference Toolkit")

    sidebar_page_link(PAGE_HELP)

    if "new_model_name" not in st.session_state:
        st.session_state["new_model_name"] = ""

    def submit():
        st.session_state["new_model_name"] = st.session_state["widget"]
        st.session_state["widget"] = ""

    with st.expander("New Model"):
        st.subheader("Add New Model")
        add_cols = st.columns((6, 1))
        add_cols[0].text_input(
            "Model Name",
            key="widget",
            placeholder="Enter Model Name",
            label_visibility="collapsed",
            help="Make sure your model name matches the model name used by inference engine.",
            on_change=submit,
        )
        if add_cols[1].button("Add Model", type="primary", use_container_width=True):
            if st.session_state["new_model_name"]:
                add_model(st.session_state["new_model_name"])
            else:
                st.error("Please enter a model name.")

    models = get_all_models()
    for i, item in enumerate(models):
        model_card(item, i)

    st.warning(
        "⚠️ Deleting a model or replica will only delete it from the database. Any cloud resources may still exist and incur billing costs."
    )


if __name__ == "__main__":
    main()
