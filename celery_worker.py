from celery import Celery
import os

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=os.environ.get('CELERY_BACKEND_URL', 'redis://localhost:6379/0'),
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    )
    celery.conf.update(app.config)
    return celery
