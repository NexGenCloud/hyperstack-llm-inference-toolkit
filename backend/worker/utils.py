import time

from hyperstack.cloud_config import InferenceEngineConfigGenerator
from hyperstack.connection import call, Response
from hyperstack.vm import VMService


def is_model_deployed(endpoint_url: str) -> bool:
    retries = 30
    while True:
        response = call('GET', endpoint_url)
        if response.error and response.response is not None:
            if response.response.status_code == 405:
                break

        retries -= 1
        if retries <= 0:
            return False

        time.sleep(30)

    return True


def create_replica_vm(data: dict) -> Response:
    run_command = data['run_command']
    conf = InferenceEngineConfigGenerator(run_command)
    data['user_data'] = conf.construct()

    return VMService.create(data)
