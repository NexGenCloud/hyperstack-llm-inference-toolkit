from .connection import call, Response
from .utils import HYPERSTACK_BASE_API_URL


class FlavorService:
    """
    Service class for managing flavor operations.
    """
    URL = f'{HYPERSTACK_BASE_API_URL}/flavors'

    @staticmethod
    def list() -> Response:
        """
        List all flavors.

        Returns:
            Response: The response object containing either an error or the list of flavors.
        """
        return call(method='GET', url=FlavorService.URL, handle_special_status=True, nested_obj_key='data')
