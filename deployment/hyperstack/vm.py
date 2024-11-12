import time
import typing

from pydantic import BaseModel, Field, field_validator, ValidationError

from .connection import call, Response
from .exceptions import CallError
from .utils import HYPERSTACK_BASE_API_URL


class SecurityRuleSchema(BaseModel):
    """
    Schema for defining a security rule.

    Attributes:
        direction (str): The direction of traffic ('ingress' or 'egress'). Required.
        protocol (str): The network protocol (e.g., 'tcp', 'udp'). Required.
        ethertype (str): The Ethernet type ('IPv4' or 'IPv6'). Required.
        remote_ip_prefix (str): The IP address range. Required.
        port_range_min (int): The minimum port number. Required.
        port_range_max (int): The maximum port number. Required.
    """

    direction: typing.Literal['ingress', 'egress']
    protocol: typing.Literal['tcp', 'udp']
    ethertype: typing.Literal['IPv4', 'IPv6']
    remote_ip_prefix: str
    port_range_min: int
    port_range_max: int


class VMCreateSchema(BaseModel):
    """
    Schema for creating a virtual machine.

    Attributes:
        name (str): The name of the virtual machine. Required.
        environment_name (str): The name of the environment for the VM. Required.
        image_name (str): The name of the operating system image.
        Required unless creating from an existing bootable volume.
        flavor_name (str): The name of the flavor specifying hardware configuration. Required.
        key_name (str): The SSH keypair name for access. Required.
        count (int): Number of VMs to deploy. Required.
        assign_floating_ip (Optional[bool]): Whether to assign a public IP. Optional.
        security_rules (List[SecurityRuleSchema]): Firewall rules configuration. Required.
        user_data (Optional[str]): Initialization scripts in cloud-init format. Required.
    """

    name: str
    environment_name: str
    image_name: str = Field(default='Ubuntu Server 22.04 LTS R535 CUDA 12.2')
    flavor_name: str
    key_name: str
    count: typing.Literal[1] = Field(default=1)
    assign_floating_ip: bool = Field(default=False)
    security_rules: typing.List[SecurityRuleSchema]
    user_data: str

    @field_validator('count')
    def count_must_be_positive(cls, value):
        """
        Validator to ensure count is a positive integer.
        """
        if value <= 0:
            raise ValueError('count must be a positive integer')
        return value


class VMVolumeAttachSchema(BaseModel):
    """
    Schema for attaching a volume to a virtual machine.

    Attributes:
        volume_ids (List[int]): The IDs of the volumes to attach.
    """

    volume_ids: typing.List[int]

    @field_validator('volume_ids')
    def volume_ids_must_not_be_empty(cls, value):
        """
        Validator to ensure volume_ids is not empty.
        """
        if not value:
            raise ValueError('volume_ids must not be empty')
        return value


class VMServiceStatus:
    CREATING = 'CREATING'
    BUILD = 'BUILD'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'
    STARTING = 'STARTING'
    HIBERNATING = 'HIBERNATING'
    HIBERNATED = 'HIBERNATED'
    RESTORING = 'RESTORING'

    CHOICES = [CREATING, BUILD, ACTIVE, ERROR, STARTING, HIBERNATING, HIBERNATED, RESTORING]


class VMService:
    """
    Service class for managing virtual machine operations.
    """

    URL = f'{HYPERSTACK_BASE_API_URL}/virtual-machines'

    @staticmethod
    def create(data: dict) -> Response:
        """
        Create a new virtual machine.

        Args:
            data (dict): The data for creating the VM. Must include required fields.

        Returns:
            Response: The response object containing either an error or the response data.
        """
        wait_for_vm_to_be_active = data.pop('wait_for_vm_to_be_active', False)
        try:
            validated_data = VMCreateSchema(**data)
        except ValidationError as e:
            return Response(error=str(e), response=None)

        vm_resp = call(method='POST', url=VMService.URL, payload=validated_data.dict())

        if not vm_resp.error:
            if vm_resp.response['status'] is False:
                vm_resp.error = f'Failed to create {data["name"]!r} VM: {vm_resp.response["message"]}'
            else:
                vm_resp.response = vm_resp.response['instances'][0]
                if wait_for_vm_to_be_active:
                    vm_resp = VMService.wait_to_be_active(vm_id=vm_resp.response['id'])

        return vm_resp

    @staticmethod
    def list() -> Response:
        """
        List all virtual machines.

        Returns:
            Response: The response object containing either an error or the list of VMs.
        """
        return call(method='GET', url=VMService.URL, handle_special_status=True, nested_obj_key='instances')

    @staticmethod
    def get(vm_id: int) -> Response:
        """
        Retrieve a vm by its ID.

        Args:
            vm_id (int): The ID of the vm to retrieve.

        Returns:
            Response: The response object containing either an error or the vm data.
        """
        url = f'{VMService.URL}/{vm_id}'
        return call(method='GET', url=url, handle_special_status=True, nested_obj_key='instance')

    @staticmethod
    def wait_to_be_active(vm_id: int, retries: int = 5, delay_in_between: int = 5) -> Response:
        """
        Wait for a VM to be in the 'ACTIVE' state.

        Args:
            vm_id (int): The ID of the VM to wait for.
            retries (int): The number of retries to wait for the VM to be active.
            delay_in_between (int): The delay in seconds between retries.

        Returns:
            Response: The response object containing either an error or the vm data.
        """
        while True:
            if (vm_resp := VMService.get(vm_id)).error:
                retries -= 1
                if retries <= 0:
                    raise CallError(f'Failed to retrieve {vm_id!r} VM status: {vm_resp.error}')
            else:
                if vm_resp.response['status'] == 'ACTIVE' and vm_resp.response['floating_ip']:
                    break

            time.sleep(delay_in_between)

        return vm_resp

    @staticmethod
    def attach_volume(vm_id: int, data: dict) -> Response:
        """
        Attach a volume to a VM.

        Args:
            vm_id (int): The ID of the VM to attach the volume to.
            data (dict): Dictionary containing volume_ids to be attached to `vm_id` VM.

        Returns:
            Response: The response object containing either an error or the vm data.
        """
        try:
            validated_data = VMVolumeAttachSchema(**data)
        except ValidationError as e:
            return Response(error=str(e), response=None)

        url = f'{VMService.URL}/{vm_id}/attach-volumes'
        return call(method='POST', url=url, payload=validated_data.dict())

    @staticmethod
    def delete(vm_id: int) -> Response:
        """
        Delete a virtual machine by its ID.

        Args:
            vm_id (int): The ID of the virtual machine to delete.

        Returns:
            Response: The response object containing either an error or a confirmation of deletion.
        """
        url = f'{VMService.URL}/{vm_id}'
        return call(method='DELETE', url=url)
