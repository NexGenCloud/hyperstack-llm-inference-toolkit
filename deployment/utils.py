import time

from hyperstack.connection import call


def wait_for_proxy_app_to_be_deployed(flask_app_url: str):
    retries = 30
    while True:
        response = call('GET', f'{flask_app_url}/models')
        if not response.error:
            break

        retries -= 1
        if retries <= 0:
            return ValueError('Timed out waiting for proxy VM to be active')

        time.sleep(10)
