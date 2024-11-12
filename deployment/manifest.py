import functools
import os
import yaml

from exceptions import CallError


@functools.cache
def load_manifest() -> dict:
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conf/build.manifest.yaml')) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError:
        raise CallError('Please specify a valid yaml file for build manifest')
