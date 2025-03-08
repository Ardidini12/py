import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pywhatsapp.settings')
app = Celery('pywhatsapp')
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.beat_schedule = {
    'send-birthday-messages': {
        'task': 'contacts.tasks.send_birthday_messages',
        'schedule': crontab(minute=0, hour=0),  # Daily at midnight
    },
}