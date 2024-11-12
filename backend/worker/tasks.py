import contextlib
import os
import subprocess

import boto3
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import NoCredentialsError, ClientError, EndpointConnectionError
from datetime import datetime
from loguru import logger as lg

from config import Config
from hyperstack.connection import set_api_key
from hyperstack.vm import VMService, VMServiceStatus
from tables.llm_model import LLMModel  # noqa
from tables.replicas import Replica, ReplicaVMStatus
from worker.celery_task import celery
from worker.db_session import db_session
from worker.utils import is_model_deployed, create_replica_vm


set_api_key(Config.HYPERSTACK_API_KEY)

# DB credentials
DB_NAME = Config.MYSQL_DATABASE
DB_ROOT_PASSWORD = Config.MYSQL_ROOT_PASSWORD
DB_HOST = Config.MYSQL_DB_HOST

# S3 credentials
S3_BUCKET_NAME = Config.S3_BUCKET_NAME
S3_ENDPOINT_URL = Config.S3_ENDPOINT_URL
S3_ACCESS_KEY = Config.S3_ACCESS_KEY
S3_SECRET_KEY = Config.S3_SECRET_KEY


@celery.task(name="monitor_vm_status")
def monitor_vm_status(vm_id: int, data: dict, replica_id: int):
    # We will wait for hyperstack to deploy the VM first and then we will see if it has been bootstrapped
    # using our cloud config, if not in the timeout we have we will mark the replica as failed
    endpoint_url = response = vm_error_msg = None
    vm_status = ReplicaVMStatus.FAILED
    try:
        # We will wait for 60 seconds and then see if VM has been deployed yet by hyperstack
        # We will then do this activity a total of 60 times until it is deployed, let's change as required
        response = VMService.wait_to_be_active(vm_id, 60, 60)
        if response.error:
            raise Exception(response.error)
    except Exception:
        vm_error_msg = "Failed while waiting for VM to be active"
        if response and response.error:
            vm_error_msg += f" ({response.error})"
    else:
        endpoint_url = f'http://{response.response["floating_ip"]}:{data["port"]}/v1/chat/completions'

    if endpoint_url:
        if is_model_deployed(endpoint_url):
            vm_status = ReplicaVMStatus.SUCCESS
        else:
            vm_status = ReplicaVMStatus.FAILED
            vm_error_msg = "Unable to bootstrap inference engine"

    with db_session() as session:
        (
            session.query(Replica)
            .filter_by(id=replica_id)
            .update(
                {
                    "vm_status": vm_status,
                    "endpoint": endpoint_url,
                    "vm_id": vm_id,
                    "error_message": vm_error_msg,
                }
            )
        )


@celery.task(name="create_vm_on_hyperstack")
def create_vm_on_hyperstack(replica_id: int, data: dict):
    response = vm_error_msg = vm_id = None
    vm_status = VMServiceStatus.ERROR
    try:
        response = create_replica_vm(data)
        if response.error:
            raise Exception(response.error)
    except Exception as e:
        lg.debug(f"Unable to deploy VM: {e}")
        if response and response.error:
            vm_error_msg = (
                str(response.response.json())
                if response.response is not None
                else response.error
            )
        else:
            vm_error_msg = "No error message retrieved from hyperstack"
        lg.error(f"Error deploying VM: {vm_error_msg}")
        raise RuntimeError(f"Error deploying VM: {vm_error_msg}")
    else:
        vm_status = response.response["status"]
        vm_id = response.response["id"]

    if vm_status != VMServiceStatus.ERROR:
        monitor_vm_status.delay(vm_id, data, replica_id)
    else:
        with db_session() as session:
            (
                session.query(Replica)
                .filter_by(id=replica_id)
                .update(
                    {
                        "vm_status": ReplicaVMStatus.FAILED,
                        "error_message": vm_error_msg,
                    }
                )
            )


@celery.task(name="backup_db")
def backup_db():
    # Backup file name
    backup_file = f'/tmp/{DB_NAME}_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.sql'

    try:
        # Dump MySQL database
        dump_command = f"mysqldump -h {DB_HOST} -u root -p{DB_ROOT_PASSWORD} {DB_NAME} > {backup_file}"
        subprocess.run(dump_command, shell=True, check=True)

        # Create s3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
        )
        try:
            # Upload to S3
            s3_client.upload_file(
                backup_file, S3_BUCKET_NAME, f"backups/{os.path.basename(backup_file)}"
            )
        except NoCredentialsError:
            lg.exception("S3 credentials not provided or invalid.")
        except EndpointConnectionError:
            lg.exception("Failed to connect to the specified S3 endpoint.")
        except (ClientError, S3UploadFailedError) as e:
            lg.exception(f"Failed to upload to S3: {e}")
    except subprocess.CalledProcessError as e:
        lg.exception(f"Failed to dump MySQL database: {e}")
    except Exception as e:
        lg.exception(f"An unexpected error occurred: {e}")
    finally:
        # Clean up local files
        with contextlib.suppress(OSError, FileNotFoundError):
            os.remove(backup_file)
