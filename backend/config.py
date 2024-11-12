import os
import logging

from tests.unit_tests.utils import make_test_llm_config
from utils.rest import get_public_ip

logger = logging.getLogger(__name__)


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM
    MOCK_LLM = False
    LLM_MOCK_DATA_STREAM_PATH = os.getenv('LLM_MOCK_DATA_STREAM_PATH', '/app/data/streamed.txt')

    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', default='redis')
    REDIS_PORT = os.getenv('REDIS_PORT', default=6379)
    REDIS_DB = os.getenv('REDIS_DB', default=0)

    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', default='redis://redis:6379')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', default='redis://redis:6379')

    # DB
    MYSQL_DB_HOST = os.getenv('MYSQL_DB_HOST', default='db')
    MYSQL_USER = os.getenv('MYSQL_USER')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')
    MYSQL_ROOT_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD')

    # s3
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

    # backup db schedule
    DB_BACKUP_SCHEDULE_MIN = os.getenv('DB_BACKUP_SCHEDULE_MIN', default='0')
    DB_BACKUP_SCHEDULE_HOUR = os.getenv('DB_BACKUP_SCHEDULE_HOUR', default='*/6')
    DB_BACKUP_SCHEDULE_DAY_OF_WEEK = os.getenv('DB_BACKUP_SCHEDULE_DAY_OF_WEEK', default='*')
    DB_BACKUP_SCHEDULE_DAY_OF_MONTH = os.getenv('DB_BACKUP_SCHEDULE_DAY_OF_MONTH', default='*')
    DB_BACKUP_SCHEDULE_MONTH_OF_YEAR = os.getenv('DB_BACKUP_SCHEDULE_MONTH_OF_YEAR', default='*')

    HYPERSTACK_API_KEY = os.getenv('HYPERSTACK_API_KEY')
    PUBLIC_IP = get_public_ip()


class LocalConfig(Config):
    pass


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://devuser:devpass@db:3306/inference_test_db'
    LLM_ENDPOINTS_CONFIG = make_test_llm_config()
    CELERY_TASK_ALWAYS_EAGER = True
    MOCK_LLM = True
    REDIS_DB = 1


class IntegrationTestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://devuser:devpass@db:5432/inference_test_db'
    LLM_ENDPOINTS_CONFIG = make_test_llm_config()
    MOCK_LLM = False
    REDIS_DB = 1


class ProductionConfig(Config):
    pass
