import os
import requests

from hyperstack.vm import VMService
from hyperstack.cloud_config import ProxyAPIConfigGenerator
from manifest import load_manifest


def create_flask_vm():

    data = load_manifest()

    git_data = data["git"]
    env_data = data["env"]
    instance_data = data["proxy_instance"]
    instance_data["assign_floating_ip"] = True
    conf = ProxyAPIConfigGenerator(git_data, env_data)
    user_data = conf.construct()
    instance_data["user_data"] = user_data

    response = VMService.create(instance_data | {"wait_for_vm_to_be_active": True})
    if response.error:
        raise ValueError(response.response.json())
    return response.response


def create_replicas(instance_data, app_url, model_id):
    instance_data.pop("model_name", None)
    payload = {
        "endpoint": "",
        "rate_limit": 20,
        "create_vm": True,
        "vm_creation_details": instance_data,
    }
    try:
        response = requests.post(
            f"{app_url}/models/{model_id}/replicas",
            json=payload,
            headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
        )
    except Exception:
        raise ValueError("Unable to create replica.")

    if response.status_code == 201:
        return response.json()
    else:
        raise ValueError(response.json())


def create_model(app_url, model_name):
    response = requests.get(
        f"{app_url}/models",
        headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
    )
    if response.status_code != 200:
        raise ValueError(f"Getting models failed: {response.json()}")

    existing_models = {model["name"]: model["id"] for model in response.json()}

    try:
        if model_name not in existing_models:
            response = requests.post(
                f"{app_url}/models",
                json={"name": model_name},
                headers={"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"},
            )
        else:
            return {"id": existing_models[model_name]}
    except Exception:
        raise ValueError("Unable to create model.")

    if response.status_code == 201:
        return response.json()
    else:
        raise ValueError(response.json())
