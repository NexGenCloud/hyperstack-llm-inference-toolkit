import argparse
import os
import subprocess

import boto3
from botocore.exceptions import NoCredentialsError


# DB
DB_HOST = os.getenv('MYSQL_DB_HOST')
DB_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')
DB_NAME = os.getenv('MYSQL_DATABASE')

# s3
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')


def is_db_running() -> bool:
    try:
        subprocess.run(
            ['mysqladmin', '-h', DB_HOST, '-u', 'root', '-p' + DB_ROOT_PASSWORD, 'ping'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        print('MySQL is running and ready.')
        return True
    except subprocess.CalledProcessError as exception:
        print(exception)
        return False


def download_from_s3(dump_file_name: str, local_path: str):
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
    )
    try:
        s3_client.download_file(S3_BUCKET_NAME, f'backups/{dump_file_name}', local_path)
        print(f'Downloaded {dump_file_name} from S3.')
    except NoCredentialsError:
        raise ValueError('Invalid / Empty s3 credentials.')
    except Exception as exception:
        print('Unable to download dump file from s3')
        raise ValueError(exception)


def apply_dump_to_db(dump_file_path: str):
    try:
        command = f'mysql -h {DB_HOST} -u root -p{DB_ROOT_PASSWORD} {DB_NAME} < {dump_file_path}'
        subprocess.run(command, shell=True, check=True)
        print(f'Applied dump {os.path.basename(dump_file_path)} to database {DB_NAME}')
    except Exception as exception:
        print('Unable to apply dump file.')
        raise ValueError(exception)


def main():
    parser = argparse.ArgumentParser(description='Download a dump file from S3 and apply it to the MySQL database.')
    parser.add_argument('--file', type=str, required=True, help='The name of the dump file to download from S3')
    args = parser.parse_args()

    local_dump_path = f'/tmp/{args.file}'

    # Check if DB is running or not
    if is_db_running():

        # Download the dump file from S3
        download_from_s3(args.file, local_dump_path)

        # Apply the dump to the database
        apply_dump_to_db(local_dump_path)

        # Clean up local dump file
        os.remove(local_dump_path)
        print(f'Removed local dump file {os.path.basename(local_dump_path)}')

    else:
        print('MySQL should be running in order to apply a backup.')


if __name__ == '__main__':
    main()
