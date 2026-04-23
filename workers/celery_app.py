from celery import Celery

from api.core.config import get_settings

s = get_settings()
app = Celery(
    "nexus",
    broker=s.celery_broker_url,
    backend=s.celery_result_backend,
)
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

from workers.beat_schedule import CELERY_BEAT_SCHEDULE

app.conf.beat_schedule = CELERY_BEAT_SCHEDULE

import workers.tasks  # noqa: E402,F401
