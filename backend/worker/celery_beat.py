from celery import Celery
from celery.schedules import crontab

from config import Config


celery_beat = Celery('periodic', broker=Config.CELERY_BROKER_URL)
celery_beat.conf.timezone = 'UTC'

celery_beat.conf.beat_schedule = {
    'backup_db': {
        'task': 'backup_db',
        'schedule': crontab(
            minute=Config.DB_BACKUP_SCHEDULE_MIN,
            hour=Config.DB_BACKUP_SCHEDULE_HOUR,
            day_of_week=Config.DB_BACKUP_SCHEDULE_DAY_OF_WEEK,
            day_of_month=Config.DB_BACKUP_SCHEDULE_DAY_OF_MONTH,
            month_of_year=Config.DB_BACKUP_SCHEDULE_MONTH_OF_YEAR
        )
    }
}
