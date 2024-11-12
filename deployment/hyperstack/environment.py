import typing

from .connection import call, Response
from .utils import HYPERSTACK_BASE_API_URL


class EnvironmentService:
    """
    Service class for managing environment operations.
    """
    URL = f'{HYPERSTACK_BASE_API_URL}/environments'

    @staticmethod
    def list() -> Response:
        """
        List all environments.

        Returns:
            Response: The response object containing either an error or the list of environments.
        """
        return call(method='GET', url=EnvironmentService.URL, handle_special_status=True, nested_obj_key='environments')

    @staticmethod
    def exists(name: str, environments: typing.List | None = None) -> bool:
        """
        Check if an environment exists.

        Args:
            name (str): The name of the environment.
            environments (list, optional): The list of environments. Defaults to None.

        Returns:
            bool: True if the environment exists, False otherwise.
        """
        envs = environments if environments else EnvironmentService.list()
        return name in [env['name'] for env in ([] if envs.error else envs.response)]
