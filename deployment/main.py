import argparse

from hyperstack.connection import set_api_key
from manifest import load_manifest
from provision import create_flask_vm, create_replicas, create_model
from utils import wait_for_proxy_app_to_be_deployed
from validate import validate_config


def main():
    argparse.ArgumentParser(description='Provision VMs using the provision_vms function.')

    manifest_data = load_manifest()
    set_api_key(manifest_data['hyperstack_api_key'])
    validate_config()

    # creating proxy vm
    print('Creating Flask VM')
    response = create_flask_vm()
    flask_app_url = f'http://{response["floating_ip"]}:5001/api/v1'

    print('Flask VM has been created, bootstrapping VM and deploying proxy-app')
    wait_for_proxy_app_to_be_deployed(flask_app_url)

    # creating inference vms
    print('Instructing proxy-app to deploy inference VMs')

    model_response = create_model(flask_app_url, manifest_data['inference_engine_vms'][0]['model_name'])
    create_replicas(manifest_data['inference_engine_vms'][0], flask_app_url, model_response['id'])

    model_response = create_model(flask_app_url, manifest_data['inference_engine_vms'][1]['model_name'])
    create_replicas(manifest_data['inference_engine_vms'][1], flask_app_url, model_response['id'])


if __name__ == '__main__':
    main()
