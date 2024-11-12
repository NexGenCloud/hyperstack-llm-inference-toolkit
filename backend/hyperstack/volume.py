import typing

from pydantic import BaseModel, Field, field_validator, ValidationError

from .connection import call, Response
from .utils import HYPERSTACK_BASE_API_URL


class VolumeCreateSchema(BaseModel):
    """
    Schema for creating a volume.

    Attributes:
        name (str): The name of the volume.
        size (int): The size of the volume in GB.
        volume_type (str): The type of the volume.
        environment_name (str): The environment of the volume.
        description (str): The description of the volume.
    """

    name: str
    size: int
    volume_type: typing.Literal['Cloud-SSD'] = Field(default='Cloud-SSD')
    environment_name: str
    description: str

    @field_validator('size')
    def size_must_be_positive(cls, value):
        """
        Validator to ensure size is a positive integer.
        """
        if not (0 < value < 1048576):
            raise ValueError('Size must be between 0 and 1048576')
        return value


class VolumeService:
    """
    Service class for managing volume operations.
    """

    URL = f'{HYPERSTACK_BASE_API_URL}/volumes'

    @staticmethod
    def create(data: dict) -> Response:
        """
        Create a new volume.

        Args:
            data (dict): The data for creating the volume. Must include 'name', 'size', and 'type'.

        Returns:
            Response: The response object containing either an error or the response data.
        """
        try:
            validated_data = VolumeCreateSchema(**data)
        except ValidationError as e:
            return Response(error=str(e), response=None)

        return call(
            method='POST', url=VolumeService.URL, payload=validated_data.dict(), handle_special_status=True,
            nested_obj_key='volume',
        )

    @staticmethod
    def list() -> Response:
        """
        Retrieve all volumes.

        Returns:
            Response: The response object containing either an error or the list of volumes
        """
        return call(method='GET', url=VolumeService.URL, handle_special_status=True, nested_obj_key='volumes')

    @staticmethod
    def delete(volume_id: int) -> Response:
        """
        Delete a volume by its ID.

        Args:
            volume_id (int): The ID of the volume to delete.

        Returns:
            Response: The response object containing either an error or a confirmation of deletion.
        """
        url = f'{VolumeService.URL}/{volume_id}'
        return call(method='DELETE', url=url)
