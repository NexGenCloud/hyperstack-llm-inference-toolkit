from jsonschema import validate, ValidationError

from exceptions import CallError, ValidationErrors
from hyperstack.environment import EnvironmentService
from manifest import load_manifest
from schema import CONF_SCHEMA


def get_cached_hyperstack_state() -> dict:
    return {
        'environments': EnvironmentService.list(),
    }


def validate_vm_config(vm_config, schema, cached_state: dict) -> ValidationErrors:
    verrors = ValidationErrors()
    if not EnvironmentService.exists(vm_config['environment_name'], cached_state['environments']):
        verrors.add(f'{schema}.environment_name', 'Environment does not exist')

    # TODO: Add checks here for other stuff as well like key name etc
    return verrors


def validate_config():
    manifest = load_manifest()
    try:
        validate(manifest, CONF_SCHEMA)
    except ValidationError as e:
        raise CallError(f'Invalid configuration specified: {e}')

    cached_state = get_cached_hyperstack_state()

    verrors = ValidationErrors()
    verrors.extend(validate_vm_config(manifest['proxy_instance'], 'proxy_instance', cached_state))
    # verrors.extend(validate_vm_config(manifest['inference_engine_vms'], 'inference_engine_vms', cached_state))
    verrors.check()
